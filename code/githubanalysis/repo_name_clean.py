"""Cleaning github repository names and urls of github repos."""

import sys

def repo_name_clean(repo_url):
    """
    Remove trailing slashes and github url root from string repo names.
    :param repo_url: repository names in url format or as 'username/repo_name' format.
    :type str:
    :returns: `repo_name` string without github url root or trailing slashes.
    :type str:

    Examples:
    ----------

    >>> repo_name_clean("https://github.com/riboviz/riboviz")
    'riboviz/riboviz'

    >>> repo_name_clean("https://github.com/FlicAnderson/20230215-JournalClub-BestPractices/")
    'FlicAnderson/20230215-JournalClub-BestPractices'

    """

# TODO: change non-string input -> TypeErrors

# TODO: is it worth setting a default value for testing? e.g. repo_url = 'https://github.com/testperson/testrepo'
# TODO: how can I handle commandline input? e.g. sys.argv[1]/[1:]

    if isinstance(repo_url, list):
        assert isinstance(repo_url,
                          str), 'Ensure input url is a string. If list of repos, use list comprension e.g. `[repo_name_clean(x) for x in repo_list]`.'

    if isinstance(repo_url, str):

        if "," in repo_url:
            raise ValueError('Input contains commas - ensure input is string of ONE repo only.')
        if ";" in repo_url:
            raise ValueError('Input contains semicolons - ensure input is string of ONE repo only.')

        try:
            repo_url = (repo_url.split("https://github.com/"))[1]
            repo_name = (repo_url.rstrip("/"))

        except ValueError:
            print(
                f"Could not clean repo_url into username/repo_name format. Confirm input is correct (and if url is given that it starts 'https://github.com/').")

        print(repo_name)
        return repo_name





