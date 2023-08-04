"""Data cleaning workflow for GitHub repo analysis."""

import sys
import random
import seaborn as sns
import seaborn.objects as so

import pandas as pd

import githubanalysis.processing.repo_name_clean as name_clean
import githubanalysis.processing.get_all_pages_issues as getallissues
#import githubanalysis.processing.write_out_repo_data as writeout
#import githubanalysis.processing.read_in_repo_data as readin
import githubanalysis.analysis.calc_issue_close_time as calcclose
import githubanalysis.processing.get_issue_assignees as issuedevs
import githubanalysis.visualization.plot_repo_issues_data as plotissues
import githubanalysis.visualization.plot_repo_issues_counts_devs as plotissuedevs
import githubanalysis.processing.get_repo_creation_date as createdate
import githubanalysis.analysis.calc_days_since_repo_creation as dayssince
import githubanalysis.processing.get_release_dates as getreleases
import githubanalysis.processing.get_contributor_commits_stats as getcontributorstats
import githubanalysis.visualization.plot_repo_contributor_commits_stats as plotcontributorcommits



def main():
    """
    data cleaning stuff:
        handle GitHub url input (read in from file? / GitHub API call?)
        loop over GitHub urls using repo_name_clean() to do cleaning
        save clean data out
        pass clean data to analysis script
    """

    if len(sys.argv) == 2:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
    elif len(sys.argv) == 1:
        # use of a specified list of test repos.
        repo_name = random.choice([
            'https://github.com/riboviz/riboviz',
            'https://github.com/ropensci/dwctaxon',
            'https://github.com/nasa/prog_models/'
            'https://github.com/FlicAnderson/20230215-JournalClub-BestPractices',
            'https://github.com/DimmestP/nextflow_paired_reads_pipeline',
            'https://github.com/sulu/sulu',
            'https://github.com/ruby/ruby',
            'https://github.com/martinwoodward/PumpkinPi/',
            'https://github.com/r-dbi/odbc',
            'https://github.com/rstudio/cheatsheets',
            'https://github.com/openjournals/joss',
            'https://github.com/easybuilders/easybuild',
            'https://github.com/aeye-lab/pymovements',
            'https://github.com/FredHutch/SEACR',
            'https://github.com/omelchert/pyGLLE',
            'https://github.com/adamspierer/FreeClimber',
            'https://github.com/alphagov/govuk-frontend',
            'https://github.com/rfordatascience/tidytuesday',
            'https://github.com/gbif/pipelines/',
            'https://github.com/gbif/ipt'
        ])
        # riboviz ~314 closed issues,
        # dwctaxon has 49 closed issues, 6 open
        # prog_models has 147 closed issues, 127 open.
        # 20230215-JournalClub-BestPractices has 0 closed issues, 0 open. << NO ISSUES
        # nextflow_paired_reads_pipeline has 0 closed issues, 2 open. << NO CLOSED, ONLY OPEN
        # sulu has 1950 closed issues, 435 open  << THOUSANDS CLOSED ISSUES
        # ruby has 7508 closed, 381 open.  << THOUSANDS CLOSED ISSUES
        # pumpkinpi has no open and no closed issues << NO ISSUES
        # r-dbi odbc has 387 closed, 71 open
        # cheatsheets has 93 closed, 24 open.
        # joss has 657 closed, 128 open
        # easybuild hs 168 closed, 90 open
        # pymovements has 68 closed, 97 open
        # seacr has 27 closed, 55 open
        # pyglle has 1 closed, 0 open << NO OPEN, ONLY CLOSED
        # freeclimber has 2 closed, 2 open
        # govuk-frontend has 981 closed, 262 open
        # tidytuesday has 196 closed 186 open
        # pipelines has 417 closed, 157 open
        # ipt has 1757 closed, 130 open

    else:
        raise IndexError('Please enter a repo_name.')

    if 'github' in repo_name:
        repo_name = name_clean.repo_name_clean(repo_name)


# ISSUES DATA:

    # all_issues = getallissues.get_all_pages_issues(
    #     repo_name,
    #     config_path='githubanalysis/config.cfg',
    #     per_pg=100,
    #     issue_state='all',
    #     verbose=True
    # )  # get all issues from all pages for given repo

    # writeout.write_out_repo_data(
    #     repo_data_df=all_issues,
    #     repo_name=repo_name,
    #     filename='all_issues',
    #     write_out_as='json',
    #     write_out_location='data/',
    #     write_orientation='table',
    #     verbose=True
    # )  # write out issues data to file

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

    # Get average close time in DF of repo issues to 3 decimal places.
    repo_issue_close_mean = round(closed_issues['close_time'].mean(), 3)

    print(f"For repo {repo_name}, average issue closure time was {repo_issue_close_mean} days")
    # 73.047... days to close (average) 314 closed issue tickets @ riboviz/riboviz

    # parse out assignee data from issues df as new column:
    closed_issues = issuedevs.get_issue_assignees(closed_issues)

    # get creation date of repo:
    repo_creation_date = createdate.get_repo_creation_date(repo_name, config_path='githubanalysis/config.cfg', verbose=True)

    # calculate days_since_start for each closed issue
    closed_issues['days_since_start'] = closed_issues.apply(lambda x: dayssince.calc_days_since_repo_creation(x.closed_at, x.repo_name, since_date=repo_creation_date, return_in='whole_days', config_path='githubanalysis/config.cfg'), axis=1)

    # add column with boolean for PR status
    closed_issues['pull_request_bool'] = closed_issues['pull_request'].notna()

    # scatterplot of time to close issue tickets, X AXIS: DAYS SINCE REPO CREATION, with mean closure time xline
    #plotissues.plot_repo_issues_data(closed_issues, repo_name, xaxis='project_time', add_events=False, save_out=True, save_name='issues_data_plot', save_type='png', save_out_location='images/')

    # separate Pull Requests (PRs) from data
    # where closed_issues['pull_request'] IS *NOT* NaN (ie it IS a pull request) => PRs.

    closed_pull_requests = closed_issues.loc[closed_issues['pull_request'].notna()]

    closed_issues_only = closed_issues.loc[closed_issues['pull_request'].isna()]

    print(f"For repo {repo_name}, there are {len(closed_issues_only.index)} closed issue tickets and {len(closed_pull_requests.index)} closed pull requests.")


    # plot ticket_number for closed_issues (closed issues and PRs together, coloured by PR status)
    #plotissues.plot_repo_issues_data(closed_issues, repo_name, xaxis='ticket_number', add_events=False,
    #                                 save_out=True, save_name='pull_requests_data_plot', save_type='png', save_out_location='images/')


    # plot issue ticket data by project_time (closed issues and PRs together, coloured by PR status)
    #plotissues.plot_repo_issues_data(closed_issues, repo_name, xaxis='project_time', add_events=False, save_out=True, save_name='issues_data_plot', save_type='png', save_out_location='images/')

    # issues & assigned devs:
    #plotissuedevs.plot_repo_issues_counts_devs(closed_issues, repo_name, save_name='pull_requests_counts_devs_plot', save_type='png', save_out_location='images/')

# OTHER DATA (e.g. COMMITS, METRICS):
    # other bits.

    # # get release dates for repo
    repo_releases = getreleases.get_release_dates(repo_name, verbose=True)
    #print(repo_releases)
    #print(repo_releases.shape)
    #print(repo_releases.columns)

    # calculate 'days since' date equivalents for release dates if there were any:
    if len(repo_releases.columns) != 0:

        repo_releases['release_date_since_repo_creation'] = repo_releases.apply(
            lambda x: dayssince.calc_days_since_repo_creation(
                x.published_at,
                x.repo_name,
                since_date=repo_creation_date,
                return_in='whole_days',
                config_path='githubanalysis/config.cfg'
            ), axis=1
        )
        # print(repo_releases['release_date_since_repo_creation'])

        repo_releases['releases_before_repo_creation'] = repo_releases['created_at'].apply(
            lambda x: 'True' if x < repo_creation_date else 'False')

        # print(repo_releases['releases_before_repo_creation'])

        if pd.Series(repo_releases['releases_before_repo_creation']).any():
            print(f"BE AWARE: Some releases were created before the 'official' repo creation date.")

        # print(repo_releases.columns)

        release_events = repo_releases['release_date_since_repo_creation']
        print(f'release events: {release_events}')
        print(f'type release events: {type(release_events)}')

        # plot issues data WITH RELEASE DATE LINES
        plotissues.plot_repo_issues_data(closed_issues, repo_name, xaxis='project_time', add_events=release_events,
                                         save_out=True, save_name='releases_issues_data_plot', save_type='png',
                                         save_out_location='images/')

    # get contributor stats for repo:
    contributor_commits_stats = getcontributorstats.get_contributor_commits_stats(repo_name, verbose=True)
    if contributor_commits_stats is not None:
        print(contributor_commits_stats.head())
        print(type(contributor_commits_stats))

        # plot contributor stats for repo:
        plotcontributorcommits.plot_repo_contributor_commits_stats(
            repo_data_df=contributor_commits_stats,
            repo_name = repo_name,
            save_out=True,
            save_name='contributor_commits_totals_plot',
            save_type='png',
            save_out_location='images/',
            verbose=True
        )


# this bit
if __name__ == "__main__":
    main()
