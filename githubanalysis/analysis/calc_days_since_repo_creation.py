""" Function to calculate time in days from date since repo creation for given repo."""

import pandas as pd
import datetime


import githubanalysis.processing.get_repo_creation_date as createdate

def calc_days_since_repo_creation(date, repo_name, since_date=None, return_in='whole_days', config_path='githubanalysis/config.cfg'):
    """
    Takes date and calculates number of days since that date from the date a given repo was created.
    For faster performance, since_date (ie date repo was created) can be supplied if already known.

    :param date: date to calculate number of days to, since creation date of repo.
    :type: datetime
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param since_date: date of creation date of repo (optional). If since_date is None, function will use get_repo_creation_date() to obtain it.
    :type: datetime
    :param return_in: format to return days since repo creation in (e.g. just number of days vs with hours etc. Default: 'whole_days'.)
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :return days_since: days_since input `date` since repo creation date for repo `repo_name`.
    :type: int (return_in='days') / pd.Timedelta (return_in not 'days')
    """

    # check date inputs are correct format
    if type(date) not in [datetime.datetime, pd.Timestamp]:
        raise TypeError("Input `date` is are not of type datetime.datetime or pd.Timestamp. Please convert this.")

    if (type(since_date) not in [datetime.datetime, pd.Timestamp]) and (since_date is not None):
        raise TypeError("Optional `since_date` is not of type datetime.datetime, pd.Timestamp or None. Please convert this.")

    if return_in not in ['decimal_days', 'whole_days']:
        raise ValueError("`return_in` parameter must be one of: 'decimal_days' or 'whole_days'.")

    if since_date is None:  # get repo creation date from GH connection .created_at info
        since_date = createdate.get_repo_creation_date(repo_name, config_path=config_path, verbose=False)

    # important bit:
    days_since = date - since_date

    if return_in == 'whole_days':

        return days_since.days

    else:
        return days_since
