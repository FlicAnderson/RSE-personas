"""Data cleaning workflow for github repo analysis."""

import sys
#from github import Github
import githubanalysis.processing.get_repo_connection as ghconnect
import githubanalysis.processing.repo_name_clean as name_clean
#import githubanalysis.processing.get_all_pages_issues as getpagesissues

# data cleaning stuff:
    # handle github url input (read in from file? / github API call?)
    # loop over github urls using repo_name_clean() to do cleaning
    # save clean data out
    # pass clean data to analysis script

def main():

# read in list of repo_names from some file / specific repo request e.g. ROpenSci repos using R language x 100 or sth.

    repo_name = sys.argv[1] # TODO: remove this once using read-in data instead of commandline
    repo_name = name_clean.repo_name_clean(repo_name)
    print(repo_name)

    ghconnect.get_repo_connection(repo_name)  # create gh repo object to given repo
    # contains:  #ghlink = ghauth.setup_github_auth() with config path default to '../config' & per_page=100

# getpagesissues.get_all_pages_issues(repo_name) # get all issues from all pages for given repo


# this bit
if __name__ == "__main__":
    main()

