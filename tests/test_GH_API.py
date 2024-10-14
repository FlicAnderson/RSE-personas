import requests

import githubanalysis.processing.setup_github_auth as ghauth


def make_request(api_key: str, repo_name: str):
    headers = {"Authorization": "token " + api_key}
    base_url = "https://api.github.com/repos/{repo_name}/commits"
    response = requests.get(url=f"{base_url}", headers=headers)
    return response


def test_GH_commits_success(
    repo_name: str = "JeschkeLab/DeerLab",
    config_path: str = "../../githubanalysis/config.cfg",
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
    assert data["element_count"] > 0
