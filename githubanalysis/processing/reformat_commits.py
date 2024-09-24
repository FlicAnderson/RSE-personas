"""Should reformat raw commit data (currently dict of lists) into pd.DataFrame appropes format."""

import pandas as pd
import logging
import datetime
import json

import utilities.get_default_logger as loggit


class CommitReformatter:
    logger: logging.Logger

    def __init__(
        self,
        repo_name,
        in_notebook: bool,
        logger: logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/commits_reformatters_logs.txt",
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits
        self.sanitised_repo_name = repo_name.replace("/", "-")
        self.reformatted_commits = None

    def reformat_commits_object(self, unique_commits_all_branches: dict[str, list]):
        """
        Reformat previously-made commit data (from get_all_branches_commits() ) into pd.DataFrame.
        """
        repo_name = self.sanitised_repo_name.replace("-", "/")

        columns = [
            "repo_name",
            "branch_sha",
            "commit_sha",
            "author_fullname",
            "author_commit_date",
            "commit_message",
            "author_field",
            "comitter_field",
            "committer_commit_date",
        ]
        frame = []

        for branch, commits in unique_commits_all_branches.items():
            for commit in commits:
                frame.append(
                    [
                        repo_name,
                        branch,
                        commit["sha"],
                        commit["commit"]["author"]["name"],
                        commit["commit"]["author"]["date"],
                        commit["commit"]["message"],
                        commit["commit"]["author"],
                        commit["commit"]["committer"],
                        commit["commit"]["committer"]["date"],
                    ]
                )

        self.reformatted_commits = pd.DataFrame(frame, columns=columns)

        return self.reformatted_commits

    def reformat_commits_from_file(self, commits_file: str):
        """
        Reformat raw commit data from json file into pd.DataFrame appropes format.
        """

        with open(commits_file, "r") as raw_commits_file:
            raw_commits = json.load(raw_commits_file)

        return self.reformat_commits_object(raw_commits)

    def save_formatted_commits(
        self, write_out_location, out_filename="processed-commits"
    ):
        """
        Save the reformatted commits data out to csv file.
        """

        if self.in_notebook:
            write_out = f"../../{write_out_location}{out_filename}_{self.sanitised_repo_name}_{self.current_date_info}.csv"  # look further up for correct path
        else:
            write_out = f"{write_out_location}{out_filename}_{self.sanitised_repo_name}_{self.current_date_info}.csv"

        if self.reformatted_commits is not None:
            self.reformatted_commits.to_csv(
                path_or_buf=write_out, mode="w", index=True, header=True
            )
        else:
            raise RuntimeError(
                f"Error: Failed saving reformatted commits data out to {write_out}. Run reformat_commits*() function."
            )
