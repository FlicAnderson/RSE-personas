"""Data cleaning workflow for GitHub repo analysis."""

import sys

import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.get_all_pages_issues as getallissues
import githubanalysis.processing.write_out_repo_data as writeout


def main():
    """
    data cleaning stuff:
        handle GitHub url input (read in from file? / GitHub API call?)
        loop over GitHub urls using repo_name_clean() to do cleaning
        save clean data out
        pass clean data to analysis script
    """

# read in list of repo_names from some file / specific repo request e.g. ROpenSci repos using R language x 100 or sth.

    repo_name = sys.argv[1]  # TODO: remove this once using read-in data instead of commandline
    repo_name = name_clean.repo_name_clean(repo_name)


# ISSUES DATA:

    all_issues = getallissues.get_all_pages_issues(
        repo_name,
        config_path='githubanalysis/config.cfg',
        per_pg=100,
        issue_state='all',
        verbose=True
    )  # get all issues from all pages for given repo

    writeout.write_out_repo_data(
        repo_data_df=all_issues,
        repo_name=repo_name,
        filename='all_issues',
        write_out_as='json'
    )  # write out issues data to file


# OTHER DATA (e.g. COMMITS, METRICS):

    # other bits.


# this bit
if __name__ == "__main__":
    main()
