"""Get code review data if present for repos; save out to files."""

import logging

# import pandas as pd
# import numpy as np
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

            repo_PRs = self.get_PR_numbers(repo_name=repo)
            if repo_PRs is not None:
                print(f"repo {repo} contains PRs: {repo_PRs}")
            else:
                print(f"No PRs for repo {repo}; skipping to next repo.")
                continue

            # check for API response
            # if I get RepoNotFoundError, I want to SKIP TO NEXT REPO. (done by RepoNotFound Error in check_PRs_exist() )

            # for repo, run get_PR_numbers(repo_name = repo)
            # get PRs_list of ints from json response
            # store in useful format for using to query separately using loop_over_repo_PRs(PRs_list)

            # (in loop_over_repo_PRs(PRs_list):)
            # for PR in PRs_list, run get_review_comments_for_PR(PR_number=PR)
            # get review comments, get GH_username and other similar info required, timestamps etc.
            # save out raw data to json file
            # combine into per-repo_name df or other structure, labelled appropriately

            # (collate and log per-repo stats: e.g. N of PRs, N of PRs with reviews, N of reviews per PR, N of GH_usernames etc )

            # shift to next repo in repo_list.

        pass

    def check_PRs_exist(self, repo_name: str, pulls_qry: str):
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

    def get_PR_numbers(self, repo_name: str) -> list[int] | None:
        """should get pull request numbers to loop through to check for code reviews."""
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
        if api_response is not None and api_response.status_code == 200:
            json_pg = api_response.json()
            count_pulls = len(json_pg)
            self.logger.info(f"Initial query for {repo_name} shows {count_pulls} PRs.")

            page_PRs = [item.get("number") for item in json_pg]
            # print(page_PRs)

            repo_PRs = []
            repo_PRs = page_PRs  # save first page PR numbers to repo list

            if is_this_single_page(api_response.links):
                self.logger.info(f"single page of PRs only for repo {repo_name}; <=100")

            elif not is_this_single_page(
                api_response.links
            ):  # use bool result from get_all_pages_issues.py function
                # print(len(repo_PRs))
                self.logger.info(
                    f"more than one pages of PRs for repo {repo_name}; >100"
                )
                next_pg = api_response.links["next"][
                    "url"
                ]  # use pagination to get 'next page' url for query

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
                    return (
                        None  # this is intentionally skipping repos which don't exist.
                    )
                    # if I get RepoNotFoundError, I want to SKIP TO NEXT REPO.
                else:
                    self.logger.info(
                        f"API response to next page query {next_pg} was {api_response}."
                    )

                json_pg = api_response.json()
                count_pulls = len(json_pg)
                # print(count_pulls)

                page_PRs = [item.get("number") for item in json_pg]
                # print(page_PRs)
                repo_PRs.extend(
                    page_PRs
                )  # add these PRs to the existing list (extend), not add this list within another list (append)
                # print(len(repo_PRs))

            self.logger.info(
                f"Number of total PRs in repo {repo_name} is: {len(repo_PRs)}"
            )
            return repo_PRs  # list of PR numbers
        else:
            self.logger.warning(f"API response for query wasn't OK: {api_response}")
            return None  # api response wasn't ok

    def loop_over_repo_PRs(self, PRs_list: list[int]):
        # for each PR_number in PRs_list:
        # do:
        # ...
        pass

    def get_review_comments_for_PR(self, PR_number: int):
        pass


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

    assert (
        filepath is not None
    ), "You must provide a filepath for the repo names list file, e.g. 'data/code_review_subset_2025-05-30_x16.txt'. "

    filepath = Path(filepath)
    get_code_reviews.logger.info(f"reading repo names from file: {filepath}")
    repo_list = get_code_reviews.get_repos(repo_list_file_name=filepath)

    # loop through repo_list
    print(f"{repo_list = }")

    # for each repo in repo_list, do:
    get_code_reviews.loop_over_repos(repo_list=repo_list)
