import pytest
import requests

import githubanalysis.processing.setup_github_auth as ghauth


def make_request(api_key: str, repo_name: str):
    headers = {"Authorization": "token " + api_key}
    base_url = f"https://api.github.com/repos/{repo_name}/commits"
    response = requests.get(url=base_url, headers=headers)
    return response


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_GH_commits_success(
    # test against one of Flic's non-updated repos; ~20 commits, 2 branches.
    repo_name: str = "FlicAnderson/peramagroon",
    config_path: str = "githubanalysis/config.cfg",
):
    # Arrange:
    api_key = ghauth.setup_github_auth(config_path=config_path)
    # Act:
    response = make_request(api_key, repo_name)
    # Assertion:
    assert response.status_code == 200  # validate status code
    data = response.json()
    # Assertion of body response content:
    assert len(data) > 0
    # GH commits API limits returns to 30(default) unless `per_page` is increased (max 100)
    assert len(data) <= 30


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_GH_commits_fail_bad_repo_name(
    repo_name: str = "FlicAnderson/NonexistentRepo",  # EXPECT FAIL
    config_path: str = "githubanalysis/config.cfg",
):
    # Arrange:
    api_key = ghauth.setup_github_auth(config_path=config_path)
    # Act:
    response = make_request(api_key, repo_name)
    # Assertion:
    assert response.status_code == 404  # validate status code
    data = response.json()
    # Assertion of body response content:
    assert len(data) == 3
    # confirm that API response returns correct message for missing repo
    assert "Not Found" in data.get("message")


@pytest.mark.xfail(reason="Fails remotely: relies on GH config file")
def test_GH_commits_fail_emptybranch(
    repo_name: str = "FlicAnderson/peramagroon",
    config_path: str = "githubanalysis/config.cfg",
):
    # Arrange:
    api_key = ghauth.setup_github_auth(config_path=config_path)
    headers = {"Authorization": "token " + api_key}
    branch = ""  # EMPTY on purpose: check response is as expected
    # Act:
    response = requests.get(
        url=f"https://api.github.com/{repo_name}/commits?sha={branch}",
        headers=headers,
    )
    # Assertion:
    assert response.status_code == 404  # validate status code
    data = response.json()
    # Assertion of body response content:
    assert len(data) == 3
    # confirm that API response returns correct message for missing repo
    assert "Not Found" in data.get("message")


# NOT expected to fail, since doesn't rely on local or missing config.cfg
def test_GH_commits_bad_api_key(
    repo_name: str = "FlicAnderson/test-repo-no-issues",
):
    response = make_request(
        api_key="teststringnonsenseunrealkey",
        repo_name=repo_name,
    )
    assert response.status_code == 401  # 401 Bad Credentials!
    data = response.json()
    # Assertion of body response content:
    assert len(data) == 3
    # confirm API response returns correct message for invalid API key
    assert "Bad credentials" in data.get("message")
