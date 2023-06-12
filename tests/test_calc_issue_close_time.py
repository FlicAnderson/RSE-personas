""" Test function for calculating issue close times. """

#import pytest
#import pandas as pd

#import githubanalysis.processing.get_all_pages_issues as issuepages
import githubanalysis.processing.calc_issue_close_time as calcclose

#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_sub_1day_closes():
    # test how function handles closure times of less than 1 whole day (ie same-day open & close)
    #calcclose.calc_issue_close_time("2022-07-05 15:19:40", "2022-07-06 14:21:09")  # w/in 1 day but dates %d are different

#def test_not_datetime():
    # test how function handles non-date-time input (e.g. throws correct error!)
    #calcclose.calc_issue_close_time("2023-07-05 15:19:40", "2023-07-06 14:21:09") # strings

#def test_create_after_close():
    # test error handling where creation date is AFTER close date
    #calcclose.calc_issue_close_time("2023-07-05 15:19:40", "2023-07-04 14:21:09") # closed_at 04th before created_at 05th

# def test_given_days():
    # test return_in value of 'days' which should fail expectedly (?or should I use default return_in and warn?)