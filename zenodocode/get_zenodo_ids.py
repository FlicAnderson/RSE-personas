"""Get zenodo record ids for software."""

import requests
from requests.adapters import HTTPAdapter, Retry
import logging
import csv
import datetime

import utilities.get_default_logger as loggit
import zenodocode.setup_zenodo_auth as znauth
from zenodocode.check_zn_response import run_with_retries, raise_if_response_error


class ZenodoIDGetter:
    # if not given a better option, use my default settings for logging
    logger: logging.Logger

    def __init__(
        self,
        in_notebook: bool,
        config_path: str = "zenodocode/zenodoconfig.cfg",
        logger: None | logging.Logger = None,
    ) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(
                console=False,
                set_level_to="INFO",
                log_name="logs/get_zenodo_ids_logs.txt",
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

    def get_zenodo_ids(
        self,
        per_pg=20,
        total_records=100,
        all_versions=False,
        filename="zn_ids",
        write_out_location: str = "data/",
    ) -> list[int]:
        """
        Get zenodo record ids for software, saving these out into a csv file.

        :param per_pg: number of items per page in paginated API requests. Default=20.
        :type: int
        :param total_records: Total number of zenodo records to iterate through to pull github URLS from if present. Default=100.
        :type: int
        :param all_versions: retrieve all versions of a record e.g. v1.0 and v2.0 record info? (default: False)
        :type: bool
        :param filename: name to include in write out filename. Saves as CSV.
        :type: str
        :param write_out_location: Desired file location path as string. Default = "data/"
        :type: str
        :returns: list of zenodo IDs of software type matching query parameters.
        :rtype: list of integers

        Examples:
        ----------
        TODO.
        """

        # writeout setup:

        # build path + filename
        write_out = f"{write_out_location}{filename}_{self.current_date_info}.csv"

        # zenodo API call setup:

        records_api_url = "https://zenodo.org/api/records"
        search_query = "type:software"

        page_iterator = 1

        self.logger.info(f"Obtaining {total_records} zenodo record IDs")

        # pull out N zenodo record IDs using a records query, paging through until N = page_iterator:

        if all_versions:
            get_all_versions = "true"
        else:
            get_all_versions = "false"

        self.logger.info(
            f"Trying Zenodo API call with url: {records_api_url} and search query parameters: q={search_query}, all_versions={get_all_versions}, size={per_pg} and page={page_iterator}."
        )
        # this is the important part: run API call with retries and sleeps if necessary to avoid rate limit issues
        api_response = run_with_retries(
            lambda: raise_if_response_error(
                api_response=self.s.get(
                    url=records_api_url,
                    params={
                        "access_token": self.zn_token,
                        "q": search_query,
                        "all_versions": get_all_versions,
                        "size": per_pg,
                        "page": page_iterator,
                    },
                ),
                logger=self.logger,
            ),
            self.logger,
        )

        assert api_response.ok, f"API response is: {api_response}"

        headers_out = api_response.headers
        print(
            f"record ID request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}"
        )

        if "hits" in api_response.json():
            still_iterating = True
        else:
            still_iterating = False

        identifiers = []

        while still_iterating and (len(identifiers) < total_records):
            api_response.raise_for_status()

            if "hits" in api_response.json():
                for hit in api_response.json()["hits"]["hits"]:
                    identifiers.append(hit["id"])

            page_iterator += 1

        self.logger.info(f"Querying {len(identifiers)} zenodo record IDs")

        print(identifiers)

        # Create file connection
        f = open(write_out, "w")
        writer = csv.writer(f)

        header = ["Zenodo ID"]
        writer.writerow(header)

        # Iterate through identifiers to get gh url info
        record_count = 0

        for record_id in identifiers:
            row = []
            row.append(record_id)
            writer.writerow(row)
            record_count += 1

        f.close()

        self.logger.info(f"Retrieved {record_count} zenodo record IDs")

        self.logger.info(
            f"Zenodo IDs file saved out as: {write_out} at {write_out_location}"
        )

        return identifiers
