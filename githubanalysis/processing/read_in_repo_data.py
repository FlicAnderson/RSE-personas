""" Takes file of repo data (e.g. issue data) and reads in to pd.DataFrame. """
import pandas as pd
from pathlib import Path


def read_in_repo_data(read_in, repo_name=None, read_in_as='json', read_orientation='table', verbose=True):
    """
    Takes repo dataset file (e.g. issues data) in json and reads in as pd.DataFrame object.
    :param read_in: filename and filepath for file to read in as dataframe.
    :type: str
    :param repo_name: Optional 'repo_name` string without github url root or trailing slashes. Default: None
    :type: str
    :param read_in_as: File format to read in. Default: json.
    :type: str
    :param read_orientation: Orientation option for writing out data.
    (json) Default = 'table' includes schema and type info with 'pandas_version' included.
    If read_in_as='json', follows 'orient' param options in pd.DataFrame.to_json()
    https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.to_json.html.
    If 'csv', default csv methods apply.
    :type: str
    :param verbose: whether to print out file information. Default: True
    :type: bool
    :returns read_in_df: pd.DataFrame containing data for given repo `repo_name`.
    :type: str
    :returns repo_name: `repo_name` for associated returned dataframe `read_in_df`.
    :type: str

    TODO: give 'csv' read-in option.

    TODO: read in datatypes more explicitly!
        - milestone, active_lock_reason and performed_via_github_app are shifted to float64
        - these are all 'string' in the written-out json file, and read in as float64. :s

    Examples:
    ----------
    TODO.
    """

    # verify input exists; is expected filetype
    # check config filepath input (using separate variable to avoid overwriting it as pathlib Path type)
    read_path = Path(read_in)
    if read_path.exists() is False:
        raise OSError('Read-in file does not exist at path:', read_path)

    if repo_name is None:
        # reverse-create repo_name from filename

        # separate path + filename + file extension string
        #read_in_location = read_path.parent
        read_in_filename = read_path.stem

        repo_name = read_in_filename.split("__")[1]  # e.g. read_in_filename = 'all_issues__riboviz_riboviz' -> ['all_issues', 'riboviz_riboviz']
        repo_name = repo_name.replace('_', '/')  # get back to user/repo format with slashes instead of underscores.

    else:
        repo_name = repo_name  # from function arguments.

    if read_in_as not in ('json', 'csv'):
        raise ValueError('write_out_as must be one of "csv" or "json".')

    if read_in_as == 'csv':
        raise Exception('csv read-in option not written yet.')

    try:

        read_in_df = pd.DataFrame()

        read_in_df = pd.read_json(
            path_or_buf=read_in, orient=read_orientation, typ='frame', dtype=None,
            convert_dates=False, keep_default_dates=False, precise_float=False, date_unit='s'
        )
        # check dates aren't borked up because there's conversions possible in the to_json() and read_json() functions.

        if verbose:
            if read_in_df.empty:  # if read_in hasn't worked and dataframe is empty
                print(f"Dataframe has not read in correctly from file {read_in}.")
            else:
                print(f"Dataframe has been created from file {read_in} for repo {repo_name} and has dimensions: {read_in_df.shape}.")

        return read_in_df, repo_name  # return tuple of dataframe and repo_name

    except:
        raise Exception(f'Reading in file {read_in} from repo {repo_name} did not work.')
        # todo: raise more helpful exception and message on fail.
