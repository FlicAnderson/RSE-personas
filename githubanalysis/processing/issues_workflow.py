"""Workflow for running issues processing and analysis code for 1 repo."""

import logging
import datetime
import json
import pandas as pd
from pathlib import Path

import utilities.get_default_logger as loggit
from githubanalysis.processing.get_all_pages_issues import IssueGetter, NoIssuesError


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
            self.logger.error(
                f"Error: Issues are not enabled for repo {self.repo_name}: {e}"
            )
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

        raw_issues_filename = f"{self.write_read_location}all-issues_{self.sanitised_repo_name}_{self.current_date_info}.json"
        raw_issues_path = Path(raw_issues_filename)
        self.logger.info(
            f"Checking whether issue tickets data for repo {self.repo_name} for today's date already exists at path {raw_issues_path}."
        )

        if raw_issues_path.is_file():
            with open(raw_issues_filename) as f1:
                raw_issues_json = json.load(f1)
                f1.close
            assert isinstance(
                raw_issues_json,
                list,  # json wrapped in list
            ), f"Error reading in raw .json file: {raw_issues_filename}."
            self.logger.info("Reading in existing issues raw .json file.")
            return raw_issues_json
        else:
            # run main issue getting function:
            self.logger.info(
                "No existing issues file found; getting issues via GH API."
            )
            all_issues = issuesgetter.get_all_pages_issues(repo_name=self.repo_name)
            return all_issues

    def format_issues_object(self, issues_object: list[dict]) -> pd.DataFrame:
        repo_name = self.repo_name
        columns = [
            "repo_name",
            "issue_id",
            "issue_number",
            "issue_state",
            "issue_title",
            "created_at",
            "updated_at",
            "closed_at",
            "author_association",
            "comments",
            "issue_author",
            "issue_assignees",
            "issue_author_username",
            "assignees_list_usernames",
        ]  # list of column names of data to keep from json
        frame = []  # for df construction later

        for issue in issues_object:
            user = issue["user"]
            assignees = issue["assignees"]

            issue_list = [
                repo_name,
                issue["id"],
                issue["number"],
                issue["state"],
                issue["title"],
                issue["created_at"],
                issue["updated_at"],
                issue["closed_at"],
                issue["author_association"],
                issue["comments"],
                issue["user"],
                issue["assignees"],
            ]

            issue_list.append(user.get("login") if user is not None else None)
            issue_list.append(
                lambda assignees: [assignees.get("login") for assignees in assignees]
                if assignees is not None
                else None
            )

            frame.append(issue_list)

        issues_df = pd.DataFrame(frame, columns=columns)
        return issues_df

        # dict_keys(
        # issues_required_fields = ['assignee',
        #     'closed_at',
        #     'comments',
        #     'comments_url',
        #     'events_url',
        #     'html_url',
        #     'id',
        #     'node_id',
        #     'labels',
        #     'labels_url',
        #     'milestone',
        #     'number',
        #     'repository_url',
        #     'state',
        #     'locked',
        #     'title',
        #     'url',
        #     'user',
        #     'author_association',
        #     'created_at',
        #     'updated_at']
        # )

    def run_all_issues(self):  # -> pd.DataFrame:
        self.logger.info(f"Checking whether repo {self.repo_name} has issues enabled.")
        worth_running = self.check_repo_valid()

        if worth_running:
            # DO ISSUE GETTING THINGS

            self.logger.info(
                f"Running run_all_issues() to get all issues data for repo {self.repo_name}."
            )

            all_issues = self.get_issues()

            # TODO:
            # process issues data

            # ?? column handling

            # all_issues  # JSON TO DATAFRAME

            processed_issues = self.format_issues_object(all_issues)
            return processed_issues

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
