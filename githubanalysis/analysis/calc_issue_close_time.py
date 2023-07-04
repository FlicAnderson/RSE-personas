""" Function to calculate time in days to close issue for given repo."""

import pandas as pd
import datetime

def calc_issue_close_time(created_at, closed_at, return_in='decimal_days'):
    """
    Takes repo dataset file (e.g. issues data) in json and reads in as pd.DataFrame object.
    :param created_at: creation time of issue; timestamp (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ) (e.g. "created_at": "2011-04-10T20:09:31Z")
    :type: datetime
    :param closed_at: closure time of issue; timestamp (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ) (e.g. "closed_at": "2013-02-12T13:22:01Z")
    :type: datetime
    :param return_in: granularity to return time difference in ('decimal_days', 'whole_days'). Default: 'decimal_days' e.g. 2.7097...
    :type: str
    :return time_diff: time_diff in days to close GitHub issue.
    :type: float64
    """

    if (type(created_at) or type(closed_at)) not in [datetime.datetime, pd.Timestamp]:
        raise TypeError("Input dates are not of type date. Please convert these.")

    if return_in not in ['decimal_days', 'whole_days']:
        raise ValueError("`return_in` parameter must be one of: 'decimal_days' or 'whole_days'.")

    time_diff = pd.Timedelta(closed_at - created_at)

    try:

        if return_in == 'decimal_days':
            return ((time_diff.total_seconds()/60)/60)/24  # returns days in decimal fraction e.g. '2.7097...' is 2 days 17 hours 2 mins etc.

        elif return_in == 'whole_days':
            return time_diff.days  # returns whole days e.g. '2' where time_diff is 2 days 17 hours 2 minutes etc.

        else:
            return time_diff.total_seconds()

    except:
        raise RuntimeError('Calculating time_diff has failed.')
