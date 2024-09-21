""" Takes pd.DataFrame repo dataset (e.g. issues data) and writes out to file. ."""
import pandas as pd
from pandas.errors import EmptyDataError


def write_out_repo_data(repo_data_df, repo_name, filename='all_issues',
                        write_out_as='json', write_out_location='data/',
                        write_orientation='table', verbose=True):
    """
    Takes pd.DataFrame repo dataset (e.g. issues data) and writes out to file.
    :param repo_data_df: pd.DataFrame containing data for given repo `repo_name`.
    :type: str
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param filename: name to include in write out filename.
    :type: str
    :param write_out_as: Format to write out as. Default: json.
    :type: str
    :param write_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param write_orientation: Orientation option for writing out data.
    (json) Default = 'table' includes schema and type info with 'pandas_version' included.
    If write_out_as='json', follows 'orient' param options in pd.DataFrame.to_json()
    https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html.
    If 'csv', default csv methods apply.
    :type: str
    :param verbose: whether to print out file information. Default: True
    :type: bool
    :returns write_out_filepath: This is the path and filename to which the file has been written out.
    :type: str/path

    NB: this conversion escapes all slashes in the urls so resulting file looks intense.

    TODO: write out and read in datatypes explicitly!
        - milestone, active_lock_reason and performed_via_github_app are shifted to float64
        - these are all 'string' in the written-out json file, and read in as float64. :s

    Examples:
    ----------
    TODO.
    """

    # verify input is df
    if not isinstance(repo_data_df, pd.DataFrame):
        raise TypeError('Ensure input data is pd.DataFrame format.')

    if repo_data_df.empty is True:
        raise EmptyDataError('There is no data in dataframe repo_data_df.')

    # check there's a repo_name
    if repo_name is None:
        raise ValueError('repo_name must be supplied for filename.')
    if not isinstance(repo_name, str):
        raise ValueError('repo_name must be a string.')

    # parse & check file write out location
        # check it's not empty
        # check it's valid and exists.

    # create filename from repo_name
    write_out_filename = f'{filename}__{repo_name.replace("/", "_")}'
    print(write_out_filename)

    # build path + filename + file extension string
    write_out = f'{write_out_location}{write_out_filename}.{write_out_as}'

    # which method:
    if write_out_as not in ('json', 'csv'):
        raise ValueError('write_out_as must be one of "csv" or "json".')

    # TODO: write out and read in datatypes explicitly!
    if write_out_as == 'json':
        repo_data_df.to_json(
            path_or_buf=write_out,
            orient=write_orientation,
            date_format='iso',
            date_unit='s',
            index=False,
            indent=4,
        )
        # FYI: json escapes all the slashes in the urls so resulting file looks pretty intense.
        # dates in ISO8601 from github (format: YYYY-MM-DDTHH:MM:SSZ e.g "2011-04-10T20:09:31Z" ie UTC times with extended format w/ ':')

        # milestone, active_lock_reason and performed_via_github_app are shifted to float64
        # these are all 'string' in the written-out json file, and read in as float64. :s

    if verbose:
        print(f'file saved out as: {write_out_filename}.{write_out_as} at {write_out_location}')

    return(write_out)  # write_out filename and path.
