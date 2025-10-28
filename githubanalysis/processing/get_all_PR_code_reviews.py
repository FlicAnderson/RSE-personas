"""Get code review data if present for repos; save out to files."""

import logging
import json
import pandas as pd
from typing import Any
import argparse
from pathlib import Path

# from run_commits_workflow import read_repos_from_file
from githubanalysis.processing.get_all_pages_issues import is_this_single_page
from githubanalysis.setup_classes import RESTRequestSetup
from utilities.check_gh_reponse import (
    raise_if_response_error,
    run_with_retries,
    RepoNotFoundError,
)


def simple_read_repos_from_file(filename) -> list[str]:
    with open(filename, "r") as f:
        repos = [txtline.strip() for txtline in f.readlines()]
        return repos


class GetCodeReviews(RESTRequestSetup):
    def _log_name(self) -> str:
        return "get_all_PR_code_reviews"

    def __init__(
        self, config_path: str, in_notebook: bool, logger: None | logging.Logger = None
    ) -> None:
        super().__init__(config_path, in_notebook, logger)

    def make_pulls_query_url(
        self,
        repos_api_url: str,
        repo_name: str,
        per_pg: int | str,
        page: int | None,
    ):
        if page is None:
            return f"{repos_api_url}{repo_name}/pulls?state=all&per_page={per_pg}"
        else:
            return f"{repos_api_url}{repo_name}/pulls?state=all&per_page={per_pg}&page={page}"

    def make_reviews_query_url(
        self,
        repos_api_url: str,
        repo_name: str,
        PR_num: int,
        per_pg: int | str,
        page: int | None,
    ):
        if page is None:
            return (
                f"{repos_api_url}{repo_name}/pulls/{PR_num}/reviews?per_page={per_pg}"
            )
        else:
            return f"{repos_api_url}{repo_name}/pulls/{PR_num}/reviews?per_page={per_pg}&page={page}"

    def review_comments_query_url(
        self,
        PR_number: int,
        PR_review_number: int,  # this is ~= to PR review_ID
        repos_api_url: str,
        repo_name: str,
        per_pg: int | str,
        page: int | None,
    ):
        if page is None:
            return f"{repos_api_url}{repo_name}/pulls/{PR_number}/reviews/{PR_review_number}/comments?per_page={per_pg}"
        else:
            return f"{repos_api_url}{repo_name}/pulls/{PR_number}/reviews/{PR_review_number}/comments?per_page={per_pg}&page={page}"

    def get_repos(
        self,
        repo_list_file_name: Path,
    ) -> list[str]:
        repo_list = simple_read_repos_from_file(
            filename=self.data_location / repo_list_file_name
        )
        return repo_list

    def loop_over_repos(
        self,
        repo_list: list[str],
    ):
        # for each repo_name in repo_list:
        # do:
        # ...
        i = 0
        all_repos_reviews_results = []

        for repo in repo_list:
            i += 1
            print(f"processing repo {i} of {len(repo_list)}")
            print(f"processing repo: {repo}.")
            pulls_qry = self.make_pulls_query_url(
                repos_api_url="https://api.github.com/repos/",
                repo_name=repo,
                per_pg=100,
                page=1,
            )
            print(f"pulls query is: {pulls_qry}")

            # for repo, run get_PR_numbers(repo_name = repo)
            # checks for API response
            # if I get RepoNotFoundError, SKIP TO NEXT REPO. (done by RepoNotFound Error in check_PRs_exist() )
            # get PRs_list of ints from json response
            # store in useful format for using to query separately using loop_over_repo_PRs(PRs_list)

            repo_PRs = self.get_PR_numbers(repo_name=repo)

            if repo_PRs is not None:
                print(f"repo {repo} contains PRs: {repo_PRs}")
            else:
                print(f"No PRs for repo {repo}; skipping to next repo.")
                continue

            assert repo_PRs is not None

            repo_reviews = self.loop_over_repo_PRs(repo_name=repo, repo_PRs=repo_PRs)

            repo_results = {
                "repo_name": repo,
                "number_PRs": len(repo_PRs),
                "total_PR_reviews": sum(
                    sum(reviews) for reviews in repo_reviews.values()
                ),
            }

            all_repos_reviews_results.append(repo_results)

        write_out_location = Path(
            self.data_location,
            f"repos_PR_reviews_results_{self.current_date_info}.csv",
        )
        all_repos_reviews_results_df = pd.DataFrame(all_repos_reviews_results)

        self.logger.info(
            f"saving results of repo PR reviews gathering out to file {write_out_location}"
        )
        all_repos_reviews_results_df.to_csv(
            path_or_buf=write_out_location, header=True, index=False
        )
        # reviews_results.append(
        #    repo_reviews
        # )  # will overwrite existing repo_names, so needs to contain the sum PR_reviews info

        # (in loop_over_repo_PRs(PRs_list):)
        # for PR in PRs_list, run get_review_comments_for_PR(PR_number=PR)
        # get review comments, get GH_username and other similar info required, timestamps etc.
        # save out raw data to json file
        # combine into per-repo_name df or other structure, labelled appropriately

        # (collate and log per-repo stats: e.g. N of PRs, N of PRs with reviews, N of reviews per PR, N of GH_usernames etc )

        # shift to next repo in repo_list.
        return all_repos_reviews_results

    def check_PRs_exist(
        self, repo_name: str, pulls_qry: str
    ):  # returns None or requests.models.Response api_response
        # for given pull requests query, check that there are PRs to check for reviews in.
        # if none exist, skip to next repo.
        self.logger.info(f"getting json via request url {pulls_qry}.")
        try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=pulls_qry, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            print(api_response)
        except RepoNotFoundError:
            print(f"Repo {repo_name} not found; skipping this repo.")
            return None  # this is intentionally skipping repos which don't exist.
            # if I get RepoNotFoundError, I want to SKIP TO NEXT REPO.
        else:
            return api_response

    def count_PR_reviews(
        self,
        repo_name: str,
        PR_num: int,
        reviews_qry: str | None,
    ) -> tuple[list[int], list[dict[str, Any]]]:
        # for given PR number in given repo, check for PR Reviews
        # if a query is supplied (e.g. from api_response.links), use that, otherwise construct the 'first page' query

        PR_review_nums: list[int] = []
        PR_reviews_json = []
        if reviews_qry is None:
            reviews_qry = self.make_reviews_query_url(
                repos_api_url="https://api.github.com/repos/",
                repo_name=repo_name,
                PR_num=PR_num,
                per_pg=100,
                page=1,
            )
        else:
            reviews_qry = reviews_qry

        print(f"pull request reviews query for PR {PR_num} is: {reviews_qry}")
        self.logger.info(f"getting json via request url {reviews_qry}.")
        try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=reviews_qry, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            print(api_response)
        except Exception as e:
            self.logger.error(
                f"Error in getting PR reviews for PR {PR_num} for repo name {repo_name} with query {reviews_qry}: {e}."
            )
            raise

        json_pg = api_response.json()

        PR_reviews_json.extend(json_pg)

        count_PR_reviews = len(json_pg)

        if is_this_single_page(api_response.links):
            self.logger.debug("single page of reviews only; <=100")
            self.logger.debug(f"Contains {count_PR_reviews} PR reviews")
            PR_review_nums.append(count_PR_reviews)

        elif not is_this_single_page(
            api_response.links
        ):  # use bool result from get_all_pages_issues.py function
            #     #print(len(repo_PRs))
            self.logger.debug("more than one pages of reviews; >100")
            #         PR_review_nums.append(count_PR_reviews)
            #         print(sum(PR_review_nums))

            next_pg = api_response.links["next"][
                "url"
            ]  # use pagination to get 'next page' url for query
            try:
                api_response = run_with_retries(
                    fn=lambda: raise_if_response_error(
                        api_response=self.s.get(url=next_pg, headers=self.headers),
                        repo_name=repo_name,
                        logger=self.logger,
                    ),
                    logger=self.logger,
                )
                print(api_response)
            except Exception as e:
                self.logger.error(
                    f"Error in getting PR reviews for PR {PR_num} for repo name {repo_name} with query {next_pg}: {e}."
                )
                raise

            json_pg = api_response.json()
            PR_reviews_json.extend(json_pg)
            count_PR_reviews += len(json_pg)  # add N of next_pg of reviews to previous
            self.logger.debug(f"Contains {count_PR_reviews} PR reviews")
            PR_review_nums.append(
                count_PR_reviews
            )  # collate N of reviews to var out of the loop

        self.logger.info(PR_review_nums)
        self.logger.info(
            f"{sum(PR_review_nums)} found across {len(PR_review_nums)} PRs"
        )

        return PR_review_nums, PR_reviews_json

    def get_PR_numbers(
        self, repo_name: str, out_json_file="all-PR-numbers_json"
    ) -> list[int] | None:
        """
        should get pull request numbers to loop through to check for code reviews.
        Writes out JSON file of PR entries (no reviews)

        """
        # create API request to use repo_name, and get PR numbers
        # PRs_api_url = f"https://api.github.com/repos/{repo_name}/pulls"
        # make query from PRs_api_url and other headers/info (SEPARATED INTO)
        # and return PRs_list list of ints to query separately.
        # PRs_list = # parsed list of ints from json response
        # return PRs_list

        # assemble query url
        pulls_qry = self.make_pulls_query_url(
            repos_api_url="https://api.github.com/repos/",
            repo_name=repo_name,
            per_pg=100,
            page=1,
        )
        api_response = self.check_PRs_exist(repo_name=repo_name, pulls_qry=pulls_qry)
        if api_response is None:
            self.logger.info(f"No PRs for repo {repo_name}; skipping to next repo.")
            return None
        assert api_response is not None and api_response.status_code == 200, (
            f"api response isn't ok somehow, {api_response}"
        )
        json_pg = api_response.json()
        count_pulls = len(json_pg)
        self.logger.info(f"Initial query for {repo_name} shows {count_pulls} PRs.")

        page_PRs = [item.get("number") for item in json_pg]
        # print(page_PRs)

        repo_PRs = []
        repo_PRs = page_PRs  # save first page PR numbers to repo list

        sanitised_repo_name = repo_name.replace("/", "-")
        out_filename = out_json_file
        write_out = f"{self.data_location / out_filename}_{sanitised_repo_name}"
        write_out_extra_info_json = f"{write_out}_{self.current_date_info}.json"
        PR_nums_json = []
        PR_nums_json.extend(json_pg)

        if is_this_single_page(api_response.links):
            self.logger.info(f"single page of PRs only for repo {repo_name}; <=100")

        else:
            # use pagination to get 'next page' url for query
            next_pg = api_response.links["next"]["url"]
            while next_pg is not None:
                self.logger.info(
                    f"more than one pages of PRs for repo {repo_name}; >100"
                )

                self.logger.info(f"getting json via request url {next_pg}.")
                try:
                    api_response = run_with_retries(
                        fn=lambda: raise_if_response_error(
                            api_response=self.s.get(url=next_pg, headers=self.headers),
                            repo_name=repo_name,
                            logger=self.logger,
                        ),
                        logger=self.logger,
                    )
                    print(api_response)
                except RepoNotFoundError:
                    print(f"Repo {repo_name} not found; skipping this repo.")
                    # this is intentionally skipping repos which don't exist
                    return None
                    # if I get RepoNotFoundError, I want to SKIP TO NEXT REPO.
                else:
                    self.logger.info(
                        f"API response to next page query {next_pg} was {api_response}."
                    )

                json_pg = api_response.json()

                # JSON HANDLING
                PR_nums_json.extend(json_pg)

                count_pulls = len(json_pg)
                # print(count_pulls)

                page_PRs = [item.get("number") for item in json_pg]
                # print(page_PRs)
                repo_PRs.extend(
                    page_PRs
                )  # add these PRs to the existing list (extend), not add this list within another list (append)
                # print(len(repo_PRs))

                # next_pg is the iterator condition for the while loop handling pagination! Do not remove this unless refactoring completely!
                next_pg = api_response.links.get(
                    "next", {}
                ).get(
                    "url"
                )  # THIS IS IMPORTANT! This is a while loop which runs until next_pg is NONE.

        self.logger.info(f"Number of total PRs in repo {repo_name} is: {len(repo_PRs)}")

        with open(
            write_out_extra_info_json, "w"
        ) as json_file:  # writes out 1 entry per PR
            json.dump(PR_nums_json, json_file)

        return repo_PRs  # list of PR numbers

    def get_review_comments_for_PR(self, PR_number: int, PR_review_number: int):
        """
        Function which pulls the pr_comments (ie review discussion/comments/subcomments)
        """
        pass

    def loop_over_repo_PRs(
        self,
        repo_name: str,
        repo_PRs: list[int],
        out_json_file: str = "all-PR-reviews_json",
        per_pg: int | str = 100,
        # page:int | None =1,
    ) -> dict[int, list[int]]:
        """
        Writes out JSON file of PR 'main' reviews across ALL repo_PRs given.
        Returns SUMMARY DICT with: {PR_num : [total number of reviews for that PR]}
        """
        # for each PR_number in PRs_list:
        # do:

        sanitised_repo_name = repo_name.replace("/", "-")
        out_filename_main = out_json_file + "_main-reviews_"
        out_filename_sub = out_json_file + "_sub-reviews_"
        write_out_main = (
            f"{self.data_location / out_filename_main}_{sanitised_repo_name}"
        )
        write_out_sub = f"{self.data_location / out_filename_sub}_{sanitised_repo_name}"
        write_out_extra_info_json_main = (
            f"{write_out_main}_{self.current_date_info}.json"
        )
        write_out_extra_info_json_sub = f"{write_out_sub}_{self.current_date_info}.json"

        # Count number of 'reviews' for each PR for single repo.
        PR_reviews: dict[int, list[int]] = {}
        PR_reviews_json_all = []

        for PR in repo_PRs:
            print(f"Pull Request ID: {PR}")

            PR_review_nums, PR_reviews_json = self.count_PR_reviews(
                repo_name=repo_name,
                PR_num=PR,
                reviews_qry=None,
            )
            self.logger.info(
                f"{sum(PR_review_nums)} found for PR {PR} in repo {repo_name}."
            )
            PR_reviews_json_all.extend(PR_reviews_json)
            PR_reviews[PR] = PR_review_nums

            main_reviews = [
                item.get("id") for item in PR_reviews_json_all
            ]  # from the concatenated json output in this PR loop e.g. PR 1, get all the 'main' reviews as list of IDs to create further queries for

            sub_reviews_json_all = []
            sub_reviews_ids_all = []

            if main_reviews is not None:
                # loop through the main reviews to get sub-reviews
                for review in main_reviews:
                    sub_reviews_ids_PR = []
                    sub_reviews_json_PR = []
                    sub_review_query = self.review_comments_query_url(  # construct sub-review query for this PR.
                        PR_number=PR,
                        PR_review_number=review,
                        repos_api_url="https://api.github.com/repos/",
                        repo_name=repo_name,
                        per_pg=per_pg,
                        page=None,
                    )
                    self.logger.debug(
                        f"Assembled sub review query: {sub_review_query} for PR {PR} and main review {review}"
                    )
                    self.logger.debug(
                        f"Running sub review query: {sub_review_query} for PR {PR} and main review {review}..."
                    )
                    # run the query
                    api_response = run_with_retries(
                        fn=lambda: raise_if_response_error(
                            api_response=self.s.get(
                                url=sub_review_query, headers=self.headers
                            ),
                            repo_name=repo_name,
                            logger=self.logger,
                        ),
                        logger=self.logger,
                    )
                    self.logger.debug(
                        f"API response {api_response} for sub review query: {sub_review_query} for PR {PR} and main review {review}"
                    )
                    sub_reviews_ids = [item.get("id") for item in api_response.json()]
                    self.logger.debug(
                        f"{len(sub_reviews_ids)} sub_review IDs for review ID {review}: {sub_reviews_ids}"
                    )
                    sub_reviews_json_PR.extend(
                        api_response.json()
                    )  # add sub-reviews JSON to the accumulator list for this MAIN review
                    sub_reviews_ids_PR.extend(sub_reviews_ids)

                    if is_this_single_page(api_response.links):
                        self.logger.debug(
                            f"single page of subreviews only for repo {repo_name} on PR {PR} for review ID {review}; <=100"
                        )
                    else:
                        # use pagination to get 'next page' url for query
                        next_pg = api_response.links["next"]["url"]
                        while (
                            next_pg is not None
                        ):  # IMPORTANT: while loop runs until no next_pg url link.
                            self.logger.info(
                                f"more than one page of subreviews for repo {repo_name} on PR {PR} for review ID {review}; >100"
                            )

                            self.logger.info(f"getting json via request url {next_pg}.")
                            # try:
                            api_response = run_with_retries(
                                fn=lambda: raise_if_response_error(
                                    api_response=self.s.get(
                                        url=next_pg, headers=self.headers
                                    ),
                                    repo_name=repo_name,
                                    logger=self.logger,
                                ),
                                logger=self.logger,
                            )
                            print(api_response)

                            # get next page of json content for sub-reviews for this main review
                            sub_reviews_json_PR.extend(api_response.json())
                            # get next page of sub-review IDs for sub-reviews on this page
                            sub_reviews_ids_PR.extend(
                                [item.get("id") for item in api_response.json()]
                            )

                            # next_pg is the iterator condition for the while loop handling pagination! Do not remove this unless refactoring completely!
                            next_pg = api_response.links.get(
                                "next", {}
                            ).get(
                                "url"
                            )  # THIS IS IMPORTANT! This is a while loop which runs until next_pg is NONE.

                    self.logger.info(
                        f"There were {len(sub_reviews_ids_PR)} subreviews in main review {review} for PR {PR} at repo {repo_name}."
                    )
                    self.logger.info("Running next main review check...")

                    sub_reviews_ids_all.extend(
                        sub_reviews_ids_PR
                    )  # punt these IDs into the accumulator
                    sub_reviews_json_all.extend(
                        sub_reviews_json_PR
                    )  # punt the json into the accumulator
                    self.logger.debug(
                        f"sub_reviews_ids_all length is {len(sub_reviews_ids_all)}"
                    )
                    self.logger.debug(
                        f"sub_reviews_json_all length is {len(sub_reviews_json_all)}"
                    )

                self.logger.info(
                    f"Completed check for sub-reviews in {len(main_reviews)} main reviews for PR {PR} at repo {repo_name}, and found {len(sub_reviews_ids_all)}."
                )
                # get json for sub reviews FOR THIS PR
            self.logger.info(
                f"There were {len(sub_reviews_ids_all)} sub-reviews in total accross all {len(main_reviews)} main reviews over {len(repo_PRs)} PRs for repo {repo_name}."
            )
            # write out json for sub reviews FOR ALL PRs from this repo to separate file
            self.logger.info(
                f"writing out json content for {len(sub_reviews_json_all)} SUB-reviews to file {write_out_extra_info_json_sub}"
            )
            with open(write_out_extra_info_json_sub, "w") as json_file:
                json.dump(sub_reviews_json_all, json_file)

        self.logger.info(
            f"writing out json content for {len(PR_reviews_json_all)} MAIN-reviews to file {write_out_extra_info_json_main}"
        )
        with open(write_out_extra_info_json_main, "w") as json_file:
            json.dump(PR_reviews_json_all, json_file)

        return PR_reviews


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--filepath-for-repos-list",
    metavar="PATH",
    help="Path to file containing list of repo_names separated by newlines (No commas! No quotes! Internal slash ok ie FlicAnderson/coding-smart)",
    type=str,
)


if __name__ == "__main__":
    args = parser.parse_args()
    filepath: str | Path = args.filepath_for_repos_list

    get_code_reviews = GetCodeReviews(
        config_path="githubanalysis/config.cfg", in_notebook=False, logger=None
    )

    assert filepath is not None, (
        "You must provide a filepath for the repo names list file, e.g. 'data/code_review_subset_2025-05-30_x16.txt'. "
    )

    filepath = Path(filepath)
    get_code_reviews.logger.info(f"reading repo names from file: {filepath}")
    repo_list = get_code_reviews.get_repos(repo_list_file_name=filepath)

    # loop through repo_list
    print(f"{repo_list = }")

    # for each repo in repo_list, do:
    results = get_code_reviews.loop_over_repos(repo_list=repo_list)

    print(results)
    print("Get code reviews info complete")
