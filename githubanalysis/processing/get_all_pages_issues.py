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

    # use requests.get().links to find number of last page:
    # ?loop through making request for each page with link e.g. for i in maxpgs: requests.get(f'...{repo_name}...page={i}')
        # save out each set of json
    # merge the jsons into ONE json (? https://pypi.org/project/jsonmerge/)
    # ensure it returns out as all_issues

    # check json input contains content?
    # check for specific fields being there?
    # check merged json doesn't contain duplicated content (e.g. set i repeated if iterator not reset etc.)

    # get_last_page_links a = requests.get(url=f'https://api.github.com/repos/{username}/{repo_name}/issues', params={'per_page': 100}).links