""" Function to retrieve all commits across ALL branches for a given GitHub repository and remove duplicates. """

import requests
from requests.adapters import HTTPAdapter, Retry
import logging

import utilities.get_default_logger as loggit

import githubanalysis.processing.get_branches as branchgetter


class AllBranchesCommitsGetter: 

        # if not given a better option, use my default settings for logging
    logger: logging.Logger
    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/get_all_branches_commits_logs.txt')
        else:
            self.logger = logger


    def get_all_branches_commits(self, repo_name, config_path='githubanalysis/config.cfg', per_pg=100, out_filename='all-branches-commits', write_out_location='data/'):
        """
        Obtain all commits data from all API request pages for ALL BRANCHES of a given GitHub repo `repo_name`.  
        cf: get_all_pages_commits( ) which only returns main branch commits. 


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
        :return: `all_branches_commits` pd.DataFrame for repo `repo_name`.
        :type: DataFrame
        """
        

        # write-out file setup     
        ##current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run commits
        ##sanitised_repo_name = repo_name.replace("/", "-")
        ##write_out = f'{write_out_location}{out_filename}_{sanitised_repo_name}'
        ##write_out_extra_info = f"{write_out}_{current_date_info}.csv"  

        ##write_out_extra_info_json = f"{write_out}_{current_date_info}.json"

        # get auth string 
        ##gh_token = ghauth.setup_github_auth(config_path=config_path)
        ##headers = {'Authorization': 'token ' + gh_token}

        s = requests.Session()
        retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
        s.mount('https://', HTTPAdapter(max_retries=retries))

        # create empty df to store commits data
        ##all_commits = pd.DataFrame()

        branches_info = branchgetter.get_branches(repo_name, config_path, per_pg)

        print(len(branches_info))

        ##headers
    