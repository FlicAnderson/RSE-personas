"""Inclusion/Exclusion workflow to create test set for GitHub repo analysis."""

import sys
import random
import seaborn as sns
import seaborn.objects as so

import pandas as pd

import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.setup_github_auth as ghauth

import githubanalysis.processing.get_repo_creation_date as createdate


def main():
    """
    Workflow to process and check input data (csv of github repo URLs),
    summarise repo stats, and check eligibility of each repo for coding-smart
    study.
    Workflow outputs eligible repos to csv file.
    :return: study_repos: a csv file of eligible repo urls or names.
    """

    # read in csv file of repo urls

    # count input repo urls

    # for each repo:
        # summarise stats using: summarise_repo_stats(repo_name):

            # count number of devs

            # count number of commits

            # count closed issue tickets

            # get date of last commit

            # get age of repo

            # get license type

            # is repo accessible?

            # does repo contain code
            # repo languages include: python, (C, C++), (shell?, R?, FORTRAN?)

            # ? repo architecture?


        # check eligibility of each repo using: check_repo_eligibility(repo_name)

        # collate eligible repos, discard ineligible ones.

    # count eligible repos total

    # output eligible repos
