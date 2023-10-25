""" Summarise key stats for GitHub repository."""

import githubanalysis.processing.setup_github_auth as ghauth



def summarise_repo_stats(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Connect to given GitHub repository and get details
    when given 'username' and 'repo_name' repository name.
    Results are of type TODO.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: TODO
    :type: TODO

    Examples:
    ----------
    >>> summarise_repo_stats('riboviz/riboviz')
    TODO
    """
