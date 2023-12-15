""" Get zenodo records for software and pull out GitHub urls from metadata."""

import requests
import csv
from ratelimit import limits, sleep_and_retry

import zenodocode.setup_zenodo_auth as znconnect

# using ratelimit library, set things to 100 calls per minute (secs) time (Authenticated user limits here https://developers.zenodo.org/#rate-limiting)
CALLS = 80
RATE_LIMIT = 60

@sleep_and_retry
@limits(calls=CALLS, period=RATE_LIMIT)
def get_gh_urls(auth='access_token', zenodo_ids_file='data/zn_ids.csv', per_pg=20, total_records=100, filename='gh_urls', write_out_location='data/', verbose=True):
    """
    Get zenodo records for software and pull out GitHub urls from metadata, saving these out into a csv file.

    :param config_path: file path of zenodoconfig.cfg file. Default=zenodocode/zenodoconfig.cfg'.
    :type: str
    :param zenodo_ids_file: file where zenodo software ids are held. Default='data/zn_ids.csv'
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
    write_out = f'{write_out_location}{filename}.csv'

# read in zenodo IDs to get urls from

    with open ('zenodo_ids_file', newline='') as csvfile:
        zn_ids = csv.reader(csvfile)

    identifiers = zn_ids
    print(identifiers)


# zenodo API call setup:

    records_api_url = 'https://zenodo.org/api/records'

# Create file connection
    f = open(write_out, 'w')
    writer = csv.writer(f)

    header = ['Zenodo ID', 'Title', 'DOI', 'GitHub Link', 'CreatedDate']
    writer.writerow(header)

# Iterate through identifiers to get gh url info
    record_count = 0

    for record_id in identifiers:
        r = requests.get(f"{records_api_url}/{record_id}", params={'access_token': auth, 'size': per_pg})

        if r.status_code != 200:
            raise Exception('gh data API response: {}'.format(r.status_code))

        headers_out = r.headers
        print(f"url info request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}")

        if 'metadata' in r.json():

            # API tag info via https://developers.zenodo.org/#representation at 12 Dec 2023.
            record_title = r.json()['title']  # (string) Title of deposition (automatically set from metadata).
            record_created = r.json()['created']  # (timestamp) Creation time of deposition (in ISO8601 format)
            record_doi = r.json()['doi']  # (string) Digital Object Identifier (DOI) ... only present for published depositions
            record_metadata = r.json()['metadata']  # (object) deposition metadata resource
            #record_published = r.json()['metadata']['publication_date']  # (string) Date of publication in ISO8601 format (YYYY-MM-DD). Defaults to current date.

            if 'related_identifiers' in record_metadata:
                record_metadata_identifiers = r.json()['metadata']['related_identifiers']

                if ("github.com" in record_metadata_identifiers[0]['identifier']) & (
                        "url" in record_metadata_identifiers[0]['scheme']):

                    record_gh_repo_url = record_metadata_identifiers[0]['identifier']

                    row = []
                    row.append(record_id)
                    row.append(record_title)
                    row.append(record_doi)
                    row.append(record_gh_repo_url)
                    row.append(record_created)
                    #row.append(record_published)
                    writer.writerow(row)
                    record_count += 1

            else:

                continue
        else:

            continue

    f.close()

    if verbose:
        print(f'Retrieved {record_count} zenodo record github URLs')

    if verbose:
        print(f'file saved out as: {write_out} at {write_out_location}')

    #return(write_out)  # write_out filename and path.
