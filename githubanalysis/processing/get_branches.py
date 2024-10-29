"""Function to retrieve and return branches info for a given GitHub repository."""

import requests
from requests.adapters import HTTPAdapter, Retry

import githubanalysis.processing.setup_github_auth as ghauth
from utilities.check_gh_reponse import (
    run_with_retries,
    raise_if_response_error,
)
import utilities.get_default_logger as loggit


logger = loggit.get_default_logger(
    console=True,
    set_level_to="DEBUG",
    log_name="logs/get_branches_logs.txt",
    in_notebook=False,
)


def get_branch_shas(
    repo_name, config_path="githubanalysis/config.cfg", per_pg=100
) -> set[str]:
    """
    Get branch info for given repo repo_name and return it.

    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
    :type: int
    :return: Branch hashes in a set for repo `repo_name`.
    :rtype: set of strings

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
        backoff_factor=1,
        status_forcelist=[202, 502, 503, 504],
    )
    s.mount("https://", HTTPAdapter(max_retries=retries))

    # assemble API call
    api_response = run_with_retries(
        fn=lambda: raise_if_response_error(
            api_response=s.get(url=api_call, headers=headers),
            repo_name=repo_name,
            logger=logger,
        ),
        logger=logger,
    )

    assert (
        api_response.status_code != 401
    ), f"WARNING! The API response code is 401: Unauthorised. Check your GitHub Personal Access Token is not expired. API Response for query {api_call} is {api_response}"
    # assertion check on 401 only as unauthorise is more likely to stop whole run than 404 which may apply to given repo only

    assert (
        api_response.status_code == 200
    ), f"WARNING! API Response code is NOT 200 ({api_response.status_code}). Cannot proceed with data gathering for get_branches()."

    branches: list = api_response.json()
    # pull sha out of commit field as separate field

    return {branch["commit"]["sha"] for branch in branches}
    # this is returned as a set for deduplication purposes to avoid
    # multiple API calls for branches with matching SHAs!
