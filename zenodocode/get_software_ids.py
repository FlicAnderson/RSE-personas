""" Get all zenodo record IDs for software records."""
import sys
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import logging
import math

def get_software_ids(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=10000, filename='zenodo_ids', write_out_location='data/', verbose=True):
    """
    Get zenodo record IDs for software records and save these out into a csv file.
    NOTE: this code overwrites an existing csv of the same name. 
    If verbose = TRUE, logging info is sent to get_software_ids_info_logs.txt file

    :param config_path: file path of zenodoconfig.cfg file. Default=zenodocode/zenodoconfig.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=20.
    :type: int
    :param total_records: Total number of zenodo records to iterate through. Default=10,000.
    :type: int
    :param filename: name to include in write out filename. Saves as CSV.
    :type: str
    :param write_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param verbose: whether to print out issue data details and counts. Default: True
    :type: bool
    :returns: software_ids
    :type: pd.Dataframe of record IDs 

    Examples:
    ----------
    $ python zenodocode/get_software_ids.py 3

    Using commandline argument 3 as number of software IDs to get from zenodo.
    Obtaining 3 zenodo record IDs
    [6567232, 5157894, 5564801]
    Gathered record IDs all unique
    3 Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.

    $ python zenodocode/get_software_ids.py 10

    Using commandline argument 10 as number of software IDs to get from zenodo.
    Obtaining 10 zenodo record IDs
    [6567232, 5157894, 5564801, 6408054] ...
    Gathered record IDs all unique
    10 Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.

    $ python zenodocode/get_software_ids.py 75

    Using commandline argument 75 as number of software IDs to get from zenodo.
    Obtaining 75 zenodo record IDs
    [6567232, 5157894, 5564801, 6408054] ...
    Gathered record IDs all unique
    75 Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.
    """

    # write logs to file: 
    # NOTE: this appends logs to same file for multiple runs. To overwrite, specify: filemode='w' in logging.basicConfig()
    logging.basicConfig(level=logging.DEBUG,
                        filename='logs/get_software_ids_logs.txt', 
                        encoding='utf-8',
                        format='[%(asctime)s] %(levelname)s:%(message)s')

    # get commandline input if any 
    if len(sys.argv) == 2:

        total_records = int(sys.argv[1])  # use second argv (user-provided by commandline)

        if not isinstance(total_records, int):
            raise TypeError('Ensure argument is an integer number.')

        if verbose:
            print(f"Using commandline argument {total_records} as number of software IDs to get from zenodo.")

    # deal with input less than per_page 
    if total_records < per_pg: 
        per_pg = total_records
        logging.info("total_records is less than per_pg; adjusting per_pg to total_records.")
    
    # writeout setup:
      # build path + filename
    write_out = f'{write_out_location}{filename}.csv'

    if verbose:
        print(f'Obtaining {total_records} zenodo record IDs')

    # set up API session details: retry 5 times with a backoff factor
      # approach via: https://stackoverflow.com/a/35636367
    s = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))
    
    records_api_url = 'https://zenodo.org/api/records'
    search_query = 'type:software'
    page_iterator = 1
    identifiers = []   

    requests_needed = math.ceil(total_records/per_pg)
    page_iterator=1

    for calls in range(requests_needed):
        logging.info(f"... page {page_iterator} of {requests_needed}...")
        api_response = s.get(
                records_api_url,
                #headers = headers_list,
                params={
                    'q': search_query, 
                    'all_versions': 'false', 
                    'size': per_pg, 
                    'page': page_iterator
                },
                timeout=10)
        logging.info(f"API response on request {page_iterator}: {api_response}")
        logging.info(f"API rate limit remaining: {api_response.headers['x-ratelimit-remaining']}")

        page = [] # temporary list which holds all IDs from this page of the query
        for hit in api_response.json()['hits']['hits']:
            #print(hit['id'])
            page.append(hit['id'])

        identifiers.extend(page)  # add this page of ids onto main identifiers list    
        page_iterator += 1  # this call loop ends

    # print only a few IDs
    if verbose:
        if len(identifiers) > 5: 
            print(f"{identifiers[0:4]} ...")
        else:
            print(identifiers)

    if len(set(identifiers)) == len(identifiers): 
        print("Gathered record IDs all unique")
        logging.info("Gathered record IDs all unique")
    else: 
        print("Watch out: Gathered record IDs contain duplicates!")
        logging.warning("Gathered record IDs contain duplicates!")
        
    # slice identifiers if it is longer than total_records value (ie total_records=30, per_page=20 => len(identifiers)=40... )
    if len(identifiers) > total_records:
        logging.info(f"Slicing down list of IDs from {len(identifiers)} to {total_records}.")
        identifiers = identifiers[0:total_records]

    if verbose:
        print(f'{len(identifiers)} Zenodo software IDs saved out as: {write_out} at {write_out_location}')
    
    # convert to pandas dataframe for ease of use and write out to csv  
    software_ids_df = pd.DataFrame(identifiers)
    software_ids_df.to_csv(write_out, index=False, header=["zenodo_id"])
    logging.info(f'{len(identifiers)} Zenodo software IDs saved out as: {write_out} at {write_out_location}')

    # return df of IDs
    return(software_ids_df)



def main():
    """
    get zenodo software IDs
    write these to csv file
    """
    software_ids = []
    software_ids = get_software_ids(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=10000, filename='zenodo_ids', write_out_location='data/', verbose=True)
    
    if len(software_ids) != 0:
        print(f"Record ID grab complete.")
    else: 
        print("Record ID grab did not work, length of software_ids returned is zero.")


# this bit
if __name__ == "__main__":
    main()