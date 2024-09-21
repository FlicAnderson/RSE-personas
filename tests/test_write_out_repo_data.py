"""Test function for writing dataframes of data from a given GitHub repo to a file."""

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
repo_name_5 = "riboviz/riboviz"

filename_1 = "all_issues"
filename_2 = "repo_info"
filename_3 = "2023-06-21-datedfilename"
filename_4 = "20230621datedfilename"


def read_write_samples(repo_name_5=repo_name_5):
    # setup function for testing.
    # big function of setup stuff for testing various parts of the code.
    # TODO: find 'more pytest' way of doing this?
    all_issues = issuepages.get_all_pages_issues(
        repo_name=repo_name_5,
        config_path="githubanalysis/config.cfg",
        per_pg=100,
        issue_state="all",
        verbose=True,
    )  # get all issues from all pages for given repo

    # write out issues data to file and return/save filename and path to write_out object
    write_out = writeout.write_out_repo_data(
        repo_data_df=all_issues,
        repo_name=repo_name_5,
        filename="all_issues",
        write_out_as="json",
        write_out_location="data/",
        write_orientation="table",
        verbose=True,
    )

    write_out = Path(write_out)

    read_in_df = pd.read_json(
        path_or_buf=write_out,
        orient="table",
        typ="frame",
        dtype=None,
        convert_dates=False,
        keep_default_dates=False,
        precise_float=False,
        date_unit="s",
    )
    # check dates aren't borked up because there's conversions possible in the to_json() and read_json() functions.

    # create 5% sample dfs from post-read_in df for comparison:
    read_in_sample = read_in_df.sample(
        frac=0.05,
        replace=False,
        weights=None,
        random_state=25,
        axis="index",
        ignore_index=True,
    )

    # create 5% sample dfs from all_issues pre-write-out df and post-read_in df for comparison:
    write_out_sample = all_issues.sample(
        frac=0.05,
        replace=False,
        weights=None,
        random_state=25,
        axis="index",
        ignore_index=True,
    )

    return (all_issues, write_out, read_in_df, read_in_sample, write_out_sample)


@pytest.fixture()
def empty_df():
    empty_df = pd.DataFrame({"A": []})
    return empty_df


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_empty_df(empty_df):
    # test what happens writing out an empty df.

    with pytest.raises(EmptyDataError):
        writeout.write_out_repo_data(
            repo_data_df=empty_df, repo_name=repo_name_1, filename=filename_1
        )


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_file_created():
    # test that file is created exists at expected location with name as expected

    # get write_out as the 2nd returned object from read_write_samples() setup function
    write_out = read_write_samples(repo_name_5=repo_name_5)[1]

    assert Path(write_out).is_file()


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_url():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["url"].equals(
        write_out_sample["url"]
    ), "Sampled urls do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_repo_url():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["repository_url"].equals(
        write_out_sample["repository_url"]
    ), "Sampled repository_urls do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_id():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["id"].equals(
        write_out_sample["id"]
    ), "Sampled ids do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_number():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["number"].equals(
        write_out_sample["number"]
    ), "Sampled numbers do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_title():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["title"].equals(
        write_out_sample["title"]
    ), "Sampled titles do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_state():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["state"].equals(
        write_out_sample["state"]
    ), "Sampled states do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_assignees():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["assignees"].equals(
        write_out_sample["assignees"]
    ), "Sampled assignees do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_created_at():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["created_at"].equals(
        write_out_sample["created_at"]
    ), "Sampled created_at dates do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_closed_at():
    # tests that df object written out can be read in and retain same data structure as initial object
    # # test values for important columns match from random samples of pre-write all_issues and read-in data:

    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()
    read_in_sample = read_write_samples(repo_name_5=repo_name_5)[3]
    write_out_sample = read_write_samples(repo_name_5=repo_name_5)[4]

    assert read_in_sample["closed_at"].equals(
        write_out_sample["closed_at"]
    ), "Sampled closed_at dates do not match"


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_write_out_reversible_df_shape():
    # tests that df object written out can be read in and retain same data structure as initial object
    # get read_in_sample and write_out_sample as the 3rd and 4th returned objects from read_write_samples()

    all_issues = read_write_samples(repo_name_5=repo_name_5)[0]
    read_in_df = read_write_samples(repo_name_5=repo_name_5)[2]

    assert all_issues.shape == read_in_df.shape


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_file_schema_matches():
# confirm that schema of json or csv file matches that of the written-out schema (and ideally the GH-pulled data).


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_filename_correct():
# test that file is created with name as expected
# test with repo names including dashes, dots, spaces.
# given a filename, repo_name, does actual filename match?


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_filetype_json():
# test json file is created if write_out_as='json'.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_filetype_json():
# test json file is created if write_out_as='json'.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_write_out_location():
# test that file is created at expected location.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_write_orientation_json():
# test that the data structure written out is as expected when set using 'write_orientation' param
# test for json files.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_write_orientation_json():
# test that the data structure written out is as expected when set using 'write_orientation' param
# test for json files.
