"""Code to get details of changes per commit in GH repo, by commit hash."""

import pandas as pd
import logging
import datetime
import requests
from requests.adapters import HTTPAdapter, Retry

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth


def make_commit_url(repos_api_url: str, repo_name: str, commit_sha: str):
    """Combine elements of API string for github API request"""
    return f"{repos_api_url}{repo_name}/commits/{commit_sha}"


class CommitChanges:
    logger: logging.Logger

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_commit_changes_logs.txt",
            )
        else:
            self.logger = logger

        self.s = requests.Session()
        retries = Retry(
            total=10,
            connect=5,
            read=3,
            backoff_factor=1.5,
            status_forcelist=[202, 502, 503, 504],
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retries))
        self.gh_token = ghauth.setup_github_auth(config_path=config_path)
        self.headers = {"Authorization": "token " + self.gh_token}
        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name

    def get_commit_changes(self, repo_name: str, commit_hash: str) -> pd.DataFrame:
        repos_api_url = "https://api.github.com/repos/"
        commit_url = make_commit_url(repos_api_url, repo_name, commit_hash)

        api_response = self.s.get(url=commit_url, headers=self.headers)

        commit_json = api_response.json()

        commit_changes_dict = [
            {
                "commit_hash": commit_hash,
                "filename": commit["filename"],
                "changes": commit["changes"],
                "additions": commit["additions"],
                "deletions": commit["deletions"],
            }
            for commit in commit_json["files"]
        ]

        commit_changes_df = pd.DataFrame.from_dict(commit_changes_dict)

        return commit_changes_df

    def get_commit_total_changes(self, commit_changes_df: pd.DataFrame) -> int:
        n_commit_changes = sum(commit_changes_df.changes)

        return n_commit_changes

    def get_commit_files_changed(self, commit_changes_df: pd.DataFrame) -> int:
        n_commit_files = commit_changes_df.filename.nunique()

        return n_commit_files
