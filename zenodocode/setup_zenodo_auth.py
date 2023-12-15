""" Set up authenticated access to Zenodo API."""

import configparser
import requests
from pathlib import Path

def setup_zenodo_auth(config_path='zenodocode/zenodoconfig.cfg', verbose=True):
    """
    Authenticates with Zenodo API using user-generated zenodoconfig.cfg file contents.

    :param config_path: file path of config.cfg file. Default='zenodocode/zenodoconfig.cfg'.
    :type: str
    :param verbose: return status info. Default: True
    :type: bool
    :returns: zenodo_response
    :type: requests.models.Response

    Examples:
    ----------
    TODO.
    """

    # check config filepath input (using separate variable to avoid overwriting it as pathlib Path type)
    pathchecker = Path(config_path)
    if pathchecker.exists() is False:
        raise OSError(f"Config file does not exist at path: {config_path} from current location {Path(__file__).resolve().parent}")

    # read config file and pull out access token details
    config = configparser.ConfigParser()
    config.read(config_path)
    config.sections()

    try:
        access_token = config['ACCESS']['token']
    except:
        raise KeyError('Config file access token info not correct somehow.')

    try:
        zenodo_response = requests.get(
            url='https://zenodo.org/api/deposit/depositions',
            params={'access_token': access_token}
        )  # type(zenodo_response) should be requests.models.Response

        assert zenodo_response.status_code == requests.codes.ok
        zenodo_response.raise_for_status()

        if verbose:
            print('Zenodo API request OK')

        return zenodo_response, access_token

    except RuntimeError:
        print('Zenodo authentication failed. Check config file format and permissions in your zenodo account.')
