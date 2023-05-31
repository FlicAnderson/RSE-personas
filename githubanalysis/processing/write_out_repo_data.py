""" Takes pd.DataFrame repo dataset (e.g. issues data) and writes out to file. ."""
import pandas as pd
import json
from re import sub

def write_out_repo_data(repo_data_df, repo_name, filename='all_issues', write_out_as='json', write_out_location='.', write_orientation='columns', verbose=True):
    """
    Takes pd.DataFrame repo dataset (e.g. issues data) and writes out to file.
    :param repo_data_df: pd.DataFrame containing data for given repo `repo_name`.
    :type str:
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type str:
    :param filename: name to include in write out filename.
    :type str:
    :param write_out_as: Format to write out as. Default: json.
    :type str:
    :param write_out_location: Desired file location path as string. Default = "." (current directory)
    :type str:
    :param write_orientation: Orientation option for writing out data (if write_out_as='json', this follows 'orient' param options in pd.DataFrame.to_json() https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html. If 'csv', default csv methods apply.)
    :type str:
    :param verbose: whether to print out file information. Default: True
    :type bool:
    :returns: ???
    :type DataFrame:

    Examples:
    ----------
    TODO.
    """


    # verify input is df
    if not isinstance(repo_data_df, pd.DataFrame):
        raise TypeError('Ensure input data is pd.DataFrame format.')

    # check there's a repo_name
    if repo_name == None:
        raise ValueError('repo_name must be supplied for filename.')
    if not isinstance(repo_name, str):
        raise ValueError('repo_name must be a string.')

    # parse & check file write out location
        # check it's not empty
        # check it's valid and exists.


    # which method:
    if write_out_as not in ('json', 'csv'):
        raise ValueError('write_out_as must be one of "csv" or "json".')

    if write_out_as == 'json':
        print("yep")

        # create filename from repo_name
        #filename = sub(r"(_|/|-)+", " ", repo_name).title().replace(" ", "")  # overly complex tbh
        filename_repo_name = repo_name.replace("/", "")
        print(filename_repo_name)
        write_out_filename = f'{filename}_{repo_name.replace("/", "")}'
        print(write_out_filename)
        # parse & check

        #repo_data_df.to_json(path_or_buf=write_out_location, orient=write_orientation)

        #if verbose:
        #    print(f'file saved out as: {filename} at {write_out_location}')