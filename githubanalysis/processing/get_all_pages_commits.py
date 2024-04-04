""" Function to retrieve ALL commits for a given GitHub repository. """

import sys
import os
import pandas as pd
import numpy as np
import datetime
from datetime import datetime
from datetime import timezone
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.processing.repo_name_clean as name_clean


class CommitsGetter: 

        # if not given a better option, use my default settings for logging
    logger: logging.Logger
    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/get_all_pages_commits_logs.txt')
        else:
            self.logger = logger


    def get_all_pages_commits(self, repo_name, config_path='githubanalysis/config.cfg', per_pg=100, out_filename='all-commits', write_out_location='data/'):
        """
        Obtain all commits data from all pages for a given GitHub repo `repo_name`.
        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
        :type: str
        :param per_pg: number of items per page in paginated GitHub API requests. Default=100 (GH's default= 30)
        :type: int
        :param out_filename: filename suffix indicating commits content (Default: 'all-commits') 
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :return: `all_commits` pd.DataFrame for repo `repo_name`.
        :type: DataFrame
        """

        # get repo_name from commandline if given (accept commandline input) 
        if len(sys.argv) == 2:
            repo_name = sys.argv[1]  # use second argv (user-provided by commandline)

            if not isinstance(repo_name, str):
                raise TypeError("Ensure argument is repository name in string format (e.g. 'repo-owner/repo-name')")

            self.logger.info(f"Using commandline argument {repo_name} as repo name to retrieve GH commits for. Entered as: {sys.argv[1]}")
        else: 
            self.logger.debug(f"Repo name is {repo_name}. Getting commits.")

        # write-out file setup     
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run commits
        sanitised_repo_name = repo_name.replace("/", "-")
        write_out = f'{write_out_location}{out_filename}_{sanitised_repo_name}'
        write_out_extra_info = f"{write_out}_{current_date_info}.csv"  

        # get auth string 
        gh_token = ghauth.setup_github_auth(config_path=config_path)
        headers = {'Authorization': 'token ' + gh_token}

        s = requests.Session()
        retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        # create empty df to store commits data
        all_commits = pd.DataFrame()

        try:    
            page = 1 # try first page only
            commits_url = f"https://api.github.com/repos/{repo_name}/commits?per_page={per_pg}&page={page}"
                # per_page=30 by default on GH, set to max (100)  
            # important bit: API request with auth headers  
            api_response = s.get(url=commits_url, headers=headers)

        except Exception as e_connect:
            if api_response.status_code == 404: 
                self.logger.error(f"404 error in connecting to {repo_name}. Possibly this repo has been deleted or made private?")
            self.logger.error(f"Error in setting up repo connection with repo name {repo_name} and config path {config_path}: {e_connect}.") 

        if api_response.status_code != 404:     
            self.logger.debug(f"Getting commits for repo {repo_name}.")
            #self.logger.debug(f"{api_response}")

            commit_links = api_response.links
            store_pg = pd.DataFrame()
            pg_count = 0

            try: 
                if 'last' in commit_links:
                    commit_links_last = commit_links['last']['url'].split("&page=")[1]
                    pages_commits = int(commit_links_last)

                    pg_range = range(1, (pages_commits+1))

                    for i in pg_range: 
                        pg_count += 1
                        self.logger.info(f">> Running commit grab for repo {repo_name}, in page {pg_count} of {pages_commits}.")        

                        commits_query = f"https://api.github.com/repos/{repo_name}/commits?per_page={per_pg}&page={i}"
                        self.logger.debug(f"Commits query for pg_count{pg_count} is {commits_query}")
                        api_response = s.get(url=commits_query, headers=headers)
                        json_pg = api_response.json()
                        if not json_pg: # check emptiness of result.
                            self.logger.debug(f"Result of api_response.json() is empty list.")
                            self.logger.error(f"Result of API request is an empty json. Error - cannot currently handle this result nicely.")
                        store_pg = pd.DataFrame.from_dict(json_pg)  # convert json to pd.df
                          # using pd.DataFrame.from_dict(json) instead of pd.read_json(url) because otherwise I lose rate handling 
                                                
                        if len(store_pg.index) > 0:
                            try:
                                store_pg['repo_name'] = repo_name
                                store_pg['commit_message'] = pd.DataFrame.from_dict(store_pg['commit']).apply(lambda x: [x.get('message') for x in x])
                                store_pg['author_dev'] = pd.DataFrame.from_dict(store_pg['author']).apply(lambda x: [x.get('login') for x in x])
                                store_pg['committer_dev'] = pd.DataFrame.from_dict(store_pg['committer']).apply(lambda x: [x.get('login') for x in x])
                                store_pg['same_dev'] = np.where((store_pg['author_dev'] == store_pg['committer_dev']), True, False)
                            except Exception as e_pages: 
                                self.logger.debug(f"There seems to be some issue: {e_pages}.")

                            # write out 'completed' page of commits as df to csv via APPEND (use added date filename with reponame inc)
                            store_pg.to_csv(write_out_extra_info, mode='a', index=True, header= not os.path.exists(write_out_extra_info))
                            all_commits = pd.concat([all_commits, store_pg], ) # append this page (df) to main commits df
                        
                        store_pg = pd.DataFrame() # empty the df of last page

                else: # there's no next page, grab all on this page and proceed.
                    pg_count += 1
                    self.logger.debug(f"getting json via request url {commits_query}.")
                    json_pg = api_response.json()
                    if not json_pg: # check emptiness of result.
                        self.logger.debug(f"Result of api_response.json() is empty list.")
                        self.logger.error(f"Result of API request is an empty json. Error - cannot currently handle this result nicely.")
                    store_pg = pd.DataFrame.from_dict(json_pg)

                    if len(store_pg.index) > 0:
                            try:
                                store_pg['repo_name'] = repo_name
                                store_pg['commit_message'] = pd.DataFrame.from_dict(store_pg['commit']).apply(lambda x: [x.get('message') for x in x])
                                store_pg['author_dev'] = pd.DataFrame.from_dict(store_pg['author']).apply(lambda x: [x.get('login') for x in x])
                                store_pg['committer_dev'] = pd.DataFrame.from_dict(store_pg['committer']).apply(lambda x: [x.get('login') for x in x])
                                store_pg['same_dev'] = np.where((store_pg['author_dev'] == store_pg['committer_dev']), True, False)
                            except Exception as e_empty: 
                                self.logger.debug(f"There seem to be no commits on the only page of the query... {e_empty}.")

                    all_commits = store_pg
                    # write out the page content to csv via APPEND (use added date filename)
                    all_commits.to_csv(write_out_extra_info, mode='a', index=True, header= not os.path.exists(write_out_extra_info))
                
                self.logger.debug(f"Total number of commits grabbed is {len(all_commits.index)} in {pg_count} page(s).")
                self.logger.info(f"Commits data written out to file for repo {repo_name} at {write_out_extra_info}.")

            except Exception as e_commits:
                self.logger.error(f"Something failed in getting commits for repo {repo_name}: {e_commits}")

        # reindex df and return;  written out data are NOT reindexed (partly to allow checking whether page is repeated, partly laziness D:)
        #all_commits = all_commits.reset_index(drop=True)  # reindex df; otherwise get indexes N x [0], N x [1] etc where N is number of pages of commits 
        return all_commits 
    



    # this bit
if __name__ == "__main__":
    """
    get commits for specific GH repo. 
    gather into df 
    write out to csv  
    (compare results of running function and reading in resulting csv file)  
    """

    logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='logs/get_all_pages_commits_logs.txt')

    commits_getter = CommitsGetter(logger)

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    else:
        raise IndexError('Please enter a repo_name.')

    commits_df = pd.DataFrame()

    # run the main function to get the commits!
    try: 
        commits_df = commits_getter.get_all_pages_commits(repo_name=repo_name, config_path='githubanalysis/config.cfg')
        if len(commits_df) != 0:
            logger.info(f"Number of commits returned for repo {repo_name} is {len(commits_df.index)}.")
        else:
            logger.warning("Getting commits did not work, length of returned records is zero.")
    except Exception as e:
        logger.error(f"Exception while running get_all_pages_commits() on repo {repo_name}: {e}")

    # generate filename and try to read file in for comparison.
    total_commits = pd.DataFrame()
    try: 
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        commits_file = f"data/all-commits"
        commits_file_extra_info = f"{commits_file}_{sanitised_repo_name}_{current_date_info}.csv"
        total_commits = pd.read_csv(commits_file_extra_info, header=0)
    except Exception as e:
        logger.error(f"There's been an exception while trying to read back in data generated by get_all_pages_commits() from {commits_file_extra_info}: {e}")

    try:
        assert  len(commits_df.index) == len(total_commits.index), f"WARNING! Lengths of returned df ({len(commits_df)}) vs df read in from file ({len(total_commits)}) DO NOT MATCH. Did you append too many records to the gh_urls file??"
    except AssertionError as e:
        logger.error(f"The outputs of running the function and reading back in data DO NOT MATCH; {e}")

        # # get commit messages as new columns in df.
        # #all_commits['commit_message'] = all_commits['commit'].apply(lambda x: [x.get('message') for x in x])

        # # pull author info into username only `commit_author` column
        # #all_commits['commit_author'] = all_commits[['author']].apply(lambda x: [x.get('login') for x in x])

        # # convert dates/times w/ pd.to_datetime() if required
        # #all_commits['commit_date_info'] = all_commits['commit'].apply(lambda x: [x.get('author') for x in x])
        # #all_commits['commit_date'] = ['commit_date_info'].apply(lambda x: [x.get('date') for x in x])

        # #all_commits['commit_date'] = pd.to_datetime(all_commits['commit_date'])
        # #all_commits['commit_date'] = all_commits.commit_date.tz_localize(tz='UTC')
