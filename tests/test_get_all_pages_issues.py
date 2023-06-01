""" Test function for getting all pages of items for issues for a given repository. """

import pytest
from github import Github
import pandas as pd
import requests
import githubanalysis.processing.get_repo_connection as ghconn
import githubanalysis.processing.get_all_pages_issues as issuepages


repo_name_a = 'ropensci/dwctaxon'  # repo with 49 closed, 6 open issues. with get_issues(state='all) this rises to 92.
test_repo_no_issues: 'FlicAnderson/test-repo-no-issues'  # this is a public repo where I've unticked 'issues' in settings.

per_pg = 100


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_1pg_only():
    # tests behaviour when there is no 'next' or 'last' page of issues

    # independently check there's no 'last' in links of repo
    urlparam = f"https://api.github.com/repos/{repo_name_a}/issues"
    repo_links = requests.get(url=urlparam, params={'per_page':per_pg, 'state':'all'}).links
    repo_links_pages = [key for key in repo_links]
    if 'last' in repo_links_pages:
        raise KeyError(f'test variable repo_name_a {repo_name_a} now contains more than one page, choose new test repo name with fewer issues as a test.')
    else:
        # continue test.
        content = issuepages.get_all_pages_issues(repo_name=repo_name_a)
        assert len(content.index) <= per_pg, 'More issues retrieved than per_pg value for this one-page repo; check for duplication or other problems.'
        # there shouldn't be more issues than 1 pg's worth. If so, this means


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_returns_df():
    # checks that object returned is pd.DataFrame

    content = issuepages.get_all_pages_issues(repo_name='ropensci/dwctaxon')
    assert isinstance(content, pd.DataFrame)


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_has_issues():
    # checks behaviour on repos without issues
    # ?check pygithub github.Repository.Repository repo object .has_issues bool.

    with pytest.raises(AttributeError):
        issuepages.get_all_pages_issues(repo_name='FlicAnderson/test-repo-no-issues')

# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_closed_issues_count():
    # confirm count of closed issues is correct


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_open_issues_count():
    # confirm count of open issues is correct

    # use get_repo_connection() to get value from repo-focussed github api call through pygithub
    open_iss = ghconn.get_repo_connection(repo_name=repo_name_a).open_issues_count

    all_issues = issuepages.get_all_pages_issues(repo_name=repo_name_a)

    # get number of open issues showing in df of all pages issues from issue-focussed github api call through pygithub
    get_all_pgs_open_iss = all_issues.state.value_counts()['open']

    assert int(get_all_pgs_open_iss) == int(open_iss), 'Number of open issues in all_issues df does not match repo_connection.open_issues_count'


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_all_issues_count():
    # confirm count of all issues is correct


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_inc_imp_issues_params():
    # confirm useful parameters are being returned in df:  'url', 'number', 'assignee'/'assignees', 'created_at', 'closed_at',
    # ... 'pull_request' (contains url of PR if so), 'title', 'repository_url', 'labels' (bug, good first issue etc), 'state' (open/closed), 'user' (created issue)

    all_issues = issuepages.get_all_pages_issues(repo_name=repo_name_a)
    all_issues_cols = all_issues.columns

    wanted_cols = ['url', 'repository_url', 'labels', 'number', 'title', 'state',
                   'assignee', 'assignees', 'created_at', 'closed_at', 'pull_request']

    assert all(item in all_issues_cols for item in wanted_cols)


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_excl_fake_issues_params():
    # this one is mainly checking my test logic tbh.

    all_issues = issuepages.get_all_pages_issues(repo_name=repo_name_a)
    all_issues_cols = all_issues.columns

    unwanted_cols = ['fake_url_column', 'cat', 'should not get this far']

    assert not all(item in all_issues_cols for item in unwanted_cols)


# @pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
# def test_validate_json():
    # validate json returned?
    # check json input contains content?
    # check for specific fields being there?