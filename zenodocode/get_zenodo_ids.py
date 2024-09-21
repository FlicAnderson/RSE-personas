"""Get zenodo record ids for software."""

import requests
import csv
from ratelimit import limits, sleep_and_retry

import zenodocode.setup_zenodo_auth as znconnect

# using ratelimit library, set things to 100 calls per minute (secs) time (Authenticated user limits here https://developers.zenodo.org/#rate-limiting)
CALLS = 80
RATE_LIMIT = 60


@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def get_zenodo_ids(
    auth="access_token",
    per_pg=20,
    total_records=100,
    filename="zn_ids",
    write_out_location="data/",
    verbose=True,
):
    """
    Get zenodo record ids for software, saving these out into a csv file.

    :param config_path: file path of zenodoconfig.cfg file. Default=zenodocode/zenodoconfig.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=20.
    :type: int
    :param total_records: Total number of zenodo records to iterate through to pull github URLS from if present. Default=100.
    :type: int
    :param filename: name to include in write out filename. Saves as CSV.
    :type: str
    :param write_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param verbose: whether to print out issue data dimensions and counts. Default: True
    :type: bool
    :returns: TODO.
    :type: TODO.

    Examples:
    ----------
    TODO.
    """

    # writeout setup:

    # build path + filename
    write_out = f"{write_out_location}{filename}.csv"

    # zenodo API call setup:

    records_api_url = "https://zenodo.org/api/records"
    search_query = "type:software"

    page_iterator = 1

    if verbose:
        print(f"Obtaining {total_records} zenodo record IDs")

    # pull out N zenodo record IDs using a records query, paging through until N = page_iterator:

    r = requests.get(
        records_api_url,
        params={
            "access_token": auth,
            "q": search_query,
            "all_versions": "true",
            "size": per_pg,
            "page": page_iterator,
        },
    )

    if r.status_code != 200:
        raise Exception("API response: {}".format(r.status_code))

    headers_out = r.headers
    print(
        f"record ID request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}"
    )

    try:
        r.status_code != 429
        print(f"API status: {r.status_code}")
    except:
        raise requests.exceptions.HTTPError("Rate Limit Exceeded - too many requests.")

    if "hits" in r.json():
        still_iterating = True
    else:
        still_iterating = False

    identifiers = []

    while still_iterating and (len(identifiers) < total_records):
        r.raise_for_status()

        if "hits" in r.json():
            for hit in r.json()["hits"]["hits"]:
                identifiers.append(hit["id"])

        page_iterator += 1

    if verbose:
        print(f"Querying {len(identifiers)} zenodo record IDs")

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

    if verbose:
        print(f"Retrieved {record_count} zenodo record IDs")

    if verbose:
        print(f"Zenodo IDs file saved out as: {write_out} at {write_out_location}")

    # return(write_out)  # write_out filename and path.
