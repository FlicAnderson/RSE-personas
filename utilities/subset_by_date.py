"""This (set of) function(s) are to help subset the dataset via dates for valid RSE Persona calculations."""

import pandas as pd
import datetime
from logging import Logger
import utilities.get_default_logger as loggit


def subset_by_dates(
    df: pd.DataFrame,
    datestamp_column,  # name of column to subset by (WILL NOT BE EDITED)
    from_datestamp: datetime.date
    | str = pd.Timestamp.min.date(),  # default to earliest possible year - not sensible, but doesn't change behaviour :C
    to_datestamp: datetime.date | str = pd.Timestamp(
        "today"
    ).date(),  # defaults to today, which is the latest possible date, no behaviour changed. Set to "2024-11-21" for earliest GH data collection date from FIRST collection (commits).
    logger: None | Logger = None,
) -> pd.DataFrame:
    """
    There should be a function that subsets repository interactions data
    dfs to between specific date/timestamps in a specific column, to
    assist with future calculations and analysis.

    !!!!!!!!!!!!
    Latest data collection date for the FIRST data type collected
    from the GH API was: "2024-11-21" for commits data.
    !!!!!!!!!!!!

    Assumes UTC timezone as this is the default GH timezone.

    Note: if you're having comparison issues, try the following on the df
    and original datestamp_column to create a new one in the right format:

    df["review_date_only"] = pd.to_datetime(df.original_datestamp_column)
    df["review_date_only"] = df["review_date_only"].apply(lambda x: pd.Timestamp.date(x))

    """
    if logger is not None:
        logger = logger
    else:
        logger = loggit.get_default_logger(
            console=True,
            set_level_to="DEBUG",
            log_name="logs/subset_by_dates.txt",
            in_notebook=False,
        )

    logger.info(f"datestamp column used for date filtering is: {datestamp_column}.")
    logger.info(f"from_datestamp used for START date filtering is: {from_datestamp}.")
    logger.info(f"to_datestamp used for END date filtering is: {to_datestamp}.")

    orig_len = len(df)
    logger.info(f"orig_len = {len(df)}")

    logger.info(f"data type of datestamp_column is {df[datestamp_column].dtype}")

    df["datestamp_column_temp"] = pd.to_datetime(  # make new column
        df[datestamp_column]
    )  # change type from string to datetime

    logger.info(
        f"type of df['datestamp_column_temp'] is {type(df['datestamp_column_temp'])} ; dtypes of df are: {df.dtypes}"
    )
    logger.info(
        f"df['datestamp_column_temp'][0:5] is: {df['datestamp_column_temp'][0:5]}"
    )

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

    logger.info(f"post_subset_len = {len(output)}")
    output_len = len(output)

    logger.info(
        f"Dropping {orig_len - output_len} rows ({(((orig_len - output_len) / orig_len) * 100):.3f}%) from df as later than date {to_datestamp}"
    )

    return output
