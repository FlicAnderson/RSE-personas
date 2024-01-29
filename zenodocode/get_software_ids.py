""" Get all zenodo record IDs for software records."""

import requests
from requests.adapters import HTTPAdapter, Retry
import csv
import pandas as pd

def get_software_ids(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=100, filename='zenodo_ids', write_out_location='data/', verbose=True):
    """
    Get zenodo record IDs for software records and save these out into a csv file.

    :param config_path: file path of zenodoconfig.cfg file. Default=zenodocode/zenodoconfig.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=20.
    :type: int
    :param total_records: Total number of zenodo records to iterate through. Default=100.
    :type: int
    :param filename: name to include in write out filename. Saves as CSV.
    :type: str
    :param write_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param verbose: whether to print out issue data dimensions and counts. Default: True
    :type: bool
    :returns: software_ids
    :type: list of integers

    Examples:
    ----------
    TODO.
    """


    # writeout setup:
      # build path + filename
    write_out = f'{write_out_location}{filename}.csv'


    # handle API responses:
      # approach via: https://stackoverflow.com/a/35636367
      # zenodo API call setup:

    records_api_url = 'https://zenodo.org/api/records'
    search_query = 'type:software'

    page_iterator = 1

    if verbose:
        print(f'Obtaining {total_records} zenodo record IDs')


# pull out N zenodo record IDs using a records query, paging through until N = page_iterator:

    #if verbose:
    #    logging.basicConfig(level=logging.DEBUG)  # might be able to remove this as it doesn't affect the requests code

    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
#
    api_response = s.get(
        records_api_url,
        #headers = headers_list,
        params={
            'q': search_query, 
            'all_versions': 'false', 
            'size': per_pg, 
            'page': page_iterator
        },
        timeout=10
    )

    headers_out = api_response.headers
    print(headers_out)
    print(f"record ID request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}")
    #headers_retry-after = api_response.headers['retry-after']
    #print(type(headers_out))

    #print(headers_out.get('x-ratelimit-limit'))
    #headers_ratelimit-remaining = r.headers.['x-ratelimit-remaining']  # e.g. 'x-ratelimit-remaining': '132'
    #headers_ratelimit-reset = r.headers['x-ratelimit-reset']  # e.g. 'x-ratelimit-reset': '1702408561'
#    headers_retry-after = api_response.headers['retry-after']
    
    #f = open(write_out, 'w')
    #writer = csv.writer(f)

    #header = 'Zenodo ID'
    #writer.writerow(header)


    if api_response.status_code == 200 and verbose:
        print(f'API response status "OK": {api_response}')

        try:
            # pull data as json then convert to pandas dataframe for ease of use
            #software_ids = api_response.json()
            if 'hits' in api_response.json():
                still_iterating = True
                print("has hits")
            else:
                still_iterating = False
                        
            identifiers = []            

            while still_iterating and (len(identifiers) < total_records):

                if 'hits' in api_response.json():
                    for hit in api_response.json()['hits']['hits']:
                        print(hit['id'])
                    #print(type(hit))
                        identifiers.append(hit['id'])

                page_iterator += 1

            if verbose:
                print(f'Querying {len(identifiers)} zenodo record IDs')
                print(identifiers)

            print(len(identifiers))
            print(type(identifiers))
            #print(identifiers)

            identifiers = pd.DataFrame(identifiers)
            identifiers.to_csv(write_out, index=False, header=["zenodo_id"])

        finally:
            #f.close()
            return(identifiers)




def main():
    """
    get zenodo software IDs
    TODO write these to csv file
    """
    software_ids = []

    software_ids = get_software_ids(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=10000, filename='zenodo_ids', write_out_location='data/', verbose=True)
    
    if len(software_ids) != 0:
        print("record ID grab complete")
    else: 
        print("this did not work.")


# this bit
if __name__ == "__main__":
    main()