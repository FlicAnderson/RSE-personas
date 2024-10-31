"""Set up authenticated access to Zenodo API."""

import configparser
import os


def setup_zenodo_auth(config_path: str = "zenodocode/zenodoconfig.cfg") -> str:
    """
    Authenticates with Zenodo API using user-generated zenodoconfig.cfg file contents.

    :param config_path: file path of config.cfg file. Default='zenodocode/zenodoconfig.cfg'.
    :type: str
    :returns: zenodo config token string
    :rtype: str

    """

    if not os.path.exists(config_path):
        raise RuntimeError("Config file does not exist at path:", config_path)
    try:
        # read config file and pull out access token details
        config = configparser.ConfigParser()
        config.read(config_path)
        return config["ACCESS"]["token"]
    except:
        raise RuntimeError(
            "Zenodo authentication failed. Check config file format and permissions in your zenodo account."
        )
