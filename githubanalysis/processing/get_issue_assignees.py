""" Function to pull out assignee usernames from issue ticket data for a repo."""

import pandas as pd


def get_issue_assignees(repo_data_df):
    """
    Takes repo issue ticket data (pd.DataFrame object), and creates new column of assignee data pulled out from 'assignees' column.
    :param repo_data_df: data to parse assignees data for
    :type: pd.DataFrame
    :return repo_data_df: input dataframe with assignee data clearly appended in 'assigned_devs' column as lists.
    :type: pd.DataFrame
    """

    if repo_data_df.empty:  # if read_in hasn't worked and dataframe is empty
        print(f"Dataframe is empty.")
    else:
        print(f"Dataframe has original dimensions: {repo_data_df.shape}.")

    repo_data_df['assigned_devs'] = repo_data_df[['assignees']].applymap(
        lambda x: [x.get('login') for x in x]
    )

    print(f"Dataframe has been updated with 'assigned_devs' info and now has dimensions: {repo_data_df.shape}.")

    return repo_data_df
