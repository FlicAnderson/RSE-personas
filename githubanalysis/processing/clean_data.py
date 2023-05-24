"""Data cleaning workflow for github repo analysis."""

import sys
import githubanalysis.repo_name_clean as name_clean

# data cleaning stuff:
    # handle github url input (read in from file? / github API call?)
    # loop over github urls using repo_name_clean() to do cleaning
    # save clean data out
    # pass clean data to analysis script

def main():
    repo_name = sys.argv[1] # TODO: remove this once using read-in data instead of commandline
    name_clean.repo_name_clean(repo_name)

# this bit
if __name__ == "__main__":
    main()

