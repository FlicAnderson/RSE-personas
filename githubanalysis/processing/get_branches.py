"""Function to retrieve and return branches info for a given GitHub repository."""

import pandas as pd
import requests
from requests.adapters import HTTPAdapter, Retry

import githubanalysis.processing.setup_github_auth as ghauth


# class BranchesGetter:

#     #     # if not given a better option, use my default settings for logging
#     # logger: logging.Logger
#     # def __init__(self, logger: logging.Logger = None) -> None:
#     #     if logger is None:
#     #         self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/get_branches_logs.txt')
#     #     else:
#     #         self.logger = logger


def get_branches(repo_name, config_path="githubanalysis/config.cfg", per_pg=100):
    """
    Get branch info for given repo repo_name and return it.

    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
    :type: int
    :return: `branches` pd.DataFrame for repo `repo_name`.
    :type: DataFrame

    """

    repos_api_url = "https://api.github.com/repos/"
    api_call = f"{repos_api_url}{repo_name}/branches"

    gh_token = ghauth.setup_github_auth(config_path=config_path)
    headers = {"Authorization": "token " + gh_token}

    s = requests.Session()
    retries = Retry(
        total=10,
        connect=5,
        read=3,
        backoff_factor=1.5,
        status_forcelist=[202, 502, 503, 504],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))

    # assemble API call
    api_response = s.get(url=api_call, headers=headers)
    api_response.status_code

    assert (
        api_response.status_code != 401
    ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {api_call} is {api_response}"
    # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

    branches = pd.DataFrame.from_dict(api_response.json())
    branches["branch_sha"] = pd.DataFrame.from_dict(branches["commit"]).apply(
        lambda x: [x.get("sha") for x in x]
    )  # pull sha out of commit field as separate field

    return branches
