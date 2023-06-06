""" Get all data from all pages of issues for a GitHub repo."""
import pandas as pd
import githubanalysis.processing.get_repo_connection as ghconnect


def get_all_pages_issues(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, issue_state='all', verbose=True):
    """
    Obtains all fields of data from all pages for a given github repo `repo_name`.
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param issue_state: one of 'open', 'closed' or 'all'. GitHub issue API status options. Default: 'all'
    :type: str
    :param verbose: whether to print out issue data dimensions and counts. Default: True
    :type: bool
    :returns: `all_issues` pd.DataFrame containing 30 fields per issue for given repo `repo_name`.
    :type: DataFrame

    Examples:
    ----------
    TODO.
    """

    repo_con = ghconnect.get_repo_connection(repo_name, config_path, per_pg)  # create gh repo object to given repo
    # contains:  #ghlink = ghauth.setup_github_auth() with config path default to '../config' & per_page=100

    if hasattr(repo_con, 'has_issues') is False:
        raise AttributeError(f'GitHub repository {repo_name} does not have issues enabled.')

    store_pgs = []

    # without `state='all'` you only get open issues.
    for page in repo_con.get_issues(state=issue_state):
        store_pgs.append(page._rawData)
        # this is currently 'access to a protected member _rawData of a class'... :s

    # store_pgs holds items in list.
        # Can pull items out using indices e.g. url of 'first' issue: store_pgs[0]['url']

    if verbose:
        print("Total responses:", len(store_pgs))

    all_issues = pd.DataFrame(store_pgs)

    if verbose:
        print("Shape of data:", all_issues.shape)
        print("Issue state counts:", all_issues.state.value_counts())

    # check all important columns are present in the df.
    wanted_cols = ['url', 'repository_url', 'labels', 'number', 'title', 'state',
                   'assignee', 'assignees', 'created_at', 'closed_at', 'pull_request']
    assert all(item in all_issues.columns for item in wanted_cols)

    all_issues['created_at'] = pd.to_datetime(all_issues['created_at'], yearfirst=True, utc=True,
                                                 format='%Y-%m-%dT%H:%M:%S%Z')
    all_issues['closed_at'] = pd.to_datetime(all_issues['closed_at'], yearfirst=True, utc=True,
                                                format='%Y-%m-%dT%H:%M:%S%Z')

    return all_issues

    # relevant fields: 'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
    # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url',
    # ... 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)

    # todo: add optional informative message about how many issues, pages etc?
