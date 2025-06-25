"""Test PR code-review data gathering functions."""

from pathlib import Path
import utilities.get_default_logger as loggit
import pytest
from githubanalysis.processing.get_all_PR_code_reviews import GetCodeReviews

# def test_function():
#     # Arrange:

#     # Act:

#     # Assert:

# LIST OF TEST REPOS TO TEST WITH
# SET WRITEOUT LOCATION ETC TO TESTDATA FOLDER INSTEAD OF DATA FOLDER.

expected_file_repos = [
    "KislakCenter/VisColl",
    "LABSN/expyfun",
    "SyneRBI/SIRF-SuperBuild",
    "avaframe/AvaFrame",
    "cookiejar/cookietemple",
    "genomeannotation/GAG",
    "gher-uliege/DIVAnd.jl",
    "gwdetchar/gwdetchar",
    "qbic-pipelines/rnadeseq",
    "ubermag/mag2exp",
    "ubermag/micromagneticmodel",
    "ubermag/ubermagtable",
    "FlicAnderson/thisrepodoesnotexist",  # repo which does not exist (not last, testing continuation at error)
    "FlicAnderson/peramagroon",  # repo without PRs
]
expected_sorted_file_repos = list(sorted(expected_file_repos))


@pytest.fixture
def get_code_reviews():
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="INFO",
        log_name="tests/testing_get_all_PR_code_reviews_logs.txt",
        in_notebook=False,
    )
    getting_code_reviews = GetCodeReviews(
        config_path="githubanalysis/config.cfg", in_notebook=False, logger=logger
    )
    getting_code_reviews.data_location = Path("tests/testdata")
    return getting_code_reviews


def test_getting_repo_names_from_file(get_code_reviews):
    repos = get_code_reviews.get_repos(
        repo_list_file_name=Path("code_review_subset_2025-05-30_x12.txt")
    )
    repos.sort()  # sorts in-place.

    assert (
        repos == expected_sorted_file_repos
    ), "Sorted list of repos does not match sorted expected list."


def test_API_pulls_query_assembly(get_code_reviews):
    # test that for given repo_name, API query is correctly assembled...
    repo_name = expected_file_repos[0]  # KislakCenter/VisColl

    pulls_qry = get_code_reviews.make_pulls_query_url(
        repos_api_url="https://api.github.com/repos/",
        repo_name=repo_name,
        per_pg=100,
        page=1,
    )
    expected_qry = (
        "https://api.github.com/repos/KislakCenter/VisColl/pulls?per_page=100&page=1"
    )
    assert (
        pulls_qry == expected_qry
    ), f"generated API query {pulls_qry} does not match expected result {expected_qry}."


def test_no_PRs_repo(get_code_reviews):
    # test what happens if there's no PRs for that repo at all
    pass


def test_get_all_code_reviews_no_reviews_exist(get_code_reviews):
    # PRs exist, but no reviews.
    pass


def test_get_all_code_reviews_no_PRs_exist(get_code_reviews):
    # no PRs for this repo, therefore no code reviews on them.
    pass


def test_get_all_code_reviews_happy_case_one(get_code_reviews):
    # happy case: PRs exist, 1 code review exists, treated correctly
    pass


def test_get_all_code_reviews_happy_case_multiple(get_code_reviews):
    # happy case: PRs exist, several code reviews exist, treated correctly
    pass


def test_get_all_code_reviews_integration_test(get_code_reviews):
    # happy case: PRs exist, > 1 code reviews exist, treated correctly
    # BUT then combined with commits, issues, timestamp data correctly for analysis.
    pass
