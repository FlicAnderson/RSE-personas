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


@pytest.fixture
def get_code_reviews():
    logger = loggit.get_default_logger(
        console=True,
        set_level_to="INFO",
        log_name="tests/testing_get_all_PR_code_reviews_logs.txt",
        in_notebook=False,
    )
    getting_code_reviews = GetCodeReviews(
        config_path="githubanalysis.config.cfg", in_notebook=False, logger=logger
    )
    getting_code_reviews.data_location = Path("tests/testdata")
    return getting_code_reviews


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
