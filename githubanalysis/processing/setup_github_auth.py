""" Set up authenticated access to GitHub."""

import configparser
from pathlib import Path
from github import Github


def setup_github_auth(config_path='githubanalysis/config.cfg', verbose=True):
    """
    Authenticates with Github API using user-generated config.cfg file contents; sets per_page to 100 items.
    :param config_path: file path of config.cfg file. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: `ghlink`
    :type: github.MainClass.Github

    # NB: GitHub API param uses 'per_page', Flic's code using 'per_pg' intentionally.

    Examples:
    ----------
    TODO.
    """

    # check config filepath input (using separate variable to avoid overwriting it as pathlib Path type)
    pathchecker = Path(config_path)
    if pathchecker.exists() is False:
        raise OSError('Config file does not exist at path:', config_path)

    # read config file and pull out access token details
    config = configparser.ConfigParser()
    config.read(config_path)
    config.sections()
    try:
        access_token = config['ACCESS']['token']
    except:
        raise KeyError('Config file access token info not correct somehow.')

    try:
        ghlink = Github(
            access_token,
        )  # type(ghlink) is github.MainClass.Github; ghlink.per_page should return 100
        return(access_token)
    
    except RuntimeError:
        print('Github authentication failed. Check config file format and permissions in your github account.')
