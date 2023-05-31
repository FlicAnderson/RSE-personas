""" Test function for getting all pages of items for issues for a given repository. """

import pytest
from github import Github
import githubanalysis.processing.get_all_pages_issues as issuepages

#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_1pg_only():
    # tests behaviour when there is no 'next' or 'last' page of issues


#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_returns_df():
    # checks that object returned is pd.DataFrame


#@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
#def test_has_issues():
    # checks behaviour on repos without issues
    # ?check pygithub github.Repository.Repository repo object .has_issues bool.


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_closed_issues_count():
    # confirm count of closed issues is correct


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_open_issues_count():
    # confirm count of open issues is correct


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_all_issues_count():
    # confirm count of all issues is correct

# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_imp_issues_params():
    # confirm useful parameters are being returned in df:  'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
    # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url', 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)


# validate json returned?
# check json input contains content?
# check for specific fields being there?