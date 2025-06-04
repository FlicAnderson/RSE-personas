"""Workflow for getting GitHub repo urls from Zenodo to create a 'Research Software repo dataset'."""

from zenodocode.get_zenodo_ids import ZenodoIDGetter
from utilities.get_default_logger import get_default_logger
from zenodocode.get_gh_urls import GhURLsGetter


def main():
    """
    get github urls
    process gh urls
    write out dataset for input to githubanalysis code
    """
    config_path: str = "zenodocode/zenodoconfig.cfg"
    logger = get_default_logger(
        console=True,
        log_name="get_gh_repo_dataset",
        in_notebook=False,
    )

    id_getter = ZenodoIDGetter(
        config_path=config_path,
        in_notebook=False,
        logger=logger,
    )

    # get zenodo IDs
    ids = id_getter.get_zenodo_ids(
        per_pg=20,
        total_records=1000,
        filename="zn_ids",
    )

    # get github urls
    ghurlsgetter = GhURLsGetter(
        config_path=config_path, logger=logger, in_notebook=False
    )
    ghurlsgetter.get_gh_urls(zenodo_ids=ids, out_filename="zenodo_gh_urls")


# this bit
if __name__ == "__main__":
    main()
