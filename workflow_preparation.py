"""Run zenodo ID to github repo getting workflow."""

import pandas as pd
from logging import Logger
import datetime

from zenodocode.get_zenodo_ids import ZenodoIDGetter
from zenodocode.get_gh_urls import GhURLsGetter
import githubanalysis.processing.repo_name_clean as repo_name_cleaner
import utilities.get_default_logger as loggit

logger = loggit.get_default_logger(
    console=False, set_level_to="INFO", log_name="logs/get_zenodo_github_info_logs.txt"
)


def get_Z_IDs(n_total_records: int = 7500) -> list[int]:
    """
    Wrapper for zenodo ID gatherer function
    """
    zenodogetter = ZenodoIDGetter(
        in_notebook=False, config_path="zenodocode/zenodoconfig.cfg", logger=logger
    )

    z_IDs_list = zenodogetter.get_zenodo_ids(
        per_pg=100, total_records=n_total_records, all_versions=False
    )
    logger.info(f"Retrieved {len(z_IDs_list)} records to check for github info from.")
    return z_IDs_list


def get_gh_zenodo_info(zenodo_ids: list[int]) -> pd.DataFrame:
    """
    Wrapper for function which gathers GH urls from Zenodo IDs if present.
    """
    ghurlgetter = GhURLsGetter(
        config_path="zenodocode/zenodoconfig.cfg", logger=logger, in_notebook=False
    )

    gh_info = ghurlgetter.get_gh_urls(zenodo_ids=zenodo_ids)
    return gh_info


def repo_names_extraction(gh_info: pd.DataFrame) -> list[str]:
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
        logger.error(
            f"Extracting names from gh repo urls has failed somehow. Please investigate. Error: {e_repo_names_extraction} "
        )


def repo_names_write_out(
    namelist: list[str],
    write_out_location: str = "data/",
    repo_name_filename="repo_names_list",
):
    """
    Write the stripped repo_names to text file one per line.
    """
    current_date_info = datetime.datetime.now().strftime("%Y-%m-%d")
    listlen = len(namelist)
    filename = (
        f"{write_out_location}{repo_name_filename}_{current_date_info}_x{listlen}.txt"
    )

    with open(filename, "w") as file:
        for repo in namelist:
            file.write(repo + "\n")

    logger.info(f"Wrote out {listlen} records to file {filename}.")
    return filename


def workflow_preparation(
    n_total_records: int = 7500,
    config_path: str = "zenodocode/zenodoconfig.cfg",
    logger: Logger = logger,
    in_notebook=False,
):
    z_IDs_list = get_Z_IDs(n_total_records=7500)

    gh_info = get_gh_zenodo_info(zenodo_ids=z_IDs_list)

    repo_names_list = repo_names_extraction(gh_info=gh_info)

    filename = repo_names_write_out(
        namelist=repo_names_list,
        write_out_location="data/",
    )

    logger.info(
        f"Preparation workflow completed after running on {n_total_records} and wrote out {len(gh_info.index)} repo names to file at {filename}."
    )
