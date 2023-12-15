""" Get zenodo records for software and pull out GitHub urls from metadata."""

import requests
import csv
import ratelimit

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

    # specify custom http headers:
    #headers_list={"Content-Type": "application/json", 'user-agent': 'coding-smart/zenodocode'}

    r = requests.get(
        records_api_url,
        #headers = headers_list,
        params={'q': search_query, 'all_versions': 'true', 'size': per_pg, 'page': page_iterator}
    )


    headers_out = r.headers
    print(f"record ID request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}")
    #print(type(headers_out))

    #print(headers_out.get('x-ratelimit-limit'))
    #headers_ratelimit-remaining = r.headers.['x-ratelimit-remaining']  # e.g. 'x-ratelimit-remaining': '132'
    #headers_ratelimit-reset = r.headers['x-ratelimit-reset']  # e.g. 'x-ratelimit-reset': '1702408561'
    #headers_retry-after = r.headers['retry-after']  # e.g. 'retry-after': '53'

    # if verbose:
    #     print(r.headers)
    # else:
    #     print(f"Ratelimit remaining: {headers_ratelimit-remaining}")
    #
    # if headers_ratelimit-remaining < total_records:
    #     print("This request is likely to be ratelimited!")
    # else:
    #     print("Request is within rate limits.")

    try:
        r.status_code != 429
        print(f"API status: {r.status_code}")
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


    print(identifiers)

# Create file connection
    f = open(write_out, 'w')
    writer = csv.writer(f)

    header = ['Zenodo ID', 'Title', 'DOI', 'GitHub Link', 'CreatedDate']
    writer.writerow(header)

# Iterate through identifiers to get gh url info
    record_count = 0

    for record_id in identifiers:
        r = requests.get(f"{records_api_url}/{record_id}")

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
