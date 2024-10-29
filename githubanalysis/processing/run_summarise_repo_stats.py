"""Run summarise_repo_stats() to generate rough info on given repo to allow targeting of further datagrabs."""

from githubanalysis.processing.summarise_repo_stats import RepoStatsSummariser


import argparse
import pandas as pd
from logging import Logger
import utilities.get_default_logger as loggit
from utilities.check_gh_reponse import RepoNotFoundError


def single_repo_method(repo_name: str, logger: Logger) -> dict | None:
    """
    This is used by multi_repo_method()
    """
    summarise_stats = RepoStatsSummariser(
        repo_name=repo_name,
        in_notebook=False,  # TODO
        config_path="githubanalysis/config.cfg",  # TODO make this editable and useful
        write_read_location="data/",  # TODO
    )
    try:
        return summarise_stats.summarise_repo_stats(repo_name=repo_name)
    except RepoNotFoundError as e:
        logger.error(
            f"Encountered repo-getting-workflow-borking error in repo {repo_name}; Repo DOES NOT EXIST or is private: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Encountered repo-getting-workflow-borking error in repo {repo_name}; error {e}"
        )
        return None


def read_repos_from_file(filename, logger: Logger) -> dict[str, pd.DataFrame | None]:
    with open(filename, "r") as f:
        repos = [txtline.strip() for txtline in f.readlines()]
        return multi_repo_method(repo_names=repos, logger=logger)


def multi_repo_method(
    repo_names: list[str], logger: Logger
) -> dict[str, pd.DataFrame | None]:
    """
    Loop through several repos from a file input, running
    single_repo_method() on each.
    Return dictionary of stats dicts with repo_name as key.
    """
    repo_names = list(set(repo_names))
    collation_dict = {}
    for repo in repo_names:
        logger.info(f"Trying to reading repo {repo} data from GH API.")
        print(f"Getting repo data for {repo}.")
        collation_dict[repo] = single_repo_method(repo_name=repo, logger=logger)
        logger.info(f"Completed repo data get for {repo}.")
    return collation_dict


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--filepath-for-repos-list",
    metavar="PATH",
    help="Path to file containing list of repo_names separated by newlines (No commas! No quotes! Internal slash ok ie FlicAnderson/coding-smart)",
    type=str,
)
parser.add_argument(
    "-r",
    "--repo-name",
    metavar="REPO_NAME",
    help="Name of the single repo to workflow",
    type=str,
)
parser.add_argument(
    "-s",
    "--several-repo-names",
    metavar="REPO_NAME",  # this is OK to be repeated from above because of nargs
    nargs="+",  # this is convention indicating that there's many
    help="NameS of the multiple repos to workflow",
)

if __name__ == "__main__":
    args = parser.parse_args()
    filepath: str | None = args.filepath_for_repos_list
    repo_name: str | None = args.repo_name
    several_repo_names: list[str] = args.several_repo_names

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="INFO",
        log_name="logs/run_summarise_repos_stats_workflow_logs.txt",
        in_notebook=False,
    )

    if (
        (filepath is not None)
        + (repo_name is not None)
        + (several_repo_names is not None)
    ) != 1:
        logger.error(
            "Exactly one argument allowed; please avoid your current whole deal."
        )
        exit(1)

    if repo_name is not None:
        logger.info(
            f"Running single repo method to summarise repo stats on {repo_name}"
        )
        single_repo_method(repo_name=repo_name, logger=logger)

    elif several_repo_names is not None:
        logger.info(
            f"Running multi repo method  to summarise repo stats on list: {several_repo_names}"
        )
        multi_repo_method(repo_names=several_repo_names, logger=logger)

    elif filepath is not None:
        logger.info(
            f"Running multi repo method to summarise repo stats on repos in file: {filepath}"
        )
        read_repos_from_file(filename=filepath, logger=logger)
