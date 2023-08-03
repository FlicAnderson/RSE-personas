""" Function to get contributor commit stats data for a GitHub repo."""

import pandas as pd
import requests


def get_contributor_commits_stats(repo_name, verbose=True):
    """
    Takes repo name, creates new dataframe of contributor commit activity (pd.DataFrame object) for that repository.
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param verbose: print status info? Default= true
    :type: bool
    :return contributor_commits_stats: dataframe with release info including dates and versions if found for the repo.
    :type: pd.DataFrame

    This returns statistics on contributor stats, rather than returning ALL commits for contributors.
    """

    # handle API responses:
    base_contributor_stats_url = f"https://api.github.com/repos/{repo_name}/stats/contributors"
    api_response = requests.get(url=base_contributor_stats_url)

    if api_response.status_code == 200 and verbose:
        print(f'API response status "OK": {api_response}')

    elif api_response.status_code == 202 and verbose:
        print(f'API response status "Accepted": {api_response}. Data not yet been cached, will retry request shortly.')
        # WAIT THEN RETRY REQUEST! Based on GH API docs: https://docs.github.com/en/rest/metrics/statistics?apiVersion=2022-11-28#best-practices-for-caching

    elif api_response.status_code == 204 and verbose:
        print(f'API response status "A header with no content is returned": {api_response}')

    else:
        print(f'Something else is wrong; API response: {api_response}')