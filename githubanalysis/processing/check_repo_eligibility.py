""" Checks whether given GitHub repository is eligible for analysis."""

import githubanalysis.processing.setup_github_auth as ghauth


def check_repo_eligibility(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Checks whether given GitHub repository meets eligibility
    criteria for analysis in coding-smart study when given
    'username' and 'repo_name' repository name. Returns bool.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: repo_eligible
    :type: bool

    Examples:
    ----------
    >>> check_repo_eligibility('riboviz/riboviz')
    TODO
    """
