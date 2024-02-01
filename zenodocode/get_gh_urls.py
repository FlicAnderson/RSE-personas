""" Get GitHub urls from metadata of existing zenodo software record IDs read in from csv file."""

import sys
import os
import requests
from requests.adapters import HTTPAdapter, Retry
import pandas as pd
import logging
import math
from datetime import datetime

def chunker(seq, size):
    for pos in range(0, len(seq), size):
        yield seq.iloc[pos:pos + size] 
# via Andrei Krivoshei at SO: https://stackoverflow.com/a/61798585  

def get_gh_urls(config_path='zenodococode/zenodoconfig.cfg', in_filename='zenodo_ids', read_in_location='data/', out_filename='gh_urls', write_out_location='data/', verbose=True):
    """
    Read in csv of zenodo record IDs for software records and query; pull out GitHub urls from metadata; 
    save these records out into a csv file and return all records in a dataframe.
    Logging output to file get_gh_urls_logs.txt
    
    :param config_path: file path of zenodoconfig.cfg file. Default=zenodocode/zenodoconfig.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=20.
    :type: int
    :param total_records: total number of zenodo records to iterate through to pull github URLS from if present. Default=100.
    :type: int
    :param in_filename: name of CSV file to read in, excluding file extension. Default = "zenodo_ids". This can be provided at commandline 
    :type: str
    :param read_in_location: path of zenodo IDs file as string. Default = "data/"
    :type: str
    :param out_filename: name to include in write out filename. Saves as CSV.
    :type: str
    :param write_out_location: desired file location path as string. Default = "data/"
    :type: str
    :param verbose: whether to print out issue data dimensions and counts. Default: True
    :type: bool
    :returns: gh_urls_df - a pd.DataFrame of github url records from zenodo and their metadata in columns: index, ZenodoID, Title, DOI, GitHubURL, CreatedDate.
    :type: pd.DataFrame

    Examples:
    ----------
$ python zenodocode/get_gh_urls.py data/zenodo_ids.csv

python zenodocode/get_gh_urls.py data/zenodo_ids_x1000_2024-02-01.csv
Using commandline argument data/zenodo_ids_x1000_2024-02-01.csv as input file of Zenodo IDs to retrieve GH URLs for.
>> Running loop/chunk number 1 of 100 ...
>> Running loop/chunk number 2 of 100 ...
# ...
>> Running loop/chunk number 99 of 100 ...
>> Running loop/chunk number 100 of 100 ...
There are 768 records with github urls, out of 1000 records in total; saved out to data/gh_urls..
GitHub URL grab complete.

$ python zenodocode/get_gh_urls.py 
# this uses default filename for input file
>>>> Running loop/chunk number 1 of 3:
>>>> Running loop/chunk number 2 of 3:
>>>> Running loop/chunk number 3 of 3:
There are 26 records with github urls, out of 30 records in total; saved out to data/gh_urls.csv.
GitHub URL grab complete.
    """

    # write logs to file: 
    # NOTE: this appends logs to same file for multiple runs. To overwrite, specify: filemode='w' in logging.basicConfig()
    logging.basicConfig(level=logging.DEBUG,
                        filename='logs/get_gh_urls_logs.txt', 
                        encoding='utf-8',
                        format='[%(asctime)s] %(levelname)s:%(message)s')

    # read-in file setup (accept commandline input for zenodo_ids file if any) 
    if len(sys.argv) == 2:
        zenodo_file = sys.argv[1]  # use second argv (user-provided by commandline)

        if not isinstance(zenodo_file, str):
            raise TypeError("Ensure argument is a file location and name in string format (e.g. 'data/zenodo_id.csv')")

        print(f"Using commandline argument {zenodo_file} as input file of Zenodo IDs to retrieve GH URLs for.")
        logging.info(f"Using commandline argument {zenodo_file} as input file of Zenodo IDs to retrieve GH URLs for. Entered as: {sys.argv[1]}")
    else: 
        # default location: data/zenodo_ids.csv 
        zenodo_file = f"{read_in_location}{in_filename}.csv"

    # write-out file setup     
     # get date for generating extra filename info
    current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
    write_out = f'{write_out_location}{out_filename}'
    write_out_extra_info = f"{write_out}_{current_date_info}.csv"   
    
    # read in CSV file of zenodo IDs  
    zenodo_ids = pd.read_csv(zenodo_file, header=None, names=['index', 'zenodo_id'], dtype='Int64')
    
    batch_size = 10
    total_records = len(zenodo_ids.index)
    num_batches = math.ceil(total_records/batch_size) # 3
    logging.info(f"\n ... STARTING RUN. Read in file {zenodo_file} of shape {zenodo_ids.shape}; Number of record IDs to process is {total_records}; Batch size is set to {batch_size}; This run requires {num_batches} batches ... \n")

    # rate handling setup  
    s = requests.Session()
    retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    # 'gatherer' variables setup   
    record_count = 0 # counts records with github urls
    id_count = 0
    loop_num = 0 # counts current 'chunk' loop
    gh_urls_df = pd.DataFrame()  # create empty df to hold complete record set  

    # this loop splits the zenodo IDs into 3x batches of size 10 and returns ephemeral 
    for i in chunker(zenodo_ids['zenodo_id'], batch_size):
        loop_num += 1
        logging.info(f"\n >> Running loop/chunk number {loop_num} of {num_batches} ... ")
        writeable_chunk = [] # reset to empty the dict of previous records
        writeable_chunk_ids = i.to_list()  # pull IDs into a list of size 10 in this iteration of the loop
        print(f">> Running loop/chunk number {loop_num} of {num_batches} ...")

        for record_id in writeable_chunk_ids:
            id_count += 1
            logging.info(f"Running loop for record ID {record_id}, in loop {loop_num}, ID count {id_count} of {total_records}")

            # API queries loop #
            try:
                # zenodo API query created 
                records_api_url = 'https://zenodo.org/api/records'
                record_query_url = f"{records_api_url}/{record_id}"

                api_response = s.get(url=record_query_url, timeout=10)
                logging.info(f"For record ID {record_id}, API response is {api_response}; with rate limit remaining: {api_response.headers['x-ratelimit-remaining']}")

                if 'metadata' in api_response.json():
                    # API tag info via https://developers.zenodo.org/#representation at 12 Dec 2023.
                    record_title = api_response.json()['title']  # (string) Title of deposition (automatically set from metadata).
                    record_created = api_response.json()['created']  # (timestamp) Creation time of deposition (in ISO8601 format)
                    record_doi = api_response.json()['doi']  # (string) Digital Object Identifier (DOI) ... only present for published depositions
                    record_metadata = api_response.json()['metadata']  # (object) deposition metadata resource

                    if 'related_identifiers' in record_metadata:
                        record_metadata_identifiers = api_response.json()['metadata']['related_identifiers']

                        if ("github.com" in record_metadata_identifiers[0]['identifier']) & (
                                "url" in record_metadata_identifiers[0]['scheme']):

                            # get the github url!
                            record_gh_repo_url = record_metadata_identifiers[0]['identifier']

                            # collate items into a dictionary for this record ID
                            row_dict = {
                                'ZenodoID': record_id, 
                                'Title': record_title, 
                                'DOI': record_doi, 
                                'GitHubURL':record_gh_repo_url, 
                                'CreatedDate': record_created
                            }
                            #print(f"{record_id}; {record_title}; {record_created}; {record_doi}; {record_gh_repo_url}")   
                            # add this completed 'row' to the chunk
                            writeable_chunk.append(row_dict)
                            logging.info(f"At (including) ID count {id_count} there have been {record_count} github urls records located so far.")
                            record_count += 1    
            # handle errors
            except TypeError as e_type:
                logging.debug(f"Type error going on: {e_type}")
            except Exception as e:
                if verbose:
                    print(f"API response fail exception for {record_id}: {e}")
                print(type(e))
                print(e)

        # convert to pandas dataframe format  
        writeable_chunk_df = pd.DataFrame.from_dict(writeable_chunk)
        if verbose: 
            print("writeable chunk dataframe vvvv")
            print(writeable_chunk_df)


        # write out 'completed' chunk df content to csv via APPEND (use added date filename)
        writeable_chunk_df.to_csv(write_out_extra_info, mode='a', index=False, header= not os.path.exists(write_out_extra_info))

        # add the completed chunk of df to a 'total' df:
        gh_urls_df = pd.concat([gh_urls_df, writeable_chunk_df], )

    print(f"There are {record_count} records with github urls, out of {total_records} records in total; saved out to {write_out_extra_info}.")
    logging.info(f"\n ... ENDING RUN. There are {record_count} records with github urls, out of {total_records} records in total; saved out to {write_out_extra_info}.")
    
    # report on status  
    if record_count >= (total_records/2): 
        logging.info("More than half of records have GitHub urls. Nice. ")
    else: 
        logging.info("Less than half of records have GitHub urls... Something could be wrong?")  

    # return complete set of github url records as a dataframe 
    return(gh_urls_df)


def main():
    """
    get zenodo software IDs
    write these to csv file
    read csv file back in
    """
    # returns dataframe and saves to variable
    gh_urls_df = get_gh_urls(config_path='zenodococode/zenodoconfig.cfg', in_filename='zenodo_ids', read_in_location='data/', out_filename='gh_urls', write_out_location='data/', verbose=False)
    
    # read in complete dataset as separate variable
    current_date_info = datetime.now().strftime("%Y-%m-%d") # run this at start of script not in loop to avoid midnight/long-run issues
    gh_urls_file = "data/gh_urls.csv"
    gh_urls_file_extra_info = f"{gh_urls_file}_{current_date_info}.csv"
    total_urls = pd.read_csv(gh_urls_file_extra_info, header=0)

    if len(gh_urls_df) != 0:
        print(f"GitHub URL grab complete.")
    else: 
        print("GitHub URL grab did not work, length of records returned is zero.")

    # if everything is good, this shouldn't trigger.
    assert len(gh_urls_df.index) == len(total_urls.index), f"WARNING! Lengths of returned df ({len(gh_urls_df)}) vs df read in from file ({len(total_urls)}) DO NOT MATCH. Did you append too many records to the gh_urls file??"


# this bit
if __name__ == "__main__":
    main()