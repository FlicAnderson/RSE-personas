""" Test function for writing dataframes of data from a given GitHub repo to a file. """

import pytest
import pandas as pd
from pandas.errors import EmptyDataError
from pathlib import Path
import githubanalysis.processing.get_all_pages_issues as issuepages
import githubanalysis.processing.write_out_repo_data as writeout

repo_name_1 = "cooltestusername/coollongunseparatedreponame"
repo_name_2 = "cooltestusername/dash-separated-repo-name"
repo_name_3 = "cooltestusername/camelCaseRepoName"
repo_name_4 = "cooltestusername/repowith.dot"

filename_1 = "all_issues"
filename_2 = "repo_info"
filename_3 = "2023-06-21-datedfilename"
filename_4 = "20230621datedfilename"


#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_empty_df():
    # test what happens writing out an empty df.

    empty_df = pd.DataFrame({'A':[]})

    with pytest.raises(EmptyDataError):
        writeout.write_out_repo_data(repo_data_df=empty_df, repo_name=repo_name_1, filename=filename_1)


#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_write_out_reversible():
    # tests that df object written out can be read in and retain same data structure as initial object


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_filename_correct():
    # test that file is created with name as expected
    # test with repo names including dashes, dots, spaces.
    # given a filename, repo_name, does actual filename match?





# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_filetype_json():
    # test json file is created if write_out_as='json'.

# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_filetype_json():
    # test json file is created if write_out_as='json'.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_write_out_location():
    # test that file is created at expected location.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_write_orientation_json():
    # test that the data structure written out is as expected when set using 'write_orientation' param
    # test for json files.

# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_write_orientation_json():
    # test that the data structure written out is as expected when set using 'write_orientation' param
    # test for json files.
    