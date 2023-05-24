""" Test github auth setup function """

import pytest
from pathlib import Path
from githubanalysis.processing import setup_github_auth

def test_config_file_not_exists():
    # test config file exists where expected
    # NOTE: this function doesn't actually touch any of the setup_github_auth.py code
    fakeconfigfilepath = 'githubanalysis/fakefolder/config.cfg'

    with pytest.raises(OSError):
        setup_github_auth.setup_github_auth(configfilepath=fakeconfigfilepath)


# def test_config_file_format():
    # should test what happens if the file doesn't have correct format (e.g. heading not [ACCESS]?)
    # should get KeyError if the file is located correctly but incorrect format.


# def test_config_file_GH_invalid():
    # should test what happens if the file doesn't contain GH-approved-valid access token.
    # should get RuntimeError if the file is located correctly and correct format but it's not a valid GH one.
    # could create text file in correct format and 'generate' incorrect hash. ?? might cause blocking tho - check GH API guidance ??

def test_per_page_25():
    # test per_page attribute value changes with user input as expected

    ghlink = setup_github_auth.setup_github_auth(per_page=25)  # not using per_page defaults from the function

    assert ghlink.per_page == 25


def test_per_page_default100():
    # test per_page attribute value is set to 100 as expected (default defined as 100 in setup_github_auth)

    ghlink = setup_github_auth.setup_github_auth()  # not using per_page defaults from the function

    assert ghlink.per_page == 100



#def test_ghlink_class:
    # test that ghlink has right class ? github.MainClass.Github