"""Set up GitHub API connection for given GitHub repository."""

import requests

import githubanalysis.processing.setup_github_auth as ghauth


def get_repo_connection(repo_name, config_path):
    """
    Create connection to GitHub repository and get details
    when given 'username' and 'repo_name' repository name.

    To get json content, run `.json()` on this function's output.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param verbose: return status info. Default: True
    :type: bool
    :returns: `api_response`
    :type: requests.models.Response

    Examples:
    ----------

    """

    # auth setup
    gh_token = ghauth.setup_github_auth(config_path=config_path)
    headers = {"Authorization": "token " + gh_token}

    # get repo api response
    base_repo_url = "https://api.github.com/repos"
    connect_to = f"{base_repo_url}/{repo_name}"

    api_response = requests.get(url=connect_to, headers=headers)

    return api_response
