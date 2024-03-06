""" Get all repo contributors data for a GitHub repo."""
import sys
import os
import pandas as pd
import datetime
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit
import githubanalysis.processing.setup_github_auth as ghauth
import githubanalysis.processing.repo_name_clean as name_clean


class DevsGetter: 
    
    # if not given a better option, use my default settings for logging
    logger: logging.Logger
    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/get_repo_contributors_logs.txt')
        else:
            self.logger = logger

    def get_repo_contributors(self, repo_name, config_path='githubanalysis/config.cfg', out_filename='contributors', write_out_location='data/'):
        """
        Get contributor data for given repo `repo_name`, output data as .csv file  
        :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
        :type: str
        :param config_path: file path of config.cfg file. Default=githubanalysis/config.cfg'.
        :type: str
        :param out_filename: filename suffix indicating contributors content (Default: 'contributors') 
        :type: str
        :param: write_out_location: path of location to write file out to (Default: 'data/')
        :type: str
        :returns: `contributors` pd.DataFrame for given repo `repo_name`.
        :type: DataFrame
        """

        #accept commandline reponame input if given
        if len(sys.argv) == 2:
            repo_name = sys.argv[1]  # use second argv (user-provided by commandline)

            if not isinstance(repo_name, str):
                raise TypeError("Ensure argument is repository name in string format (e.g. 'repo-owner/repo-name')")

            self.logger.info(f"Using commandline argument {repo_name} as repo name to retrieve GH contributors for. Entered as: {sys.argv[1]}")
        else: 
            try:
                repo_name = repo_name
                self.logger.debug(f"Repo name to get contributors from is {repo_name}.")
            except: 
                raise IndexError('Please enter a repo_name.')
        
        #set up writeout file
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        write_out = f'{write_out_location}{out_filename}_{sanitised_repo_name}'
        write_out_extra_info = f"{write_out}_{current_date_info}.csv" 

        #run ghauth into API request headers
        gh_token = ghauth.setup_github_auth(config_path=config_path)
        headers = {'Authorization': 'token ' + gh_token}


        #set up requests.Session()
        s = requests.Session()
        retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        #create storage df
        contributors_df = pd.DataFrame()

        #run first connection s.get() and error handle
        try:
            page = 1 # try first page only
            anon = True # include anonymous contributors in results
            contributors_url = f"https://api.github.com/repos/{repo_name}/contributors?anon={anon}&per_page=100&page={page}"
                # per_page=30 by default on GH, set to max
            
            api_response = s.get(url=contributors_url, headers=headers)

        except Exception as e_connect:
            if api_response.status_code == 404: 
                self.logger.error(f"404 error in connecting to {repo_name}. Possibly this repo has been deleted or made private?")
            self.logger.error(f"Error in setting up repo connection with repo name {repo_name} and config path {config_path}: {e_connect}.") 

        if api_response.status_code != 404:     
            self.logger.debug(f"Getting contributors for repo {repo_name}.")
            
            contributors_links = api_response.links
            store_pg = pd.DataFrame()
            pg_count = 0
            
        #handle pages and set up conditional loop
            try: #get contributors data from page
                if 'last' in contributors_links:
                    contributors_links_last = contributors_links['last']['url'].split("&page=")[1]
                    pages_contributors = int(contributors_links_last)

                    pg_range = range(1, (pages_contributors+1))
                    self.logger.debug("has last pg")
                    for i in pg_range: 
                        pg_count += 1
                        self.logger.info(f">> Running contributors grab for repo {repo_name}, in page {pg_count} of {pages_contributors}.")
                        contributors_query = f"https://api.github.com/repos/{repo_name}/contributors?anon={anon}&per_page=100&page={i}"
                        api_response = s.get(url=contributors_query, headers=headers)
                        json_pg = api_response.json()
                        store_pg = pd.DataFrame.from_dict(json_pg)  # convert json to pd.df
                        self.logger.debug("stored_pg")
                          # using pd.DataFrame.from_dict(json) instead of pd.read_json(url) because otherwise I lose rate handling 
                                                
                        if len(store_pg.index) > 0:
                            #store_pg['login'] = store_pg['login'].replace(to_replace=r'^\s*$', value='Anonymous', regex=True)  # if login is empty, this is likely due to Anonymous user. Fill with 'Anonymous'                         
                            # write out 'completed' page of contributors as df to csv via APPEND (use added date filename with reponame inc)
                            store_pg.to_csv(write_out_extra_info, mode='a', index=True, header= not os.path.exists(write_out_extra_info))
                            #append to storage df
                            contributors_df = pd.concat([contributors_df, store_pg], ) # append this page (df) to main contributors df
                            self.logger.debug("transferred to df")
                        store_pg = pd.DataFrame() # empty the df of last page
                
                else: # there's no next page, grab all on this page and proceed.
                    try: 
                        pg_count += 1
                        self.logger.debug(f"getting json via request url {contributors_url}.")
                        json_pg = api_response.json()
                        self.logger.debug("got json")
                        self.logger.debug(json_pg)
                        store_pg = pd.DataFrame.from_dict(json_pg)
                        self.logger.debug("json to dict")
                        #store_pg['login'] = store_pg['login'].replace(to_replace=r'^\s*$', value='Anonymous', regex=True)  # if login is empty, this is likely due to Anonymous user. Fill with 'Anonymous'                         
                        contributors_df = store_pg
                        # write out the page content to csv via APPEND (use added date filename)
                        contributors_df.to_csv(write_out_extra_info, mode='a', index=True, header= not os.path.exists(write_out_extra_info))
                    except Exception as e_singlepg: 
                        self.logger.error(f"Single page of contributors getting failed for repo {repo_name}: {e_singlepg}")
                
                
                self.logger.info(f"Total number of contributors grabbed is {len(contributors_df.index)} in {pg_count} page(s).")
                self.logger.info(f"There are {contributors_df['login'].isna().sum()} anonymous contributors for repo {repo_name}.")

            except Exception as e_contributors:
                self.logger.error(f"Something failed in getting contributors for repo {repo_name}: {e_contributors}")

            #deal with anonymous contributors; announce cases where it's over 500 folks (API case)
            if contributors_df['login'].isna().sum() > 499:
                self.logger.warning(f"There are 500+ ({contributors_df['login'].isna().sum()})contributors in repo {repo_name}; GH only lists 500 users fully, the rest will be shown as anonymous (see https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28#list-repository-contributors).")

            #return contributors storage df repo_devs
            # contributors_df.contributions column =  commits per contributor in descending order. 
            return contributors_df


        
# this bit
if __name__ == "__main__":
    """
    get contributors for specific GH repo. 
    gather into df 
    writeout to csv
    """

    logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='logs/get_repo_contributors_logs.txt')

    devs_getter = DevsGetter(logger)

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    else:
        raise IndexError('Please enter a repo_name.')

    if 'github' in repo_name:
        repo_name = name_clean.repo_name_clean(repo_name)    

    contributors_df = pd.DataFrame()
    
    # run the main function to get the devs!
    try:
        contributors_df = devs_getter.get_repo_contributors(repo_name, config_path='githubanalysis/config.cfg', out_filename='contributors', write_out_location='data/')
        if len(contributors_df) != 0: 
            logger.info("Running get_repo_contributors() has run successfully.")
            #logger.info(f"Number of contributors returned for repo {repo_name} is {len(contributors_df.index)}.")
            #logger.info(f"There are {contributors_df['login'].isna().sum()} anonymous contributors for repo {repo_name}.")
        else: 
            logger.warning("Getting contributors did not work, length of returned records is zero.")
    except Exception as e: 
        logger.error(f"Exception while running get_repo_contributors() on repo {repo_name}: {e}")

    # generate file and try to read back in for comparison as check  
    total_contributors = pd.DataFrame()
    try:
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
        sanitised_repo_name = repo_name.replace("/", "-")
        contributors_file = f"data/contributors"
        contributors_file_extra_info = f"{contributors_file}_{sanitised_repo_name}_{current_date_info}.csv"
        total_contributors = pd.read_csv(contributors_file_extra_info, header=0)
    except Exception as e:
        logger.error(f"There's been an exception while trying to read back in data generated by get_all_pages_contributors() from {contributors_file_extra_info}: {e}")

    try:
        assert  len(contributors_df.index) == len(total_contributors.index), f"WARNING! Lengths of returned df ({len(contributors_df)}) vs df read in from file ({len(total_contributors)}) DO NOT MATCH. Did you append too many records to the gh_urls file??"
    except AssertionError as e:
        logger.error(f"The outputs of running the function and reading back in data DO NOT MATCH; {e}")