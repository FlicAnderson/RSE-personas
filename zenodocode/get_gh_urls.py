""" Get zenodo records for software and pull out GitHub urls from metadata."""

import requests
import csv


import zenodocode.setup_zenodo_auth as znconnect



def get_gh_urls(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=100, filename='gh_urls', write_out_location='data/', verbose=True):
    """
    Get zenodo records for software and pull out GitHub urls from metadata, saving these out into a csv file.

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

# check Zenodo API with test request to confirm token authentication is working.
    try:
        znconnect.setup_zenodo_auth(config_path=config_path, verbose=False)
    except requests.exceptions.Timeout:
    # Maybe set up for a retry, or continue in a retry loop
        print("Timeout happened; please retry.")
    except requests.exceptions.TooManyRedirects:
    # Tell the user their URL was bad and try a different one
        print("Too many redirects, bad url?")
    except requests.exceptions.RequestException as e:
        # catastrophic error. Bail.
        raise SystemExit(e)


# writeout setup:

    # build path + filename
    write_out = f'{write_out_location}{filename}.csv'


# zenodo API call setup:

    records_api_url = 'https://zenodo.org/api/records'
    search_query = 'type:software'

    page_iterator = 1

    if verbose:
        print(f'Obtaining {total_records} zenodo record IDs')

# pull out N zenodo record IDs using a records query, paging through until N = page_iterator:

    r = requests.get(
        records_api_url,
        params={'q': search_query, 'all_versions': 'true', 'size': per_pg, 'page': page_iterator}
    )

    try:
        r.status_code != 429
        print(r.status_code)
    except:
        raise requests.exceptions.HTTPError("Rate Limit Exceeded - too many requests.")

    if 'hits' in r.json():
        still_iterating = True
    else:
        still_iterating = False

    identifiers = []

    while still_iterating and (len(identifiers) < total_records):

        r.raise_for_status()

        if 'hits' in r.json():
            for hit in r.json()['hits']['hits']:
                #print(hit['id'])
                #print(type(hit))
                identifiers.append(hit['id'])

        page_iterator += 1

    if verbose:
        print(f'Querying {len(identifiers)} zenodo record IDs')


# Create file connection
    f = open(write_out, 'w')
    writer = csv.writer(f)

    header = ['Zenodo ID', 'Title', 'DOI', 'GitHub Link']
    writer.writerow(header)

# Iterate through identifiers to get gh url info
    record_count = 0

    for record_id in identifiers:
        r = requests.get(f"{records_api_url}/{record_id}")

        if 'metadata' in r.json():

            record_title = r.json()['title']
            record_doi = r.json()['doi']
            record_metadata = r.json()['metadata']

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
                    writer.writerow(row)
                    record_count += 1

            else:
                # print(record_id, record_title)
                continue
        else:
            # print("no metadata")
            continue

    f.close()

    if verbose:
        print(f'Retrieved {record_count} zenodo record github URLs')

    if verbose:
        print(f'file saved out as: {write_out} at {write_out_location}')

    #return(write_out)  # write_out filename and path.
