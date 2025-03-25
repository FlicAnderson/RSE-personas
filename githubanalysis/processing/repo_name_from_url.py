"""Cleaning github repository names and urls of github repos."""

from urllib import parse
from pathlib import Path


def repo_name_from_url(repo_url: str) -> str | None:
    """
    Remove trailing slashes and github url root from string repo names.
    Returns string composed of gh_user or organisation / repository name if valid;
    Returns None if repository url is not validly composed.
    :param repo_url: repository names in url format or as 'username/repo_name' format.
    :type str:
    :returns: `repo_name` string without github url root or trailing slashes, or None.
    :type str | None:

    Examples:
    ----------
    # from within python:
    >>> repo_name_from_url("https://github.com/riboviz/riboviz")
    'riboviz/riboviz'

    >>> repo_name_from_url("https://github.com/FlicAnderson/20230215-JournalClub-BestPractices/")
    'FlicAnderson/20230215-JournalClub-BestPractices'
    """

    # putting type check here in 'if not' format reduces subsequent indentation
    # by raising error and breaking out otherwise

    if not isinstance(repo_url, str):
        raise TypeError(
            "Ensure input url is a string. If list of repos, use list comprension e.g. `[repo_name_from_url(x) for x in repo_list]`."
            + f"Received type {type(repo_url)}"
        )

    # do repo url extraction
    parsed_url = parse.urlparse(repo_url)
    parsed_path = Path(parsed_url.path)
    path_components = parsed_path.parts[:3]
    if len(path_components) != 3:
        return None
    else:
        # join elements with slashes, remove .git if that's present in url, remove front slashes (and trailing if present)
        return "/".join(path_components).removesuffix(".git").strip("/")
