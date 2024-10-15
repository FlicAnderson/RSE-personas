"""Testing for core commits-grab code."""

# import requests
import json

# from githubanalysis.processing.get_all_branches_commits import AllBranchesCommitsGetter

# def test_get_all_branches_commits():
#     # Arrange:

#     # Act:

#     # Assert:

rawjson = "tests/testdata/raw-commits__all-branches-commits_FlicAnderson-peramagroon_2024-10-15.json"
deduplicatedjson = "tests/testdata/deduplicated-commits__all-branches-commits_FlicAnderson-peramagroon_2024-10-15_deduplicated.json"

with open(rawjson) as f1:
    rawjsondata = json.load(f1)
    f1.close

with open(deduplicatedjson) as f2:
    deduplicatedjsondata = json.load(f2)
    f2.close


# def test_get_all_branches_commits_success():
#     # Arrange:

#     # Act:

#     # Assert:
