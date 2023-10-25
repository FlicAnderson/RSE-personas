""" Summarise key stats for GitHub repository."""

import pandas as pd
import datetime
from datetime import timezone

import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.processing.get_repo_connection as ghconnect
import githubanalysis.processing.get_all_pages_issues as getallissues
import githubanalysis.analysis.calc_days_since_repo_creation as dayssince

def summarise_repo_stats(repo_name, config_path='githubanalysis/config.cfg', per_pg = 100, verbose=True):
    """
    Connect to given GitHub repository and get details
    when given 'username' and 'repo_name' repository name.
    Results are of type dict, containing keys for each stat.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: repo_stats: dictionary w/ keys: "repo_name", "devs", "total_commits", "tickets", "last_commit", "repo_age_days",
     ... "repo_license", "repo_visibility", "repo_language".
    :type: dict

    Examples:
    ----------
    >>> summarise_repo_stats(repo_name='riboviz/riboviz', per_pg=100, verbose=True)
    TODO
    """

# create output dict to update with stats:
    repo_stats = {}

# get repo_name gh connection:

    repo_stats.update({"repo_name": repo_name})

    repo_con = ghconnect.get_repo_connection(repo_name, config_path, per_pg)  # create gh repo object to given repo
    # contains:  #ghlink = ghauth.setup_github_auth() with config path default to '../config' & per_page=100

    if hasattr(repo_con, 'has_issues') is False:
        raise AttributeError(f'GitHub repository {repo_name} does not have issues enabled.')


# get stats:

    # count number of devs

    repo_stats.update({"devs": 0})


    # count number of commits

    repo_stats.update({"total_commits": 0})


    # count closed issue tickets

    if hasattr(repo_con, 'has_issues') is True:

        closed_issues = getallissues.get_all_pages_issues(
            repo_name=repo_name,
            config_path='githubanalysis/config.cfg',
            per_pg=100,
            issue_state='closed',
            verbose=True
        )  # get closed issues from all pages for given repo

        closed_issues = closed_issues.shape[0]  # get number; discard df
    else:
        closed_issues = 0
        #raise AttributeError(f'GitHub repository {repo_name} does not have issues enabled.')

    repo_stats.update({"tickets": closed_issues})


    # get date of last commit

    repo_stats.update({"last_commit": "datetype"})


    # get age of repo
    repo_age_days = dayssince.calc_days_since_repo_creation(
        datetime.datetime.now(timezone.utc).replace(tzinfo=timezone.utc),
        repo_name,
        since_date=None,
        return_in='whole_days',
        config_path=config_path
    )
    repo_stats.update({"repo_age_days": repo_age_days})


    # get license type
    license_type = repo_con.get_license().license
    # will be of type: github.License.License
    # TODO: check license type is in list of open licenses.
        # perhaps check for something specific in `repo_con.get_license().license.permissions`?
        # Example: Apache 2: ['commercial-use', 'modifications', 'distribution', 'patent-use', 'private-use']

    repo_stats.update({"repo_license": license_type})


    # is repo accessible?

    if hasattr(repo_con, 'private') is False:
        repo_visibility = True
    else:
        repo_visibility = False
        #raise AttributeError(f'GitHub repository {repo_name} is private.')

    repo_stats.update({"repo_visibility": repo_visibility})


    # does repo contain code
    # repo languages include: python, (C, C++), (shell?, R?, FORTRAN?)
    languages = repo_con.get_languages().keys()

    if 'Python' or 'C' or 'C++' or 'Shell' in languages:
        repo_stats.update({"repo_language": languages})
    else:
        repo_stats.update({"repo_language": "other"})

    # ? repo architecture?
    # ? Not sure how best to check this...


    # return:
    # dict of repo_name stats:
    # repo_stats = {
    #     "repo_name": "repo_name",
    #     "devs": 0,
    #     "total_commits": 0,
    #     "tickets": 0,
    #     "last_commit": "datetype",
    #     "repo_age_days": 0,
    #     "repo_license": "license",
    #     "repo_visibility": "visible",
    #     "repo_language": "python"
    # }

    # check ALL keys in repo_stats dict:
    #try: all x in repo_stats = TRUE

    return repo_stats

    # except: something's wrong.