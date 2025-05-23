"""Set up GitHub API connection for given GitHub repository."""

import pandas as pd

import githubanalysis.processing.get_repo_connection as ghconnect


def get_repo_creation_date(
    repo_name, config_path="githubanalysis/config.cfg", verbose=True
):
    """
    Get creation date of GitHub repo using get_repo_connection().
    Use for plotting and analysis.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param verbose: return status info. Default: True
    :type: bool
    :returns: repo_creation_date
    :type: datetime.datetime

    Examples:
    ----------
    >>> get_repo_creation_date('riboviz/riboviz', config_path='githubanalysis/config.cfg', verbose=True)
    GH link opened
    Creation date of repo riboviz/riboviz is 2019 5 3.
    Timestamp('2019-05-03 12:15:59+0000', tz='UTC')
    """
    # connect to repos api for reponame
    api_response = ghconnect.get_repo_connection(
        repo_name=repo_name, config_path=config_path
    )
    api_response_json = api_response.json()
    # print(api_response.url)

    # get creation date:
    repo_creation_date = pd.to_datetime(api_response_json.get("created_at"))  # type: pandas._libs.tslibs.timestamps.Timestamp
    repo_creation_date = repo_creation_date.tz_convert(
        "UTC"
    )  # created_at date now 'intelligently' utc

    if verbose:
        print(
            f"Creation date of repo {repo_name} is {repo_creation_date.year} {repo_creation_date.month} {repo_creation_date.day}."
        )

    return repo_creation_date
