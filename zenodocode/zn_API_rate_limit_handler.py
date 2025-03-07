"""Code to handle Zenodo API rate limiting."""
# https://developers.zenodo.org/#rate-limiting at 31 Oct 2024:

# Global limit for guest users:	60 requests per minute, 2000 requests per hour
# Global limit for authenticated users:	100 requests per minute, 5000 requests per hour
# OAI-PMH API harvesting:	120 requests per minute
# When you are making requests to any of our endpoints, you can inspect the following HTTP response headers for more information of your current rate-limit status:
#   HTTP header	Description
#   X-RateLimit-Limit	Current rate-limit policy, i.e. maximum number of requests per minute
#   X-RateLimit-Remaining	Number of requests remaining in the current rate limit
#   X-RateLimit-Reset	Reset time of the current rate limit

import requests
from time import time
import zenodocode.setup_zenodo_auth as znauth


def get_zn_API_rate_limit_reset(config_path: str) -> tuple[int, int]:
    """
    Get remaining rate limit on Zenodo API and return the remaining
    number of requests available, and reset_time in UTC epoch seconds
    But rule of thumb is ~1 request per second shouldn't hit the limit.
    Run this before kicking off a new repo, to check there's limit
    remaining, then if not, wait until reset_time +1 second.
    """
    # authenticated user ratelimit is 5000 requests per hour. ~100 per minute.
    #  ~>1 per second.

    zn_token = znauth.setup_zenodo_auth(config_path=config_path)

    zenodo_check_url = "https://zenodo.org/api/deposit/depositions"
    # using depositions API as this is NOT an endpoint required by this codebase
    # and checks write access is included in token permissions FYI

    api_response = requests.Session().get(
        url=zenodo_check_url, params={"access_token": zn_token}
    )

    remaining_limit = api_response.headers["X-RateLimit-Remaining"]
    assert isinstance(remaining_limit, int)

    reset_time = api_response.headers["X-RateLimit-Reset"]
    assert isinstance(reset_time, int)

    return remaining_limit, reset_time


def wait_until_calc(reset_time: int) -> int:
    """
    Get time until Zenodo API rate limit reset time (in epoch seconds)
    """
    now = int(time())  # this is epoch seconds, but as an int not float
    future = reset_time

    time_to_wait = future - now + 1

    return time_to_wait
    # run from time import sleep
    # sleep(time_to_wait)
