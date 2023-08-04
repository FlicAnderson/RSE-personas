""" Function to retrieve ALL commits for a given GitHub repository. """

import pandas as pd
import githubanalysis.processing.get_repo_connection as ghconnect

def get_all_pages_commits(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Obtain all commits data from all pages for a given GitHub repo `repo_name`.
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
    :type: int
    :param verbose: print commit data dimensions and counts. Default: True
    :type: bool
    :return: `all_commits` pd.DataFrame for repo `repo_name`.
    :type: DataFrame
    """

    # repo_name confirmation?

    # repo connection?
    repo_con = ghconnect.get_repo_connection(repo_name, config_path, per_pg)  # create gh repo object to given repo
    # contains:  #ghlink = ghauth.setup_github_auth() with config path default to '../config' & per_page=100

    # create empty list for commit data:
    store_pgs = []

    # loop through pages of commit data, append to list
    for page in repo_con.get_commits():
        store_pgs.append(page._rawData)

    if verbose:
        print("Total responses:", len(store_pgs))

    # convert list to dataframe
    all_commits = pd.DataFrame(store_pgs)

    if verbose:
        print("Shape of data:", all_commits.shape)
        print("Commit columns:", all_commits.columns)
        print(all_commits.head())

    # confirm all important columns present;
    # pull author info into username only `commit_author` column
    # drop unnecessary columns;
    # convert dates/times w/ pd.to_datetime()

    # add repo_name column to df
    all_commits['repo_name'] = repo_name

    # return df

    return all_commits
