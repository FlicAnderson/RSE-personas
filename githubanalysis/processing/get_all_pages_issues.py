""" Get all data from all pages of issues for a github repo."""
import pandas as pd
import requests


def get_all_pages_issues(repo_name, per_pg=100):
    """
    Obtains all fields of data from all pages for a given github repo `repo_name`.
    :param ???: cleaned `repo_name` string without github url root or trailing slashes.
    :type str:
    :returns: `issues_data` dataframe(?or github object?)
    :type ???:

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

    urlparam = f"https://api.github.com/repos/{repo_name}/issues"

    links = requests.get(url=urlparam, params={'per_page' : per_pg}).links

    # ERROR if there's no 'last'. In this case, just take
    # figure out how many pages there are.
    last_pg = links['last']['url'].split("&page=")[1] # pull off the number of last page
    # last_pg should be number (convert from returned string I guess?)

    # pull json for ALL pages
    pg_url = links['last']['url'].split("&page=")[0] # pull out the part before pagenumber

    store_pgs = []

    for i in range(int(last_pg)):  # starts at 0
        url_num = i + 1
        # print(i+1) # 1, 2 for i in range(last_pg = 2)
        tmp_pg_results = requests.get(f"{pg_url}&page={url_num}").json()
        # counter = i
        if i == 0:
            print("first run", url_num, ":", len(tmp_pg_results), type(tmp_pg_results))
            store_pgs.extend(tmp_pg_results)  # for first set, create store_pgs
        else:
            print("subsequent", url_num, ":", len(tmp_pg_results), type(tmp_pg_results))
            store_pgs.extend(tmp_pg_results)  # for subsequent sets, extend (add to) store_pgs

    # store_pgs holds items in list.
      # Can pull items out using indices e.g. url of 'first' issue: store_pgs[0]['url']

    print("Total responses:", len(store_pgs))

    issue_pgs_df = pd.DataFrame(store_pgs)
    return (issue_pgs_df)

    # relevant fields: 'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
    # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url', 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)

    # todo: add optional informative message about how many issues, pages etc?
