""" Set up authenticated access to github."""

import configparser
from github import Github


def setup_github_auth():
    """
    Authenticates with Github API using user-generated config.cfg file contents; sets per_page to 100 items.

    :returns: `ghlink`
    :type github.MainClass.Github:

    Examples:
    ----------
    TODO.
    """

    # set up github access token with github package:
    config = configparser.ConfigParser()
    config.read('../config.cfg')
    config.sections()

    access_token = config['ACCESS']['token']

    try:
        ghlink = Github(
            access_token,
            per_page=100
        )  # type(ghlink) is github.MainClass.Github; ghlink.per_page should return 100

        return ghlink

    except RuntimeError:
        print('Github authentication did not work. Check config file has correct format locally and has correct permissions in your github account.')