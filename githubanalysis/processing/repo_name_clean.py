"""Cleaning github repository names and urls of github repos."""

import re


def repo_name_clean(repo_url):
    """
    Remove trailing slashes and github url root from string repo names.
    :param repo_url: repository names in url format or as 'username/repo_name' format.
    :type str:
    :returns: `repo_name` string without github url root or trailing slashes.
    :type str:

    Examples:
    ----------
    # from within python:
    >>> repo_name_clean("https://github.com/riboviz/riboviz")
    'riboviz/riboviz'

    >>> repo_name_clean("https://github.com/FlicAnderson/20230215-JournalClub-BestPractices/")
    'FlicAnderson/20230215-JournalClub-BestPractices'

    # to run from terminal @ coding-smart/code:
    $ python githubanalysis/processing/clean_data.py https://github.com/riboviz/riboviz/
    riboviz/riboviz
    """

    # handle bad input types
    if isinstance(repo_url, list):
        raise TypeError(
            "Ensure input url is a string. If list of repos, use list comprension e.g. `[repo_name_clean(x) for x in repo_list]`."
        )

    if isinstance(repo_url, int):
        raise TypeError("Ensure input url is a string.")

    if isinstance(repo_url, str):
        # if "," in repo_url:
        #     raise ValueError('Input contains commas - ensure input is string of ONE repo only.')
        # if ";" in repo_url:
        #     raise ValueError('Input contains semicolons - ensure input is string of ONE repo only.')

        # do repo url cleaning
        try:
            repo_url = (repo_url.split("https://github.com/"))[1]
            if "tree" in repo_url:
                repo_url = re.split("(^[\.\w-]+\/[\.\w-]+)", repo_url)[1]
            repo_name = repo_url
            return repo_name

        except ValueError:
            print(
                "Could not clean repo_url into username/repo_name format. Confirm input is correct (and if url is given that it starts 'https://github.com/')."
            )
