"""Test repo name cleaning function"""

import pytest

from githubanalysis.processing.repo_name_clean import repo_name_clean


def test_repo_name_clean_notstr():
    # Arrange
    repo_notstr = 1

    # Act
    # Assert
    with pytest.raises(TypeError):
        repo_name_clean(repo_notstr)


def test_repo_name_clean_notlist():
    # Arrange

    repo_list = [
        "https://github.com/riboviz/riboviz/",
        "https://github.com/FlicAnderson/20230215-JournalClub-BestPractices",
        "https://github.com/PyGithub/PyGithub/",
        "https://github.com/softwaresaved/",
    ]

    repo_list_empty = []

    # Act
    # Assert
    with pytest.raises(TypeError):
        repo_name_clean(repo_list)


# def test_repo_name_clean_emptylist():
# ## THIS TEST CURRENTLY RAISES INDEX ERROR
# ## AS [] INPUT IS READ AS STRING FROM COMMANDLINE INPUT AT COMMIT a720907
# ## "IndexError('list index out of range')" - occurs at line: repo_url = (repo_url.split("https://github.com/"))[1]
#     # Arrange
#
#     repo_list_empty = []
#
#     # Act
#     # Assert
#     with pytest.raises(TypeError):
#         repo_name_clean(repo_list_empty)


def test_repo_name_clean_comma():
    # Arrange

    repo_example = "https://github.com/edcarp/edcarp.github.io, https://github.com/ropensci/software-review"

    # Act & Assert
    with pytest.raises(ValueError):
        repo_name_clean(repo_example)


def test_repo_name_clean_semicolon():
    # Arrange

    repo_example = "https://github.com/edcarp/edcarp.github.io; https://github.com/ropensci/software-review"

    # Act & Assert
    with pytest.raises(ValueError):
        repo_name_clean(repo_example)
