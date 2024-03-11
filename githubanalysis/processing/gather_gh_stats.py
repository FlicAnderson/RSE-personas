""" Gather GitHub stats from todo file of repo_names. """

import sys
import os
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import logging
import math
from datetime import datetime

import utilities.chunker as chunker
import utilities.get_default_logger as loggit
import githubanalysis.processing.summarise_repo_stats
from githubanalysis.processing.summarise_repo_stats import RepoStatsSummariser


class GhStatsGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger
    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/gather_gh_stats_logs.txt')
        else:
            self.logger = logger


    def gather_gh_stats(self, config_path='githubanalysis/config.cfg', in_filename='todo', read_in_location='data/', out_filename='gh_stats', write_out_location='data/'):
        """
        Read in csv of github repo names and their zenodo record IDs; 
        Get github stats for each repo; collate details. 
        Save these records out into a csv file and return all records in a dataframe.
        Logging output to file logs/gather_gh_stats_logs.txt
        """
        #logger.propagate = False

        # read-in file setup (accept commandline input for todo_file file if any) 
        if len(sys.argv) == 2:
            todo_file = sys.argv[1]  # use second argv (user-provided by commandline)

            if not isinstance(todo_file, str):
                raise TypeError("Ensure argument is a file location and name in string format (e.g. 'data/todo.csv')")

            self.logger.info(f"Using commandline argument {todo_file} as input file of GH Repo names to retrieve GH stats for. Entered as: {sys.argv[1]}")
        else: 
            # default location: data/todo_file_*.csv 
            todo_file = f"{read_in_location}{in_filename}.csv"

        # write-out file setup     
        # get date for generating extra filename info
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
        write_out = f'{write_out_location}{out_filename}'
        write_out_extra_info = f"{write_out}_{current_date_info}.csv"  

        # read in csv file of repo names and zenodo IDs
        gh_repos_df = pd.read_csv(todo_file, header=0, usecols=['ZenodoID', 'repo_name'], dtype={'ZenodoID':'Int64', 'repo_name':'str'})

        batch_size = 10
        total_records = len(gh_repos_df.index)
        num_batches = math.ceil(total_records/batch_size) 
        self.logger.debug(f"\n ... STARTING RUN. Read in file {todo_file}; Number of Repo Names to process is {total_records}; Batch size is set to {batch_size}; This run requires {num_batches} batches ... \n")

        # 'gatherer' variables setup   
        record_count = 0 # counts records with github urls
        id_count = 0
        loop_num = 0 # counts current 'chunk' loop
        gh_stats_df = pd.DataFrame() # create empty df to hold complete record set  

        # this loop splits the zenodo IDs into 3x batches of size 10 and returns ephemeral 
        for i in chunker.chunker(gh_repos_df['repo_name'], batch_size):
            loop_num += 1
            self.logger.info(f"\n >>> Running loop/chunk number {loop_num} of {num_batches} ... ")
            writeable_chunk = [] # reset to empty the dict of previous records
            writeable_chunk_repos = i.to_list()  # pull IDs into a list of size 10 in this iteration of the loop
            
            for repo in writeable_chunk_repos:
                id_count += 1
                self.logger.debug(f">> Running loop for record ID {repo}, in loop {loop_num}, at repo {id_count} of {total_records}")
                #print(f">> Getting data for repo {repo}, in loop {loop_num}, which is repo {id_count} of {total_records}. <<<")
            
                try: 
                    repo_stats = RepoStatsSummariser.summarise_repo_stats(self, repo_name=repo, config_path=config_path, per_pg=1)
                    writeable_chunk.append(repo_stats)
                except Exception as e_repo: 
                    self.logger.error(f"Something failed in getting stats for repo {repo}, in loop {loop_num}, which is repo {id_count} of {total_records}: {e_repo}")
                
                record_count += 1

            # convert to pandas dataframe format  
            writeable_chunk_df = pd.DataFrame.from_dict(writeable_chunk)

            # write out 'completed' chunk df content to csv via APPEND (use added date filename)
            writeable_chunk_df.to_csv(write_out_extra_info, mode='a', index=False, header= not os.path.exists(write_out_extra_info))

            # add the completed chunk of df to a 'total' df:
            gh_stats_df = pd.concat([gh_stats_df, writeable_chunk_df], )
            writeable_chunk_df = pd.DataFrame() # empty the chunk df 

        # complete the script run
        self.logger.info(f"\n ... ENDING RUN. There are {record_count} records with github stats, out of {total_records} records in total; saved out to {write_out_extra_info}.")

        # return complete set of github stats as a dataframe 
        return(gh_stats_df)






# this bit
if __name__ == "__main__":
    """
    get github repo names, gather GH stats for each.
    write these to csv file
    read csv file back in for comparison
    """
    logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='logs/gather_gh_stats_logs.txt')

    stat_getter = GhStatsGetter(logger)

    gh_repos_df = pd.DataFrame()
    try: 
        # returns dataframe and saves to variable
        gh_repos_df = stat_getter.gather_gh_stats(config_path='githubanalysis/config.cfg', in_filename='todo', read_in_location='data/', out_filename='gh_stats', write_out_location='data/', verbose=False)
        if len(gh_repos_df) != 0:
            logger.info("GitHub stats grab complete.")
        else: 
            logger.warning("GitHub stats grab did not work, length of records returned is zero.")
    except Exception as e: 
        logger.error(f"There's been an exception while trying to run gather_gh_stats(): {e}")

    # read in complete dataset as separate variable for comparison
    total_stats = pd.DataFrame()
    try: 
        current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
        gh_stats_file = "data/gh_stats"
        gh_stats_file_extra_info = f"{gh_stats_file}_{current_date_info}.csv"
        total_stats = pd.read_csv(gh_stats_file_extra_info, header=0)
    except Exception as e: 
        logger.error(f"There's been an exception while trying to read back in data generated by gather_gh_stats() from {gh_stats_file_extra_info}: {e}")
        
    # if everything is good, this shouldn't trigger.
        try: 
            assert len(gh_repos_df.index) == len(total_stats.index), f"WARNING! Lengths of returned df ({len(gh_repos_df)}) vs df read in from file ({len(total_stats)}) DO NOT MATCH. Did you append too many records to the gh_urls file??"
        except AssertionError as e:
            logger.error(f"The outputs of running the function and reading back in data DO NOT MATCH; {e}")