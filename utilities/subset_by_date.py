"""This (set of) function(s) are to help subset the dataset via dates for valid RSE Persona calculations."""

import pandas as pd
import datetime


def subset_by_dates(
    df: pd.DataFrame,
    datestamp_column,
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

    print(f"{df.datestamp_column.dtype}")

    if isinstance(to_datestamp, str):
        to_datestamp = pd.Timestamp(to_datestamp).date()

    assert isinstance(to_datestamp, pd.Timestamp) or isinstance(
        to_datestamp, datetime.date
    ), (
        f"to_datestamp is not an instance of pd.Timestamp or datetime.date, instead it's {type(to_datestamp)}."
    )

    output = df[
        (df[datestamp_column] > from_datestamp)
        & (
            df[datestamp_column] < to_datestamp
        )  # df retains only rows AFTER from_datestamp AND BEFORE to_datestamp!
    ]

    print(f"post_subset_len = {len(output)}")
    output_len = len(output)

    print(
        f"Dropping {orig_len - output_len} rows ({(((orig_len - output_len) / orig_len) * 100):.3f}%) from df as later than date {to_datestamp}"
    )

    return output
