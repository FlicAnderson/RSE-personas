"""Set up authenticated access to GitHub."""

import configparser
import os


def setup_github_auth(config_path="githubanalysis/config.cfg") -> str:
    """
    Authenticates with Github API using user-generated config.cfg file contents
    :param config_path: file path of config.cfg file. Default='githubanalysis/config.cfg'.
    :type: str
    :returns: accesstoken
    :rtype: str
    """

    # check config filepath input (using separate variable to avoid overwriting it as pathlib Path type)
    if not os.path.exists(config_path):
        raise RuntimeError("Config file does not exist at path:", config_path)
    try:
        # read config file and pull out access token details
        config = configparser.ConfigParser()
        config.read(config_path)
        return config["ACCESS"]["token"]
    except:
        raise RuntimeError(
            "Github authentication failed. Check config file format and permissions in your github account."
        )
