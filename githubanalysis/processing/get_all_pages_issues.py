""" Get all data from all pages of issues for a github repo."""
import pandas as pd
import githubanalysis.processing.get_repo_connection as ghconnect


def get_all_pages_issues(repo_name, per_pg=100, issue_state='all', verbose=True):
    """
    Obtains all fields of data from all pages for a given github repo `repo_name`.
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type str:
    :param per_pg: how many issues per GitHub API page to request. Default: 100
    :type int:
    :param issue_state: one of 'open', 'closed' or 'all'. GitHub issue API status options. Default: 'all'
    :type str:
    :param verbose: whether to print out issue data dimensions and counts. Default: True
    :type bool:
    :returns: `all_issues` pd.DataFrame containing 30 fields per issue for given repo `repo_name`.  
    :type DataFrame:

    Examples:
    ----------
    TODO.
    """

    # use requests.get().links to find number of last page:

    # ?loop through making request for each page with link e.g. for i in maxpgs: requests.get(f'...{repo_name}...page={i}')
        # save out each set of json
        # un-nest/flatten json parts w/ json_normalize?
    # merge the jsons into ONE json (? https://pypi.org/project/jsonmerge/)
    # ensure it returns out as all_issues

    # checking/testing:
        # validate json returned?
        # check json input contains content?
        # check for specific fields being there?
        # check merged json doesn't contain duplicated content (e.g. set i repeated if iterator not reset etc.)


    # # use requests.get().links to find number of last page:

    repo_con = ghconnect.get_repo_connection(repo_name)  # create gh repo object to given repo
    # contains:  #ghlink = ghauth.setup_github_auth() with config path default to '../config' & per_page=100

    store_pgs = []

    # without `state='all'` you only get open issues.
    for page in repo_con.get_issues(state=issue_state):
        store_pgs.append(page._rawData)

    # store_pgs holds items in list.
      # Can pull items out using indices e.g. url of 'first' issue: store_pgs[0]['url']

    if verbose = True:
        print("Total responses:", len(store_pgs))

    all_issues = pd.DataFrame(store_pgs)

    if verbose = True:
        print("Shape of data:", all_issues.shape)
        print("Issue state counts:", all_issues.state.value_counts())

    return (issue_pgs_df)

    # relevant fields: 'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
    # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url', 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)

    # todo: add optional informative message about how many issues, pages etc?
