""" Set up Github API connection for given github repository."""

from github import Github
# todo NEEDS set up access token separately (see above!)

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

    # g = Github(access_token)  # this access token setup line is required, plus extra setup code elsewhere above.

    # check input

    # try to set up connection
    repo_connection = g.get_repo(repo_name)

    return repo_connection