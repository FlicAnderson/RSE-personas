""" Get GitHub urls from metadata of existing zenodo software record IDs."""

import sys
import os
import requests
from requests.adapters import HTTPAdapter, Retry
import numpy as np
import pandas as pd
import logging
import csv
import math

def chunker(seq, size):
    for pos in range(0, len(seq), size):
        yield seq.iloc[pos:pos + size] 
# via Andrei Krivoshei at SO: https://stackoverflow.com/a/61798585  

def get_gh_urls(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=100, filename='gh_urls', write_out_location='data/', verbose=True):
    """
    Read in zenodo record IDs for software records and query; pull out GitHub urls from metadata, saving these out into a csv file.
    Logging output to file get_gh_urls_logs.txt
    
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

    # write logs to file: 
    # NOTE: this appends logs to same file for multiple runs. To overwrite, specify: filemode='w' in logging.basicConfig()
    logging.basicConfig(level=logging.DEBUG,
                        filename='logs/get_gh_urls_logs.txt', 
                        encoding='utf-8',
                        format='[%(asctime)s] %(levelname)s:%(message)s')

    # accept commandline input for zenodo_ids file  
     # default location: data/zenodo_ids.csv  
    
    # write-out file setup
     # default location: data/gh_urls.csv    
     # build path + filename
    write_out = f'{write_out_location}{filename}.csv'
    
    # set format for section of data to write out to csv  

    # read in CSV file of zenodo IDs  
     # default location: data/zenodo_ids.csv 
    zenodo_ids = pd.read_csv('data/zenodo_ids.csv', header=None, names=['index', 'zenodo_id'], dtype='Int64')
    
    # print(zenodo_ids.dtypes)
    # #index        Int64
    # #zenodo_id    Int64
    # #dtype: object
    # print(zenodo_ids.shape)
    # #(30, 2)
    # print(zenodo_ids)
    # #    index  zenodo_id
    # #0       0    6626409
    # #1       1    1283299
    # #2       2      35602
    # #3       3    5179941
    # print(zenodo_ids.columns)
    # #Index(['index', 'zenodo_id'], dtype='object')
    # print(zenodo_ids.take([0]))
    # #   index  zenodo_id
    # #0      0    6626409
    # print(zenodo_ids.zenodo_id[0])
    # #6626409

    # for record in range(len(zenodo_ids)):
    #     print(record)
    #     print(zenodo_ids.zenodo_id[record])
    # #0
    # #6626409
    # #1
    # #1283299

    batch_size = 10
    total_records = 30
    num_batches = math.ceil(total_records/batch_size) # 3
    logging.info(f"Number of records to process is {total_records}; batch size is set to {batch_size}; this requires {num_batches} batches.")

    # rate handling setup  
    s = requests.Session()
    retries = Retry(total=10, connect=5, read=3, backoff_factor=1.5, status_forcelist=[202, 502, 503, 504])
    s.mount('https://', HTTPAdapter(max_retries=retries))

    # 'gatherer' variables setup   
    record_count = 0
    loop_num = 0

    # this loop splits the zenodo IDs into 3x batches of size 10 and returns ephemeral 
    for i in chunker(zenodo_ids['zenodo_id'], batch_size):
        writeable_chunk = []
        loop_num += 1
        writeable_chunk_ids = i.to_list()  # pull IDs into a list of size 10 in this iteration of the loop
        #print(writeable_chunk_ids)
        #print(f"This is the 3rd item of this chunk: {writeable_chunk_ids[2]}")  # print 3rd item of this chunk; remember it's 0-based index

        print(f">>>> Running loop/chunk number {loop_num}:")

        for record_id in writeable_chunk_ids:
            #print(f"record ID {record_id}; {type(record_id)}; {type(writeable_chunk_ids)}")

            # API queries loop #
            try:
                # zenodo API query created 
                records_api_url = 'https://zenodo.org/api/records'
                record_query_url = f"{records_api_url}/{record_id}"

                api_response = s.get(url=record_query_url, timeout=10)
                #headers = api_response.headers
                logging.info(f"For record ID {record_id}, API response is {api_response}") # and headers are {headers}")

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
                            record_count += 1    
            # handle errors
            except TypeError as e_type:
                logging.debug(f"Type error going on: {e_type}")
            except Exception as e:
                if verbose:
                    print(f"API response fail exception for {record_id}: {e}")
                print(type(e))
                print(e)

        # write out 'completed' chunk content to csv via APPEND 
        # convert to pandas dataframe format  
        writeable_chunk_df = pd.DataFrame.from_dict(writeable_chunk)
        print("writeable chunk dataframe vvvv")
        print(writeable_chunk_df)

        # append df to csv file  
        #writeable_chunk_df.to_csv(write_out, mode='a', index=False, header= not os.path.exists(write_out))


    print(f"There are {record_count} records with github urls, out of {total_records} records in total.")

        # report on status  
        # report success/fail  
        #print("Data appended successfully.")



def main():
    """
    get zenodo software IDs
    write these to csv file
    """
    total_urls = []
    total_urls = get_gh_urls(config_path='zenodococode/zenodoconfig.cfg', per_pg=20, total_records=100, filename='gh_urls', write_out_location='data/', verbose=True)
    
    # if len(total_urls) != 0:
    #     print(f"Record ID grab complete.")
    # else: 
    #     print("Record ID grab did not work, length of software_ids returned is zero.")


# this bit
if __name__ == "__main__":
    main()


  







# # Iterate through identifiers to get gh url info
#     record_count = 0

#     for record_id in identifiers:
#         r = requests.get(f"{records_api_url}/{record_id}")

#         headers_out = r.headers
#         print(f"url info request headers limit/remaining: {headers_out.get('x-ratelimit-limit')}/{headers_out.get('x-ratelimit-remaining')}")

#         if 'metadata' in r.json():

#             # API tag info via https://developers.zenodo.org/#representation at 12 Dec 2023.
#             record_title = r.json()['title']  # (string) Title of deposition (automatically set from metadata).
#             record_created = r.json()['created']  # (timestamp) Creation time of deposition (in ISO8601 format)
#             record_doi = r.json()['doi']  # (string) Digital Object Identifier (DOI) ... only present for published depositions
#             record_metadata = r.json()['metadata']  # (object) deposition metadata resource
#             #record_published = r.json()['metadata']['publication_date']  # (string) Date of publication in ISO8601 format (YYYY-MM-DD). Defaults to current date.

#             if 'related_identifiers' in record_metadata:
#                 record_metadata_identifiers = r.json()['metadata']['related_identifiers']

#                 if ("github.com" in record_metadata_identifiers[0]['identifier']) & (
#                         "url" in record_metadata_identifiers[0]['scheme']):

#                     record_gh_repo_url = record_metadata_identifiers[0]['identifier']

#                     row = []
#                     row.append(record_id)
#                     row.append(record_title)
#                     row.append(record_doi)
#                     row.append(record_gh_repo_url)
#                     row.append(record_created)
#                     #row.append(record_published)
#                     writer.writerow(row)
#                     record_count += 1