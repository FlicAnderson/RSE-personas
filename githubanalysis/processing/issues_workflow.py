"""Workflow for running issues processing and analysis code for 1 repo."""

import logging
import datetime
import pandas as pd

import utilities.get_default_logger as loggit
from utilities.check_gh_reponse import UnexpectedAPIError
from githubanalysis.processing.get_all_pages_issues import IssueGetter, NoIssuesError
from utilities.check_gh_reponse import raise_if_response_error, run_with_retries


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

    def check_repo_valid(self) -> bool:
        issuesgetter = IssueGetter(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
            logger=self.logger,
        )
        try:
            repo_has_issues = issuesgetter.check_repo_has_issues(
                repo_name=self.repo_name
            )
            assert repo_has_issues, f"There are NO issues enabled for repo {self.repo_name}. Cannot obtain issues data for this repo."
            return repo_has_issues
        except NoIssuesError as e:
            self.logger.error(f"Error: Issues are not enabled for this repo: {e}")
            return False

    def check_existing_formatted_issues(self):
        pass

    def get_issues(self):
        issuesgetter = IssueGetter(
            repo_name=self.repo_name,
            in_notebook=self.in_notebook,
            config_path=self.config_path,
            logger=self.logger,
        )

        # main issue getting function:
        all_issues = issuesgetter.get_all_pages_issues(repo_name=self.repo_name)
        return all_issues

    def run_all_issues(self):  # -> pd.DataFrame:
        self.logger.info(f"Checking whether repo {self.repo_name} has issues enabled.")
        worth_running = self.check_repo_valid()

        if worth_running:
            # DO ISSUE GETTING THINGS

            self.logger.info(
                f"Running run_all_issues() to get all issues data for repo {self.repo_name}."
            )

            all_issues = self.get_issues()

            return all_issues

            # TODO:
            # process issues data

            # ?? column handling

            # all_issues  # JSON TO DATAFRAME

            # if processed_issues is None or processed_issues.empty:
            #     raise pd.errors.EmptyDataError(
            #         "Frame is None or pd.DataFrame is empty; perhaps no issues?"
            #     )

            # log retyping of json to df

            #

            # Write out to CSVs
            # log writeout

            # return processed issues data (pd.df format)
            # return processed_issues

        else:
            # EXIT TO NEXT OR SOMETHING? NoIssuesError has been invoked...
            self.logger.info(
                f"There are no issues for repo {self.repo_name}; workflow not run."
            )
