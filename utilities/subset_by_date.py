"""This (set of) function(s) are to help subset the dataset via dates for valid RSE Persona calculations."""

import pandas as pd
import datetime


def subset_by_dates(
    df: pd.DataFrame,
    datestamp_column=str,
    from_datestamp: datetime.datetime = datetime.datetime.min,  # default to earliest possible year - not sensible, but doesn't change behaviour :C
    to_datestamp: datetime.datetime = datetime.datetime.today(),  # defaults to today, which is the latest possible date, no behaviour changed.
):
    """
    There should be a function that subsets the reviews'
    interactions to between specific date/timestamps in a specific column
    to assist with future calculations and analysis.

    Assumes UTC timezone as this is the default GH timezone.
    """
    return df[
        (df[datestamp_column] > from_datestamp) & (df[datestamp_column] < to_datestamp)
    ]
