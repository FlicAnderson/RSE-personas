"""Data cleaning workflow for GitHub repo analysis."""

import sys

import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.get_all_pages_issues as getallissues
import githubanalysis.processing.write_out_repo_data as writeout
#import githubanalysis.processing.read_in_repo_data as readin
import githubanalysis.processing.calc_issue_close_time as calcclose
import githubanalysis.visualization.plot_repo_issues_data as plotissues


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

    # this is a rather coarse attempt at whether to use repo_name_clean() or not, but good in the meantime.
    # TODO: would be nice to try parseing the url or check how many slashes etc.
    if 'github' in repo_name:
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
        write_out_as='json',
        write_out_location='data/',
        write_orientation='table',
        verbose=True
    )  # write out issues data to file

    # read data back in from file & return tuple: read_in_df, repo_name
    #all_issues_new = readin.read_in_repo_data(read_in='data/all_issues__riboviz_riboviz.json', repo_name=None, read_in_as='json', read_orientation='table', verbose=True)
        ## remember that read_in_repo_data() returns tuple. Access as follows:
        # e.g. print(all_issues_new[0].shape, all_issues_new[1])


    # calculate issue close times

    closed_issues = getallissues.get_all_pages_issues(
        repo_name=repo_name,
        config_path='githubanalysis/config.cfg',
        per_pg=100,
        issue_state='closed',
        verbose=True
    )  # get closed issues from all pages for given repo

    #print(closed_issues.dtypes)

    # calculate close_time for each closed issue
    closed_issues['close_time'] = closed_issues.apply(lambda x: calcclose.calc_issue_close_time(x.created_at, x.closed_at, return_in='decimal_days'), axis=1)

    # Get average close time in DF of repo issues.
    repo_issue_close_mean = closed_issues['close_time'].mean()

    print(f"For repo {repo_name}, average issue closure time was {repo_issue_close_mean} days")
    # 73.047... days to close (average) 314 closed issue tickets @ riboviz/riboviz

# OTHER DATA (e.g. COMMITS, METRICS):

    # other bits.

    plotissues.plot_repo_issues_data(closed_issues, repo_name, save_out=True, save_name='issues_data_plot', save_type='png', save_out_location='images/')



# this bit
if __name__ == "__main__":
    main()
