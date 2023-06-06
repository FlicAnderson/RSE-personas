""" Function to calculate time in days to close issue for given repo."""

import pandas as pd
import datetime


def calc_issue_close_time(created_at, closed_at):
    """
    Takes repo dataset file (e.g. issues data) in json and reads in as pd.DataFrame object.
    :param created_at: creation time of issue; timestamp (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ) (e.g. "created_at": "2011-04-10T20:09:31Z")
    :type: datetime
    :param closed_at: closure time of issue; timestamp (ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ) (e.g. "closed_at": "2013-02-12T13:22:01Z")
    :type: datetime
    :return time_diff: time_diff in days to close GitHub issue.
    :type: ?str
    """

    # todo: check closed_at and created_at are datetimes
    if (type(created_at) or type(closed_at)) is not (datetime.datetime or pd.Timestamp):
        raise TypeError("Input dates are not of type date. Please convert these.")

    time_diff = closed_at - created_at

    # todo: make precision of return an argument

    return time_diff.days
