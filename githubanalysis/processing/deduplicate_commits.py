"""Deduplicate commits for a repo."""

import pandas as pd


def deduplicate_commits(commits):
    """
    Remove non-unique commits for repository

    Currently `commits` should exist (ie run githubanalysis/processing/get_all_branches_commits() first).
    """

    assert isinstance(
        commits, pd.DataFrame
    ), "Input 'commits' is not a pandas dataframe."

    unique_commits = commits.drop_duplicates(
        subset="sha"
    )  # use commit hash as unique key

    return unique_commits
