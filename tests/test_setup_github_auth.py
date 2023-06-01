""" Test github auth setup function """

import pytest
from pathlib import Path
from githubanalysis.processing import setup_github_auth

def test_config_file_not_exists():
    # test config file exists where expected
    fake_config_path = 'githubanalysis/fakefolder/config.cfg'

    with pytest.raises(OSError):
        setup_github_auth.setup_github_auth(config_path=fake_config_path)

#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_config_file_format():
    # should test what happens if the file doesn't have correct format (e.g. heading not [ACCESS]?)
    # should get KeyError if the file is located correctly but incorrect format.

#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_config_file_GH_invalid():
    # should test what happens if the file doesn't contain GH-approved-valid access token.
    # should get RuntimeError if the file is located correctly and correct format but it's not a valid GH one.
    # could create text file in correct format and 'generate' incorrect hash. ?? might cause blocking tho - check GH API guidance ??

@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_per_pg_25():
    # test per_pg attribute value changes with user input as expected

    ghlink = setup_github_auth.setup_github_auth(per_pg=25)  # not using per_pg defaults from the function

    assert ghlink.per_page == 25

@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_per_pg_default100():
    # test per_pg attribute value is set to 100 as expected (default defined as 100 in setup_github_auth)

    ghlink = setup_github_auth.setup_github_auth()  # not using per_pg defaults from the function

    assert ghlink.per_page == 100   # NB: GitHub API param uses 'per_page', Flic's code using 'per_pg' intentionally.


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_per_pg_exceed100():
    # test per_pg attribute value max is 100 in GH API, so don't accept this!

    with pytest.raises(ValueError):
        setup_github_auth.setup_github_auth(per_pg=150)



#def test_ghlink_class:
    # test that ghlink has right class ? github.MainClass.Github