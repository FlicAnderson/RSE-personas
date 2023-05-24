""" Get all data from all pages of issues for a github repo."""

import requests


def get_all_pages_issues(repo_name):
    """
    Obtains all fields of data from all pages for a given github repo `repo_name`.
    :param ???: cleaned `repo_name` string without github url root or trailing slashes.
    :type str:
    :returns: `issues_data` dataframe(?or github object?)
    :type ???:

    Examples:
    ----------
    TODO.
    """

    # get_last_page_links a = requests.get(url=f'https://api.github.com/repos/{username}/{repo_name}/issues', params={'per_page': 100}).links