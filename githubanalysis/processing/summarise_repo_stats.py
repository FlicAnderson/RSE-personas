""" Summarise key stats for GitHub repository."""

import sys
import pandas as pd
import datetime
from datetime import datetime
from datetime import timezone
import requests
from requests.adapters import HTTPAdapter, Retry

import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.get_repo_connection as ghconnect
import githubanalysis.processing.get_all_pages_issues as getallissues
import githubanalysis.analysis.calc_days_since_repo_creation as dayssince


def summarise_repo_stats(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Connect to given GitHub repository and get details
    when given 'username' and 'repo_name' repository name.
    Results are of type dict, containing keys for each stat.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default = 'githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default = 100, overwrites GitHub default 30.
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

    # count number of devs (contributors; including anonymous contribs* )

    contribs_url = f"https://api.github.com/repos/{repo_name}/contributors?per_page=1&anon=1"

    api_response = requests.get(contribs_url)

    total_contributors = None

    if api_response.ok:
        contrib_links = api_response.links
        contrib_links_last = contrib_links['last']['url'].split("&page=")[1]
        total_contributors = int(contrib_links_last)

        if total_contributors >= 500:
            raise Warning(f"Repo {repo_name} has over 500 contributors, so API may not return contributors numbers accurately.")
        # * NOTE: gh API does NOT return username info where number of contributors is > 500;
        #  ... after this they're listed as anonymous contributors.
        #  ... It's NOT possible to get the number of contributors GH web page returns using API info.
        # source: https://docs.github.com/en/free-pro-team@latest/rest/repos/repos?apiVersion=2022-11-28#list-repository-contributors
            # > "GitHub identifies contributors by author email address.
            # > This endpoint groups contribution counts by GitHub user, which includes all associated email addresses.
            # > To improve performance, only the first 500 author email addresses in the repository link to GitHub users.
            # > The rest will appear as anonymous contributors without associated GitHub user information."

    repo_stats.update({"devs": total_contributors})



    # count total number of commits

    base_commits_url = f"https://api.github.com/repos/{repo_name}/commits?per_page=1"

    api_response = requests.get(base_commits_url)
    commit_links = api_response.links
    commit_links_last = commit_links['last']['url'].split("&page=")[1]
    total_commits = int(commit_links_last)


    repo_stats.update({"total_commits": total_commits})


    # count total commits in last year

    base_commit_stats_url = f"https://api.github.com/repos/{repo_name}/stats/commit_activity"

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    api_response = s.get(url=base_commit_stats_url, timeout=10)
    print(api_response)

    total_commits_1_year = pd.DataFrame(api_response.json())['total'].sum()
    repo_stats.update({"total_commits_last_year": total_commits_1_year})


    # date of most recently updated PR:
    per_pg = 1
    state = 'all'
    sort = 'udpated'
    direction = 'desc'
    params_string = f"?per_pg={per_pg}&state={state}&sort={sort}&direction={direction}"

    PRs_url = f"https://api.github.com/repos/{repo_name}/pulls{params_string}"

    api_response = requests.get(PRs_url)

    PRs_bool = None
    last_PR_updated = None

    if api_response.ok:
        print(api_response.ok)

        try:
            assert len(api_response.json()) != 0, "No json therefore no PRs"
            last_PR_update = api_response.json()[0]['updated_at']  # 0th(1st) for latest update as sorted desc.
            date_format = '%Y-%m-%dT%H:%M:%S%z'
            last_PR_updated = datetime.strptime(last_PR_update, date_format)
            # as datetime w/ UTC timezone awareness(last_PR_update)
            PRs_bool = True
        except:
            PRs_bool = False
            last_PR_updated = None
    else:
        api_response.raise_for_status()

    repo_stats.update({"has_PRs": PRs_bool})
    repo_stats.update({"last_PR_update": last_PR_updated})



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


    # get age of repo
    repo_age_days = dayssince.calc_days_since_repo_creation(
        datetime.now(timezone.utc).replace(tzinfo=timezone.utc),
        repo_name,
        since_date=None,
        return_in='whole_days',
        config_path=config_path
    )
    repo_stats.update({"repo_age_days": repo_age_days})


    # get license type
    license_type = repo_con.get_license().license
    # will be of type: github.License.License

    repo_stats.update({"repo_license": license_type})


    # is repo accessible?

    if hasattr(repo_con, 'private') is True:
        repo_visibility = False
    else:
        repo_visibility = True
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
    #     "total_commits_last_year": 0,
    #     "tickets": 0,
    #     "last_commit": "datetype",
    #     "repo_age_days": 0,
    #     "repo_license": "license",
    #     "repo_visibility": "visible",
    #     "repo_language": "python"
    # }

    # check ALL keys in repo_stats dict:
    #try: all x in repo_stats = TRUE


    if verbose:
        print(f"Stats for {repo_name}: {repo_stats}")

    return repo_stats

    # except: something's wrong.


def main():
    """
    Run summarise_repo_stats() from terminal on supplied repo name.
    """

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    else:
        raise IndexError('Please enter a repo_name.')

    if 'github' in repo_name:
        repo_name = name_clean.repo_name_clean(repo_name)

    # run summarise_repo_stats() on repo_name.
    summarise_repo_stats(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True)


# this bit
if __name__ == "__main__":
    main()