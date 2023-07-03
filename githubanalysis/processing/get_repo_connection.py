""" Set up GitHub API connection for given GitHub repository."""

import githubanalysis.processing.setup_github_auth as ghauth


def get_repo_connection(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Create connection to GitHub repository and get details
    when given 'username' and 'repo_name' repository name.
    repo_connection is type: GitHub.Repository.Repository.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: `repo_connection` GitHub object repository connection
    :type: GitHub.Repository.Repository

    Examples:
    ----------
    >>> get_repo_connection('riboviz/riboviz')
    Repository(full_name="riboviz/riboviz")
    """

    # this access token authentication setup line is required; use defaults `config_path` & `per_pg`=100
    ghlink = ghauth.setup_github_auth(config_path, per_pg, verbose=verbose)

    # TODO: check repo_name input validity

    # try to set up connection
    repo_connection = ghlink.get_repo(repo_name)

    return repo_connection
