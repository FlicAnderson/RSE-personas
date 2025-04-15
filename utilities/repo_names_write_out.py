"""Utility to write out repo_names nicely; Originated from workflow_preparation.py."""

import datetime
from pathlib import Path
import logging

import utilities.get_default_logger as loggit


class RepoNamesListCreator:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/utilities_repo_names_write_out.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.write_location = Path("data/" if not in_notebook else "../../data/")

    def repo_names_write_out(
        self,
        namelist: list[str | None],
        repo_name_filename: str = "repo_names_list",
    ) -> str:
        """
        Write the stripped repo_names to text file one per line (no commas).
        Returns writeout filepath as string.
        Writes out in chaotic unsorted manner.
        """
        current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")
        listlen = len(namelist)
        filename = f"{self.write_location}{repo_name_filename}_{current_date_info}_x{listlen}.txt"

        with open(filename, "w") as file:
            for repo in namelist:
                if repo is not None:
                    file.write(repo + "\n")
                else:
                    continue

        self.logger.info(f"Wrote out {listlen} records to file {filename}.")
        return filename
