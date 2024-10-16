import logging
import pandas as pd
import datetime

import utilities.get_default_logger as loggit


from githubanalysis.processing.commits_workflow import RunCommits
import githubanalysis.processing.gh_API_rate_limit_handler as ratehandler


import argparse


parser = argparse.ArgumentParser()
parser.add_argument(
    "--repo-names",
    metavar="PATH",
    help="Name of the repo to workflow",
    type=str,
)


def single_repo_method(repo_name: str):
    runcommits = RunCommits(
        repo_name=repo_name,
        in_notebook=True,
        config_path="../../githubanalysis/config.cfg",
        write_read_location="../../data/",
    )
    repodf = runcommits.do_it_all()
    return repodf


def read_repos_from_file(filename):
    with open(filename, "r") as f:
        repos = [txtline.strip() for txtline in f.readlines()]
        return multi_repo_method(repo_names=repos)


def multi_repo_method(repo_names: list[str]):
    """
    Loop through several repos from a file input, running
    single_repo_method() on each.
    Return dictionary of repodfs with repo_name as key.
    """
    collation_dict = {}
    for item in repo_names:
        repodf = single_repo_method(repo_name=item)
        collation_dict[item] = repodf
    return collation_dict


if __name__ == "__main__":
    args = parser.parse_args()
    names = args.repo_names
