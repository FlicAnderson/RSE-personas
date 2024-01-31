""" Get GitHub urls from metadata of existing zenodo software record IDs."""

import sys
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
    writeable_chunk = {'ZenodoID': [], 
           'Title': [], 
           'DOI': [], 
           'GitHubURL':[], 
           'CreatedDate': []
    }
    

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

    writeable_chunk = []

    # this loop splits the zenodo IDs into 3x batches of size 10 and returns ephemeral 
    for i in chunker(zenodo_ids['zenodo_id'], batch_size):
        writeable_chunk_ids = i.to_list()  # pull IDs into a list of size 10 in this iteration of the loop
        print(writeable_chunk_ids)
        print(f"This is the 3rd item of this chunk: {writeable_chunk_ids[2]}")  # print 3rd item of this chunk; remember it's 0-based index


    # rate handling setup  

    # zenodo API call setup  

    # 'gatherer' variables setup   

    # API queries loop 

    # write out 'completed' chunks to csv via APPEND 
    # convert to pandas dataframe format  
    #writeable_chunk_df = pd.DataFrame(writeable_chunk)
    
    # append df to csv file  
    #writeable_chunk_df.to_csv(write_out, mode='a', index=False, header=False)

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