""" Function to calculate average issue close times per assigned dev username from issue ticket data for a repo."""

import pandas as pd


def calc_per_dev_mean_close_time(repo_data_df):
    """
    Takes repo issue ticket data (pd.DataFrame object), and creates new column of assignee data pulled out from 'assignees' column.
    :param repo_data_df: closed issue ticket data to calculate issue close_time data for (requires 'assigned_devs' column)
    :type: pd.DataFrame
    :return repo_data_df:
    :type: pd.DataFrame
    """

    # check input df 'repo_data_df' isn't empty
    # check df has 'close_time' column present (ie calc_issue_close_time() has been run)
    # check 'assigned_devs' column present (ie get_issue_assignees() has been run)

    # get all unique dev usernames from closed issue tickets -> 'dev_list'

    # for each dev in dev_list:
    #   identify each issue where dev is assigned

        #   get close_time for issue

        #   add dev, close_time and issue number and repo_number to df 'all_devs_close_times'
        #   calculate mean from all_devs_close_times for dev

        #   return ?df? for dev to output (+/- repo_name?)

    # calc summary per_dev stats (% of issues assigned; lone-wolf vs team-worker; mean_close_time; min/max issue close_time
    # print each (dev, per_dev_mean_close_time) tuple if verbose
    # return df of devs and per_dev_mean_close_times.
