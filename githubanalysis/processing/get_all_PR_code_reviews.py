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
        """
        Read the list of repo names from input file (commandline argument.)
        Returns list of strings (reponames)
        """
        repo_list = simple_read_repos_from_file(
            filename=self.data_location / repo_list_file_name
        )
        return repo_list

    def loop_over_repos(
        self,
        repo_list: list[str],
    ):
        """
        Run the main work.
        """

        for i, repo in enumerate(
            repo_list
        ):  # enumerate: better than manually incrementing i like a pleb, I guess
            print(f"processing repo {i} of {len(repo_list)}")
            print(f"processing repo: {repo}.")
            pulls_qry = self.make_pulls_query_url(
                repos_api_url="https://api.github.com/repos/",
                repo_name=repo,
                per_pg=100,
                page=1,
            )
            print(f"pulls query is: {pulls_qry}")

            repo_PRs = self.get_PR_numbers(
                repo_name=repo
            )  # list of PR numbers for repo

            if repo_PRs is not None:
                print(f"repo {repo} contains PRs: {repo_PRs}")
            else:
                print(f"No PRs for repo {repo}; skipping to next repo.")
                continue

            self.process_PR_reviews_one_repo(  # gather the main and sub reviews for one repo.
                repo_name=repo, repo_PRs=repo_PRs
            )
        # No return.

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

    def fetch_main_reviews_json(
        self,
        repo_name: str,
        PR_num: int,
        reviews_qry: str | None,
    ) -> list[dict[str, Any]]:
        # for given PR number in given repo, check for PR Reviews
        # if a query is supplied (e.g. from api_response.links), use that, otherwise construct the 'first page' query

        main_reviews_json = []
        if reviews_qry is None:
            reviews_qry = self.make_reviews_query_url(
                repos_api_url="https://api.github.com/repos/",
                repo_name=repo_name,
                PR_num=PR_num,
                per_pg=100,
                page=1,
            )

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

        main_reviews_json.extend(json_pg)

        if not is_this_single_page(api_response.links):
            main_reviews_json.extend(
                self.get_remaining_pgs(
                    next_pg=api_response.links["next"]["url"], repo_name=repo_name
                )
            )
            self.logger.debug("more than one pages of reviews; >100")

        return main_reviews_json

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

        sanitised_repo_name = repo_name.replace("/", "-")
        out_filename = out_json_file
        write_out = f"{self.data_location / out_filename}_{sanitised_repo_name}"
        write_out_extra_info_json = f"{write_out}_{self.current_date_info}.json"
        PR_nums_json = []
        PR_nums_json.extend(json_pg)

        if is_this_single_page(api_response.links):
            self.logger.info(f"single page of PRs only for repo {repo_name}; <=100")

        else:
            PR_nums_json.extend(
                self.get_remaining_pgs(
                    next_pg=api_response.links["next"]["url"],
                    repo_name=repo_name,
                )
            )
            # use pagination to get 'next page' url for query
        repo_PRs = [item.get("number") for item in PR_nums_json]

        self.logger.info(f"Number of total PRs in repo {repo_name} is: {len(repo_PRs)}")

        with open(
            write_out_extra_info_json, "w"
        ) as json_file:  # writes out 1 entry per PR
            json.dump(PR_nums_json, json_file)

        return repo_PRs  # list of PR numbers

    def get_remaining_pgs(
        self,
        next_pg: str | None,
        repo_name,
    ):
        # use pagination to get 'next page' url for query
        sub_reviews_json_responses = []
        # sub_reviews_ids = []
        while (
            next_pg is not None
        ):  # IMPORTANT: while loop runs until no next_pg url link.
            self.logger.info(f"getting json via request url {next_pg}.")
            # try:
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(url=next_pg, headers=self.headers),
                    repo_name=repo_name,
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            print(api_response)

            # get next page of json content for sub-reviews for this main review
            sub_reviews_json_responses.extend(api_response.json())

            # next_pg is the iterator condition for the while loop handling pagination! Do not remove this unless refactoring completely!
            next_pg = api_response.links.get(
                "next", {}
            ).get(
                "url"
            )  # THIS IS IMPORTANT! This is a while loop which runs until next_pg is NONE.
        return sub_reviews_json_responses

    def get_sub_review_from_main_review(
        self, PR, review, repo_name, per_pg
    ) -> list[dict[str, Any]]:
        sub_reviews_json_PR = []
        sub_review_query = (
            self.review_comments_query_url(  # construct sub-review query for this PR.
                PR_number=PR,
                PR_review_number=review,
                repos_api_url="https://api.github.com/repos/",
                repo_name=repo_name,
                per_pg=per_pg,
                page=None,
            )
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
                api_response=self.s.get(url=sub_review_query, headers=self.headers),
                repo_name=repo_name,
                logger=self.logger,
            ),
            logger=self.logger,
        )
        self.logger.debug(
            f"API response {api_response} for sub review query: {sub_review_query} for PR {PR} and main review {review}"
        )
        sub_reviews_json_PR.extend(
            api_response.json()
        )  # add sub-reviews JSON to the accumulator list for this MAIN review

        if not is_this_single_page(api_response.links):
            subreview_json = self.get_remaining_pgs(
                next_pg=api_response.links["next"]["url"],
                repo_name=repo_name,
            )
            sub_reviews_json_PR.extend(subreview_json)
        else:
            self.logger.debug(
                f"single page of subreviews only for repo {repo_name} on PR {PR} for review ID {review}; <=100"
            )

        sub_reviews_ids = [item.get("id") for item in api_response.json()]
        self.logger.debug(
            f"{len(sub_reviews_ids)} sub_review IDs for review ID {review}: {sub_reviews_ids}"
        )

        self.logger.info(
            f"There were {len(sub_reviews_json_PR)} subreviews in main review {review} for PR {PR} at repo {repo_name}."
        )
        self.logger.info("Running next main review check...")
        return sub_reviews_json_PR

    def get_all_sub_reviews_from_ALL_main_reviews(
        self,
        PR: int,
        main_reviews: list[int],
        repo_name,
        per_pg,
    ) -> list[dict[str, Any]]:
        all_sub_reviews = []
        # loop through the main reviews to get sub-reviews
        for review in main_reviews:
            all_sub_reviews.extend(
                self.get_sub_review_from_main_review(
                    PR, review, repo_name=repo_name, per_pg=per_pg
                )
            )

        self.logger.info(
            f"Completed check for sub-reviews in {len(main_reviews)} main reviews for PR {PR} at repo {repo_name}, and found {len(all_sub_reviews)}."
        )
        return all_sub_reviews

    def process_PR_reviews_one_repo(
        self,
        repo_name: str,
        repo_PRs: list[int],
        out_json_file: str = "all-PR-reviews_json",
        per_pg: int | str = 100,
    ):
        """
        Writes out JSON file of PR 'main' reviews across ALL repo_PRs given
        AND JSON file of SUB reviews as well.
        """

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

        PR_reviews_json_all = []

        for PR in repo_PRs:
            print(f"Pull Request ID: {PR}")

            PR_reviews_json = (
                self.fetch_main_reviews_json(  # THIS IS REALLY IMPORTANT :C
                    repo_name=repo_name,
                    PR_num=PR,
                    reviews_qry=None,
                )
            )
            self.logger.info(
                f"{len(PR_reviews_json)} found for PR {PR} in repo {repo_name}."
            )
            PR_reviews_json_all.extend(PR_reviews_json)  # assemble all the PR entries

            main_reviews = [
                item["id"]
                for item in PR_reviews_json  # JUST FOR THIS PR
                if "id" in item  # avoids Nones
            ]  # from the concatenated json output in this PR loop e.g. PR 1, get all the 'main' reviews as list of IDs to create further queries for

            sub_reviews_json_all = self.get_all_sub_reviews_from_ALL_main_reviews(
                PR, main_reviews=main_reviews, repo_name=repo_name, per_pg=per_pg
            )

            # get json for sub reviews FOR THIS PR
            self.logger.info(
                f"There were {len(sub_reviews_json_all)} sub-reviews in total accross all {len(main_reviews)} main reviews over {len(repo_PRs)} PRs for repo {repo_name}."
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
        # no return, intentionally. We're making files here.


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

    # for each repo in repo_list, do all the things:
    get_code_reviews.loop_over_repos(repo_list=repo_list)

    print("Get code reviews info complete")
