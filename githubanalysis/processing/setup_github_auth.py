""" Set up authenticated access to github."""

import configparser
from pathlib import Path
from github import Github


def setup_github_auth(configfilepath = '../config', per_page=100):
    """
    Authenticates with Github API using user-generated config.cfg file contents; sets per_page to 100 items.
    :param configfilepath: file path of config.cfg file. Default='../config'.
    :type str:
    :param per_page: number of items per page. Default=100, overwrites Github default 30.
    :type int:
    :returns: `ghlink`
    :type github.MainClass.Github:

    Examples:
    ----------
    TODO.
    """

    # ensure arguments are valid
    if per_page > 100:
        raise ValueError('GH API maximum per_page value is 100.')

    # check config filepath input (using separate variable to avoid overwriting it as pathlib Path type)
    pathchecker = Path(configfilepath)
    if pathchecker.exists() == False:
        raise OSError('Config file does not exist at that path.')

    # read config file and pull out access token details
    config = configparser.ConfigParser()
    config.read(configfilepath)
    config.sections()
    access_token = config['ACCESS']['token']

    try:
        ghlink = Github(
            access_token,
            per_page=per_page
        )  # type(ghlink) is github.MainClass.Github; ghlink.per_page should return 100

        print('GH link opened')
        return ghlink

    except RuntimeError:
        print('Github authentication did not work. Check config file has correct format locally and has correct permissions in your github account.')