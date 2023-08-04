""" Function to get contributor commit stats data for a GitHub repo."""

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry
import logging



def get_contributor_commits_stats(repo_name, verbose=True):
    """
    Takes repo name, creates new dataframe of total contributor commit activity (pd.DataFrame object) for the repository.
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param verbose: print status info? Default= true
    :type: bool
    :return contributor_commits_stats: dataframe with release info including dates and versions if found for the repo.
    :type: pd.DataFrame

    This returns statistics on contributor stats, rather than returning ALL commits for contributors.
    See more at the GH API docs: https://docs.github.com/en/rest/metrics/statistics?apiVersion=2022-11-28#get-all-contributor-commit-activity
    """

    # handle API responses:
    base_contributor_stats_url = f"https://api.github.com/repos/{repo_name}/stats/contributors"
    # approach via: https://stackoverflow.com/a/35636367

    #if verbose:
    #    logging.basicConfig(level=logging.DEBUG)  # might be able to remove this as it doesn't affect the requests code

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    api_response = s.get(url=base_contributor_stats_url, timeout=10)

    if api_response.status_code == 200 and verbose:
        print(f'API response status "OK": {api_response}')

        try:
            # pull data as json then convert to pandas dataframe for ease of use
            contributor_stats_info = api_response.json()
            contributor_commits_stats = pd.DataFrame.from_dict(contributor_stats_info)

            if verbose:
                print(contributor_commits_stats.shape)

            if len(contributor_commits_stats.columns) == 0:
                raise Exception(f"Repo {repo_name} contains NO contributor stats.")

            # pull author username out from rest of author data
            contributor_commits_stats['contributor_author'] = contributor_commits_stats[['author']].apply(
                lambda x: [x.get('login') for x in x])

            contributor_commits_stats['repo_name'] = repo_name

            contributor_commits_stats = contributor_commits_stats.sort_values(by='total', axis=0, ascending=False)

            return contributor_commits_stats

        except:
            print("No contributor stats found")
            contributor_commits_stats = pd.DataFrame()
            return contributor_commits_stats

    elif api_response.status_code == 202 and verbose:
        print(f'API response status "Accepted": {api_response}. Data not yet been cached, need to retry request shortly.')
        # Wait further, then retry...
        print('Retrying same function recursively; this could go infinitely wrong... Cancel if uncertain tbh!')
        get_contributor_commits_stats(repo_name, verbose=True)


    elif api_response.status_code == 204 and verbose:
        print(f'API response status "A header with no content is returned": {api_response}')
        contributor_commits_stats = pd.DataFrame()
        return contributor_commits_stats

    else:
        print(f'Something else is wrong; API response: {api_response}')
        contributor_commits_stats = pd.DataFrame()
        return contributor_commits_stats