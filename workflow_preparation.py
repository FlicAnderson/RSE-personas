"""Run zenodo ID to github repo getting workflow."""

import pandas as pd
import logging
import datetime

from zenodocode.get_zenodo_ids import ZenodoIDGetter
from zenodocode.get_gh_urls import GhURLsGetter
import githubanalysis.processing.repo_name_clean as repo_name_cleaner
import utilities.get_default_logger as loggit


class RunPrep:
    logger: logging.Logger
    config_path: str = "zenodocode/zenodoconfig.cfg"
    in_notebook: bool
    current_date_info: str
    write_read_location: str

    def __init__(
        self,
        in_notebook: bool,
        config_path: str,
        write_read_location: str,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_zenodo_github_info_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.config_path = config_path
        self.in_notebook = in_notebook
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        self.write_read_location = write_read_location

    def get_Z_IDs(self, n_total_records: int = 7500) -> list[int]:
        """
        Wrapper for zenodo ID gatherer function
        """
        zenodogetter = ZenodoIDGetter(
            in_notebook=self.in_notebook,
            config_path=self.config_path,
            logger=self.logger,
            write_read_location=self.write_read_location,
        )

        z_IDs_list = zenodogetter.get_zenodo_ids(
            per_pg=100,
            total_records=n_total_records,
            all_versions=False,  # don't want all versions as interested in commits from all branches, not a specific fixed version
        )
        self.logger.info(
            f"Retrieved {len(z_IDs_list)} records to check for github info from."
        )
        return z_IDs_list

    def get_gh_zenodo_info(
        self,
        zenodo_ids: list[int],
    ) -> pd.DataFrame:
        """
        Wrapper for function which gathers GH urls from Zenodo IDs if present.
        """
        ghurlgetter = GhURLsGetter(
            in_notebook=self.in_notebook,
            config_path=self.config_path,
            logger=self.logger,
        )

        gh_info = ghurlgetter.get_gh_urls(zenodo_ids=zenodo_ids)
        return gh_info

    def repo_names_extraction(self, gh_info: pd.DataFrame) -> list[str]:
        """
        Means of pulling clean repo_name info out of the dataframe returned
        by get_gh_zenodo_info() or internal function get_gh_urls().
        """
        namelist = []
        assert type(gh_info) is pd.DataFrame, "GH dataframe cannto be of type None"
        try:
            if len(gh_info.index) >= 0:
                record_gh_repo_url = gh_info["GitHubURL"]
                for repo_url in record_gh_repo_url:
                    cleanurl = repo_name_cleaner.repo_name_clean(repo_url=repo_url)
                    namelist.append(cleanurl)
                return namelist

        except Exception as e_repo_names_extraction:
            self.logger.error(
                f"Extracting names from gh repo urls has failed somehow. Please investigate. Error: {e_repo_names_extraction} "
            )
            raise RuntimeError

    def repo_names_write_out(
        self,
        namelist: list[str],
        repo_name_filename: str = "repo_names_list",
    ) -> str:
        """
        Write the stripped repo_names to text file one per line (no commas).
        Returns writeout filepath as string.
        """
        current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")
        listlen = len(namelist)
        filename = f"{self.write_read_location}{repo_name_filename}_{current_date_info}_x{listlen}.txt"

        with open(filename, "w") as file:
            for repo in namelist:
                file.write(repo + "\n")

        self.logger.info(f"Wrote out {listlen} records to file {filename}.")
        return filename

    def workflow_preparation(
        self,
        n_total_records: int = 7500,
    ):
        self.logger.info(
            f"Running preparation workflow from {n_total_records} Zenodo software records."
        )
        z_IDs_list = self.get_Z_IDs(n_total_records)

        self.logger.info(
            f"Gathering Github information (if present) for {len(z_IDs_list)} Zenodo software records."
        )
        gh_info = self.get_gh_zenodo_info(z_IDs_list)

        self.logger.info(
            f"Pulling out repo names from all {len(gh_info)} records with GitHub information."
        )
        repo_names_list = self.repo_names_extraction(gh_info=gh_info)

        self.logger.info(
            f"Writing out {len(repo_names_list)} repo names for consumption by GitHub commits- and issues- data gathering workflows to files."
        )
        filename = self.repo_names_write_out(
            namelist=repo_names_list,
        )
        self.logger.info(
            f"Preparation workflow completed after running on {n_total_records} and wrote out {len(gh_info.index)} repo names to file at {filename}."
        )
        return filename
