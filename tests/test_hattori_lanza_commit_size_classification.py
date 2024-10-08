import pytest
from githubanalysis.analysis.hattori_lanza_commit_size_classification import (
    hattori_lanza_commit_size_classification,
)

from typing import cast


def test_hattori_lanza_commit_size_classification_exceptions():
    """
    Testing of hattori lanza size categorisation function for commits.
    """
    commit_float = cast(int, 0.6)
    commit_negative = -1
    commit_emptystr = cast(int, "")

    with pytest.raises(Exception):
        hattori_lanza_commit_size_classification(commit_size=commit_float)

    with pytest.raises(Exception):
        hattori_lanza_commit_size_classification(commit_size=commit_emptystr)

    with pytest.raises(Exception):
        hattori_lanza_commit_size_classification(commit_size=commit_negative)


def test_hattori_lanza_commit_size_classification_zeroes():
    assert hattori_lanza_commit_size_classification(0) is None


def test_hattori_lanza_commit_size_classification_none():
    assert hattori_lanza_commit_size_classification(None) is None


def test_hattori_lanza_commit_size_classification_tiny():
    assert hattori_lanza_commit_size_classification(1) == "tiny"
    assert hattori_lanza_commit_size_classification(5) == "tiny"


def test_hattori_lanza_commit_size_classification_small():
    assert hattori_lanza_commit_size_classification(6) == "small"
    assert hattori_lanza_commit_size_classification(25) == "small"


def test_hattori_lanza_commit_size_classification_medium():
    assert hattori_lanza_commit_size_classification(26) == "medium"
    assert hattori_lanza_commit_size_classification(125) == "medium"


def test_hattori_lanza_commit_size_classification_large():
    assert hattori_lanza_commit_size_classification(126) == "large"
    assert hattori_lanza_commit_size_classification(100000) == "large"
    assert hattori_lanza_commit_size_classification(100000000000) == "large"
