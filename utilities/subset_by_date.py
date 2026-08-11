"""This (set of) function(s) are to help subset the dataset via dates for valid RSE Persona calculations."""

import pandas as pd
import datetime


def subset_by_dates(
    df: pd.DataFrame,
    datestamp_column,  # name of column to subset by (WILL NOT BE EDITED)
    from_datestamp: datetime.date
    | str = pd.Timestamp.min.date(),  # default to earliest possible year - not sensible, but doesn't change behaviour :C
    to_datestamp: datetime.date | str = pd.Timestamp(
        "today"
    ).date(),  # defaults to today, which is the latest possible date, no behaviour changed. Set to "2025-04-23" for latest GH data collection date from FIRST collection (commits).
):
    """
    There should be a function that subsets repository interactions data
    dfs to between specific date/timestamps in a specific column, to
    assist with future calculations and analysis.

    !!!!!!!!!!!!
    Latest data collection date for the FIRST data type collected
    from the GH API was: "2025-04-23" for commits data.
    !!!!!!!!!!!!

    Assumes UTC timezone as this is the default GH timezone.

    Note: if you're having comparison issues, try the following on the df
    and original datestamp_column to create a new one in the right format:

    df["review_date_only"] = pd.to_datetime(df.original_datestamp_column)
    df["review_date_only"] = df["review_date_only"].apply(lambda x: pd.Timestamp.date(x))

    """
    orig_len = len(df)
    print(f"orig_len = {len(df)}")

    print(f"data type of datestamp_column is {df[datestamp_column].dtype}")

    df["datestamp_column_temp"] = pd.to_datetime(  # make new column
        df[datestamp_column]
    )  # change type from string to datetime

    print(
        f"type of df['datestamp_column_temp'] is {type(df['datestamp_column_temp'])} ; dtypes of df are: {df.dtypes}"
    )
    print(f"df['datestamp_column_temp'][0:5] is: {df['datestamp_column_temp'][0:5]}")

    df["datestamp_column_temp"] = df["datestamp_column_temp"].apply(
        lambda x: pd.Timestamp.date(
            x
        )  # drop the times, keep the date for date comparisons and subsetting
    )

    if isinstance(to_datestamp, str):
        to_datestamp = pd.Timestamp(to_datestamp).date()

    assert isinstance(to_datestamp, pd.Timestamp) or isinstance(
        to_datestamp, datetime.date
    ), (
        f"to_datestamp is not an instance of pd.Timestamp or datetime.date, instead it's {type(to_datestamp)}."
    )

    output = df[
        (df["datestamp_column_temp"] > from_datestamp)
        & (
            df["datestamp_column_temp"] < to_datestamp
        )  # df retains only rows AFTER from_datestamp AND BEFORE to_datestamp!
    ]

    # drop extra column created for subsetting with
    output = output.drop(columns=["datestamp_column_temp"], errors="raise")

    print(f"post_subset_len = {len(output)}")
    output_len = len(output)

    print(
        f"Dropping {orig_len - output_len} rows ({(((orig_len - output_len) / orig_len) * 100):.3f}%) from df as later than date {to_datestamp}"
    )

    return output
