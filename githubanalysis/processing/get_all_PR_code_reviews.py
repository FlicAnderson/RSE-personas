"""Get code review data if present for repos; save out to files."""

import logging

# import pandas as pd
# import numpy as np
import argparse
from pathlib import Path
from run_commits_workflow import read_repos_from_file
from githubanalysis.setup_classes import RESTRequestSetup, DatasetSetup
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries


class GetCodeReviews(RESTRequestSetup):
    def _log_name(self) -> str:
        return "get_all_PR_code_reviews"

    def __init__(
        self, config_path: str, in_notebook: bool, logger: None | logging.Logger = None
    ) -> None:
        super().__init__(config_path, in_notebook, logger)

    def get_repos(
        self,
        repo_list_file: Path,
    ):
        repo_list = read_repos_from_file(filename=repo_list_file, logger=self.logger)
        return repo_list

    def loop_over_repos(
        self,
        repo_list: list[str],
    ):
        # for each repo_name in repo_list:
        # do:
        # ...
        pass

    def get_PR_numbers(self, repo_name: str) -> list[int]:
        """should get pull request numbers to loop through to check for code reviews."""
        # create API request to use repo_name, and get PR numbers
        PRs_api_url = f"https://api.github.com/repos/{repo_name}/pulls"
        # make query from PRs_api_url and other headers/info
        # and return PRs_list list of ints to query separately.
        # PRs_list = # parsed list of ints from json response
        return PRs_list

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

    get_code_reviews = GetCodeReviews(config_path="", in_notebook=False, logger=None)

    assert (
        filepath is not None
    ), "You must provide a filepath for the repo names list file, e.g. 'data/code_review_subset_2025-05-30_x12.txt'. "

    filepath = Path(filepath)
    get_code_reviews.logger.info(f"reading repo names from file: {filepath}")
    repo_list = get_code_reviews.get_repos(repo_list_file=filepath)

    # loop through repo_list

    # for each repo in repo_list, do:
    get_code_reviews.loop_over_repos(repo_list=repo_list)
