"""Get GitHub urls from metadata of existing zenodo software record IDs read in from csv file."""

import os
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import logging
import math
import datetime

import utilities.chunker as chunker
import utilities.get_default_logger as loggit
import zenodocode.setup_zenodo_auth as znauth
from zenodocode.check_zn_response import run_with_retries, raise_if_response_error


class GhURLsGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(
        self,
        config_path: str,
        logger: None | logging.Logger = None,
        in_notebook=False,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_gh_urls_logs.txt",
                in_notebook=in_notebook,
            )
        else:
            self.logger = logger

        self.s = requests.Session()
        retries = Retry(
            total=10,
            connect=5,
            read=3,
            backoff_factor=1,
            status_forcelist=[202, 502, 503, 504],
        )
        self.s.mount("https://", HTTPAdapter(max_retries=retries))
        self.zn_token = znauth.setup_zenodo_auth(config_path=config_path)
        self.config_path = config_path
        self.in_notebook = in_notebook
        # write-out file setup
        self.current_date_info = datetime.datetime.now().strftime(
            "%Y-%m-%d"
        )  # run this at start of script not in loop to avoid midnight/long-run commits

    def get_gh_urls(
        self,
        zenodo_ids: list[int],
        out_filename="gh_urls",
        write_out_location="data/",
    ):
        """
        Read in csv of zenodo record IDs for software records and query; pull out GitHub urls from metadata;
        save these records out into a csv file and return all records in a dataframe.
        Logging output to file get_gh_urls_logs.txt

        :param zenodo_ids: list of zenodo IDs to check within zenodo API for github URL info.
        :type: list[int]
        :param out_filename: name to include in write out filename. Saves as CSV.
        :type: str
        :param write_out_location: desired file location path as string. Default = "data/"
        :type: str
        :returns: gh_urls_df - a pd.DataFrame of github url records from zenodo and their metadata in columns: index, ZenodoID, Title, DOI, GitHubURL, CreatedDate.
        :type: pd.DataFrame
        """

        # write-out file setup
        # get date for generating extra filename info
        write_out = f"{write_out_location}{out_filename}"
        write_out_extra_info = f"{write_out}_{self.current_date_info}.csv"

        # batch_size = 10
        total_records = len(zenodo_ids)
        # num_batches = math.ceil(total_records / batch_size)  # 3
        self.logger.debug(f"Fetching urls for {total_records} records")

        # 'gatherer' variables setup
        record_count = 0  # counts records with github urls
        id_count = 0
        loop_num = 0  # counts current 'chunk' loop
        gh_urls_df = pd.DataFrame()  # create empty df to hold complete record set

        records_list = []

        records_api_url = "https://zenodo.org/api/records"

        for record_id in zenodo_ids:
            loop_num += 1
            self.logger.info(
                f"\n >> Running loop number {loop_num} of {total_records} ... "
            )

            # API queries loop; zenodo API query created
            record_query_url = f"{records_api_url}/{record_id}"

            self.logger.info(f"getting json via request url {record_query_url}.")
            api_response = run_with_retries(
                fn=lambda: raise_if_response_error(
                    api_response=self.s.get(
                        url=record_query_url,
                        params={"access_token": self.zn_token},
                        # timeout=10,
                    ),
                    logger=self.logger,
                ),
                logger=self.logger,
            )
            assert api_response.ok, f"API response is: {api_response}"

            self.logger.debug(
                f"For record ID {record_id}, API response is {api_response}; with rate limit remaining: {api_response.headers['x-ratelimit-remaining']}"
            )
            self.logger.debug(f"JSON is: {api_response.json()}")

            if "metadata" in api_response.json():
                # API tag info via https://developers.zenodo.org/#representation at 12 Dec 2023.
                record_title = api_response.json()[
                    "title"
                ]  # (string) Title of deposition (automatically set from metadata).
                record_created = api_response.json()[
                    "created"
                ]  # (timestamp) Creation time of deposition (in ISO8601 format)
                record_doi = api_response.json()[
                    "doi"
                ]  # (string) Digital Object Identifier (DOI) ... only present for published depositions
                record_metadata = api_response.json()[
                    "metadata"
                ]  # (object) deposition metadata resource

                if "related_identifiers" in record_metadata:
                    record_metadata_identifiers = api_response.json()["metadata"][
                        "related_identifiers"
                    ]

                    if (
                        "github.com" in record_metadata_identifiers[0]["identifier"]
                    ) & ("url" in record_metadata_identifiers[0]["scheme"]):
                        # get the github url!
                        record_gh_repo_url = record_metadata_identifiers[0][
                            "identifier"
                        ]

                        # collate items into a dictionary for this record ID
                        row_dict = {
                            "ZenodoID": record_id,
                            "Title": record_title,
                            "DOI": record_doi,
                            "GitHubURL": record_gh_repo_url,
                            "CreatedDate": record_created,
                        }
                        self.logger.debug(
                            f"{record_id}; {record_title}; {record_created}; {record_doi}; {record_gh_repo_url}"
                        )
                        # add this completed 'row' to the chunk
                        records_list.extend(row_dict)
                        self.logger.debug(
                            f"At (including) ID count {id_count} there have been {record_count} github urls records located so far."
                        )
                        record_count += 1

            # create a df from records_list:
            gh_urls_df = pd.DataFrame(records_list)

            # write out 'completed' chunk df content to csv via APPEND (use added date filename)
            gh_urls_df.to_csv(
                write_out_extra_info,
                mode="w",
                index=False,
                header=not os.path.exists(write_out_extra_info),
            )

        # print(f"There are {record_count} records with github urls, out of {total_records} records in total; saved out to {write_out_extra_info}.")
        self.logger.info(
            f"\n ... ENDING RUN. There are {record_count} records with github urls, out of {total_records} records in total; saved out to {write_out_extra_info}."
        )
        # return complete set of github url records as a dataframe
        return gh_urls_df
