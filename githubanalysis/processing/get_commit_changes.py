"""Code to get details of changes per commit in GH repo, by commit hash."""

import pandas as pd
import logging
import datetime
from time import sleep
import requests
from requests.adapters import HTTPAdapter, Retry

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.processing.gh_API_rate_limit_handler as ratehandle

from typing import TypedDict


class CommitInfo(TypedDict):
    commit_hash: str
    changes: int
    filename: str
    additions: int
    deletions: int


def make_commit_url(repos_api_url: str, repo_name: str, commit_sha: str):
    """Combine elements of API string for github API request"""
    return f"{repos_api_url}{repo_name}/commits/{commit_sha}"


class RateLimitError(RuntimeError):
    waittime: int

    def __init__(self, waittime: int):
        self.waittime = waittime
        super().__init__()


class UnexpectedAPIError(RuntimeError):
    pass


class CommitChanges:
    logger: logging.Logger

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        config_path: str,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_commit_changes_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.s = requests.Session()
        self.s.mount(
            "https://",
            HTTPAdapter(
                max_retries=Retry(
                    total=10,
                    connect=5,
                    read=3,
                    backoff_factor=1,
                    status_forcelist=[202, 502, 503, 504],
                )
            ),
        )
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

    def __del__(self):
        self.s.close()

    def get_commit_changes_with_retries(self, commit_hash: str, max_retries=25):
        assert max_retries > 0
        retries = 0
        while retries < max_retries:
            try:
                return self.get_commit_changes(commit_hash=commit_hash)
            except RateLimitError as e:
                retries += 1
                sleep(e.waittime)  # in seconds
                self.logger.debug(f"Sleep of {e.waittime} seconds complete.")
        raise RuntimeError("Hit maximum number of retries")

    def get_commit_changes(self, commit_hash: str) -> pd.DataFrame | None:
        repos_api_url = "https://api.github.com/repos/"
        commit_url = make_commit_url(repos_api_url, self.repo_name, commit_hash)

        self.logger.info(
            f"Attempting to gather commit changes for repo {self.repo_name} with commit_url {commit_url}."
        )
        self.logger.info(f"Session info: {self.s}")

        api_response = self.s.get(url=commit_url, headers=self.headers)
        self.logger.info(
            f"API response is {api_response.status_code} for call to commit-hash {commit_hash} for repo {self.repo_name} and API response headers are {api_response.headers}."
        )

        headers_out = api_response.headers
        self.logger.debug(
            f"record ID request headers limit/remaining: {headers_out}/{headers_out.get('x-ratelimit-remaining')}"
        )
        if api_response.status_code == 403 or api_response.status_code == 429:
            self.logger.debug(
                f"API response code is {api_response.status_code} and API response is: {api_response}; headers are {api_response.headers}. "
            )
            if api_response.headers.get("X-RateLimit-Remaining") == "0":
                resettime = api_response.headers.get("X-RateLimit-Reset")
                if resettime is not None:
                    resettime = int(resettime)
                else:
                    raise RuntimeError(
                        "Reset time value 'X-RateLimit-Reset' resettime is None"
                    )
                waittime = ratehandle.wait_until_calc(reset_time=resettime)
            else:
                waittime = 1
            self.logger.error(
                f"Waiting {waittime} seconds as API rate limit remaining is {api_response.headers.get('X-RateLimit-Remaining')} and reset time is {api_response.headers.get('X-RateLimit-Reset')} in epoch seconds."
            )
            raise RateLimitError(waittime=waittime)

        if api_response.status_code == 200:
            commit_json = api_response.json()

            if commit_json["files"] == []:
                commit_changes: list[CommitInfo] = [
                    {
                        "commit_hash": commit_hash,
                        "filename": "",
                        "changes": 0,
                        "additions": 0,
                        "deletions": 0,
                    }
                ]
            else:
                commit_changes: list[CommitInfo] = [
                    {
                        "commit_hash": commit_hash,
                        "filename": commit["filename"],
                        "changes": commit["changes"],
                        "additions": commit["additions"],
                        "deletions": commit["deletions"],
                    }
                    for commit in commit_json["files"]
                ]

                commit_changes_df = pd.DataFrame(commit_changes)
                self.logger.info(
                    f"Dataframe of length {len(commit_changes_df)} obtained for commit-hash {commit_hash} for repo {self.repo_name}."
                )

                if commit_changes_df.empty:
                    commit_changes = [
                        {
                            "commit_hash": commit_hash,
                            "filename": "",
                            "changes": 0,
                            "additions": 0,
                            "deletions": 0,
                        }
                    ]
                    commit_changes_df = pd.DataFrame(commit_changes)
                    return commit_changes_df
                else:
                    return commit_changes_df

        else:
            raise UnexpectedAPIError(
                f"API response not OK, please investigate for commit {commit_hash} at repo {self.repo_name}; API response is: {api_response}; headers are: {api_response.headers}."
            )

    def get_commit_total_changes(
        self, commit_changes_df: pd.DataFrame | None, commit_hash: str
    ) -> tuple[int | None, str]:
        if commit_changes_df is not None and not commit_changes_df.empty:
            n_commit_changes = sum(commit_changes_df.changes)

            return n_commit_changes, commit_hash
        else:
            self.logger.info(
                f"Beware: commit_changes_df is empty or None for commit {commit_hash} and contains NO changes."
            )
            return None, commit_hash

    def get_commit_files_changed(
        self, commit_changes_df: pd.DataFrame | None, commit_hash: str
    ) -> tuple[int | None, str]:
        if commit_changes_df is not None and not commit_changes_df.empty:
            n_commit_files = commit_changes_df.filename.nunique()

            return n_commit_files, commit_hash

        else:
            self.logger.info(
                f"Beware: commit_changes_df is empty or None for commit {commit_hash} and contains NO changes."
            )
            return None, commit_hash
