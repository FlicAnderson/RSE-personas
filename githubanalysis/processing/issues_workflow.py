"""Workflow for running issues processing and analysis code for 1 repo."""

import logging
import datetime
import pandas as pd

import utilities.get_default_logger as loggit
from utilities.check_gh_reponse import UnexpectedAPIError
from githubanalysis.processing.get_all_pages_issues import IssueGetter


class RunIssues:
    logger: logging.Logger
    config_path: str
    in_notebook: bool
    current_date_info: str
    sanitised_repo_name: str
    repo_name: str
    write_read_location: str

    def __init__(
        self,
        repo_name: str,
        in_notebook: bool,
        config_path: str,
        write_read_location: str,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/issues_workflow_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.repo_name = repo_name
        self.write_read_location = write_read_location

    def check_repo_valid(self):
        pass

    def check_repo_has_issues(self):
        pass

    def check_existing_formatted_issues(self):
        pass

    def run_all_issues(self):  # -> pd.DataFrame:
        pass
        # return processed_issues
