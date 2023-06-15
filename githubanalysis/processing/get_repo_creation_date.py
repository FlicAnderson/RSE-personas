""" Set up GitHub API connection for given GitHub repository."""
import pandas as pd
from pandas import DatetimeIndex

import githubanalysis.processing.get_repo_connection as ghconn

def get_repo_creation_date(repo_name, config_path='githubanalysis/config.cfg', verbose=True):
    """
    Get creation date of GitHub repo using get_repo_connection().
    Use for plotting and analysis.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :returns: repo_creation_date
    :type: datetime.datetime

    Examples:
    ----------
    >>> get_repo_creation_date('riboviz/riboviz', config_path='githubanalysis/config.cfg', verbose=True)
    GH link opened
    Creation date of repo riboviz/riboviz is 2019 5 3.
    Timestamp('2019-05-03 12:15:59+0000', tz='UTC')
    """

    # set up connection
    repo_conn = ghconn.get_repo_connection(repo_name=repo_name, config_path=config_path)

    # get creation date:
    repo_creation_date = pd.to_datetime(repo_conn.created_at)
    repo_creation_date = repo_creation_date.tz_localize(tz='UTC')  # created_at date is UTC but returns as tz naive

    if verbose:
        print(f'Creation date of repo {repo_name} is {repo_creation_date.year} {repo_creation_date.month} {repo_creation_date.day}.')

    return repo_creation_date
