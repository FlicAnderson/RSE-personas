""" Set up Github API connection for given github repository."""

from github import Github
import githubanalysis.processing.setup_github_auth as ghauth

def get_repo_connection(repo_name):
    """Create connection to github repository and get details
    when given 'username' and 'repo_name' repository name.
    repo_connection is type: github.Repository.Repository.

    NOTE: Requires `access_token` setup with Github package.

    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type str:
    :returns: `repo_connection` github object repository connection
    :type github.Repository.Repository:

    Examples:
    ----------
    >>> get_repo_connection('riboviz/riboviz')
    Repository(full_name="riboviz/riboviz")
    """

    # this access token authentication setup line is required; use defaults configfilepath & per_page=100
    ghlink = ghauth.setup_github_auth()

    # check repo_name input validity

    # try to set up connection
    repo_connection = ghlink.get_repo(repo_name)

    return repo_connection