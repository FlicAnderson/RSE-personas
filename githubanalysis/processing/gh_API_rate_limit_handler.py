"""Code to handle API rate limiting"""

from time import time
import datetime
import requests

import githubanalysis.processing.setup_github_auth as ghauth


def get_gh_API_rate_limit_reset(config_path: str) -> tuple[int, int]:
    """
    Get remaining rate limit on GH API and return the remaining
    number of requests available, and reset_time in UTC epoch seconds
    But rule of thumb is ~1 request per second shouldn't hit the limit.
    Run this before kicking off a new repo, to check there's limit
    remaining, then if not, wait until reset_time +1 second.
    """
    # ratelimit is 5000 requests per hour. ~80 per minute. ~1 per second.
    # n_commits is number of commits per repo (across all branches)
    # will hit rate limit for single repo if n_commits
    # 5000 commits / 100 per page = 50 pages full of commits,
    # but requires 1 request per commit also, so limit would be 2500, and 25 pages.

    gh_token = ghauth.setup_github_auth(config_path=config_path)
    auth_header = {"Authorization": "token " + gh_token}

    ratelimit_api_url = "https://api.github.com/rate_limit"
    # using 'core' resource as this provides rate limit status for
    # all non-search-related resources in the REST API:
    # https://docs.github.com/en/rest/rate-limit/rate-limit?apiVersion=2022-11-28

    api_response = requests.Session().get(url=ratelimit_api_url, headers=auth_header)

    remaining_limit = api_response.json().get("resources").get("core").get("remaining")
    assert isinstance(remaining_limit, int)

    reset_time = api_response.json().get("resources").get("core").get("reset")
    assert isinstance(reset_time, int)

    return remaining_limit, reset_time


def wait_until_calc(reset_time: int) -> int:
    """
    Get time until GH API rate limit reset time (in epoch seconds)
    """
    now = int(time())  # this is epoch seconds, but as an int not float
    future = reset_time

    time_to_wait = future - now + 1

    return time_to_wait
    # run from time import sleep
    # sleep(time_to_wait)
