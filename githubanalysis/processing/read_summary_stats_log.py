"""Pull Summarised Repo Stats Data out of logs from lots/summarise_repo_stats_logs.txt to usable pandas df in csv."""

import argparse
from pathlib import Path
import datetime
import re
import pandas as pd
import logging
import utilities.get_default_logger as loggit
from typing import Any
from ast import literal_eval

# """
# $ python githubanalysis/processing/read_summary_stats_log.py -f logs/summarise_repo_stats_logs.txt
# generates: data/summarised_repo_stats_2025-03-26.csv  for example
# """

# helper functions for pulling out borks:

# compile the regular expressions ahead of time because it's an expensive operation
dict_keys_pat = re.compile(r"dict_keys\((\[[^\]]*\])\)")
datetime_pat = re.compile(r"datetime\.datetime")
tzinfo_pat = re.compile(r"tzinfo=datetime\.timezone\.utc")


def remove_dict_keys(from_: str) -> str:
    return re.sub(dict_keys_pat, r"\1", from_)


def remove_datetime(from_: str) -> str:
    return re.sub(datetime_pat, "", from_)


def remove_tzinfo(from_: str) -> str:
    return re.sub(tzinfo_pat, "", from_)


# main parsing happens here
def parse_log(lines: list[str]) -> list[tuple[str, dict[str, Any]]]:
    """
    Parse a line from the log file summarise_repo_stats_logs.txt;
    This function: pulls out required elements of the logfile line,
    applies transformations, removes problematic bits before evaluating
    the 'dictionary string' to a REAL dictionary item;
    Returns a tuple of repo_name, and a dictionary of the repo's details data.
    """

    indicator = " INFO:Stats for "
    out = list[tuple[str, dict[str, Any]]]()
    for line in lines:
        if indicator not in line:
            continue
        line = line.strip()
        # line.index(indicator) = index of indicator is the index of the first character of `indicator` in `line`
        # e.g. the space in front of INFO:Stats for
        # adding `len(indicator)` shifts index to one past the end of the `indicator`
        # the colon before the closing ] means "everything from here to the end of the string"
        # therefore, details == repo_name and the whole dict of content
        details = line[line.index(indicator) + len(indicator) :]
        start_of_dict_idx = (
            details.index(": ") + 2
        )  # Same logic as above, but jump to location of ':', then add 2, because `len(": ") == 2`

        # details is repo_name, so we're running from start of that to location of {,
        # then minus 2 for the space and colon before end of repo_name
        repo_name = details[: start_of_dict_idx - 2]

        # use regex-applier functions to remove badness that borks the literal_eval otherwise:
        # remove dict_keys() badness if there
        # remove datetimes if there
        # remove timezoneinfo if there
        dict_str = remove_tzinfo(
            remove_datetime(remove_dict_keys(details[start_of_dict_idx:]))
        )
        # this takes a string representation of a python literal (dict, list, str, etc...) and returns it as a python object:
        repo_dict = literal_eval(dict_str)
        if (
            "last_PR_update" in repo_dict and repo_dict["last_PR_update"] is not None
        ):  # if there's a datetime, re-apply datetime-ness properly
            repo_dict["last_PR_update"] = datetime.datetime(
                *repo_dict["last_PR_update"],
                tzinfo=datetime.timezone.utc,  # '*' means put this thing here elements-wise
            )
        out.append((repo_name, repo_dict))
    return out


class RepoStatsReader:
    logger: logging.Logger
    in_notebook: bool
    current_date_info: str
    write_location: Path

    def __init__(
        self,
        in_notebook: bool,
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="DEBUG",
                log_name="logs/read_repo_stats_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # at start of script to avoid midnight/long-run issues
        # self.read_location = read_location
        self.write_location = Path("data/" if not in_notebook else "../../data/")

    def read_repo_summary_data(
        self,
        filename: str | Path,
        write_location="data/",
    ) -> pd.DataFrame | None:
        """
        This function applies parse_log() line by line of the logfile;
        It appends matching dictionary to a list, then converts to dataframe
        and writes out to CSV file.
        """

        with open(filename, "r") as file:
            content = file.readlines()

        # parse line by line, removing badness,
        # returning tuple of repo_name and working dictionary of details
        items = parse_log(content)

        # pull out the dictionary only from tuple, convert to pd.DF
        repo_stats = pd.DataFrame.from_records([a[1] for a in items])

        saveas = f"summarised_repo_stats_{self.current_date_info}.csv"

        # write out the df to csv file to the write location
        repo_stats.to_csv(self.write_location / saveas, index=False)
        return repo_stats


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--filepath_for_logfile",
    metavar="PATH",
    help="Path to file containing summary stats logfile.",
    type=Path,
    required=False,
    default="logs/summarise_repo_stats.txt",
)

if __name__ == "__main__":
    args = parser.parse_args()
    filepath: Path = args.filepath_for_logfile

    logger = loggit.get_default_logger(
        console=True,
        set_level_to="DEBUG",
        log_name="logs/read_repo_stats_logs.txt",
        in_notebook=False,
    )

    logger.debug(f"{filepath = }")  # THE SPACE AFTER EQUALS IS REQUIRED FOR FORMATTING

    repostatsreader = RepoStatsReader(in_notebook=False, logger=logger)

    # do the reading and writing out of summary details
    repostatsreader.read_repo_summary_data(filename=filepath)
