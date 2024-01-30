""" Get all zenodo record IDs for software records."""
import sys
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd

def get_software_ids(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=10000, filename='zenodo_ids', write_out_location='data/', verbose=True):
    """
    Get zenodo record IDs for software records and save these out into a csv file.
    NOTE: this code overwrites an existing csv of the same name. 

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
    API response status "OK": <Response [200]>
    Querying 3 zenodo record IDs
    [32712, 6477900, 5899728]
    Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.

    $ python zenodocode/get_software_ids.py 10

    Using commandline argument 10 as number of software IDs to get from zenodo.
    Obtaining 10 zenodo record IDs
    API response status "OK": <Response [200]>
    Querying 10 zenodo record IDs
    [32712, 6477900, 5899728, 3608671] ...
    Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.

    $ python zenodocode/get_software_ids.py
    Obtaining 10000 zenodo record IDs
    API response status "OK": <Response [200]>
    Querying 10000 zenodo record IDs
    [32712, 6477900, 5899728, 3608671] ...
    Zenodo software IDs saved out as: data/zenodo_ids.csv at data/
    Record ID grab complete.
    """

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

    # run API request 
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

    if api_response.status_code == 200 and verbose:
        print(f'API response status "OK": {api_response}')

    # pull out N zenodo record IDs json response, paging through until N = page_iterator:
        try:
            if 'hits' in api_response.json():
                still_iterating = True
            else:
                still_iterating = False
                        
            identifiers = []            

            while still_iterating and (len(identifiers) < total_records):

                if 'hits' in api_response.json():
                    for hit in api_response.json()['hits']['hits']:
                        identifiers.append(hit['id'])

                
                if api_response.status_code == 200 and verbose:
                    print(f'API response status still "OK": {api_response}')

                page_iterator += 1

            if verbose:
                print(f'Querying {len(identifiers)} zenodo record IDs')
                if len(identifiers) > 5: 
                    print(f"{identifiers[0:4]} ...")
                else:
                    print(identifiers)

            # check there are no duplicates in list 
            if len(set(identifiers)) == len(identifiers): 
                print("Gathered record IDs all unique")
            else: 
                print("ERROR: Gathered record IDs contain duplicates!")  

            # convert to pandas dataframe for ease of use and write out to csv  
            software_ids = pd.DataFrame(identifiers)
            software_ids.to_csv(write_out, index=False, header=["zenodo_id"])

            if verbose:
                print(f'Zenodo software IDs saved out as: {write_out} at {write_out_location}')

        finally:
            return(software_ids)



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