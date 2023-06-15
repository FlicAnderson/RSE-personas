""" Function to calculate time in days from date since repo creation for given repo."""

import pandas as pd


import githubanalysis.processing.get_repo_creation_date as createdate

def calc_days_since_repo_creation(date, repo_name, return_in='days', config_path='githubanalysis/config.cfg'):
    """
    Takes repo dataset file (e.g. issues data) in json and reads in as pd.DataFrame object.
    :param date: date to calculate number of days to, since creation date of repo.
    :type: datetime
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param return_in: format to return days since repo creation in (e.g. just number of days vs with hours etc. Default: 'days'.
    :type: str
    :return days_since: days_since input `date` since repo creation date for repo `repo_name`.
    :type: int (return_in='days') / pd.Timedelta (return_in not 'days')
    """

    # check date input is correct format


    days_since = date - createdate.get_repo_creation_date(repo_name, config_path=config_path, verbose=False)

    if return_in == 'days':

        return days_since.days

    else:
        return days_since
