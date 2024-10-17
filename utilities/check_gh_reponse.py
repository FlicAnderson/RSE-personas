from requests import Response
from time import sleep
from typing import Callable, TypeVar
from logging import Logger

import githubanalysis.processing.gh_API_rate_limit_handler as ratehandle


class UnexpectedAPIError(RuntimeError):
    pass


class RepoNotFoundError(RuntimeError):
    pass


class RateLimitError(RuntimeError):
    waittime: int

    def __init__(self, waittime: int):
        self.waittime = waittime
        super().__init__()


def raise_if_response_needs_retry(api_response: Response, logger: Logger):
    if not (api_response.status_code == 403 or api_response.status_code == 429):
        return

    logger.debug(
        f"API response code is {api_response.status_code} and API response is: {api_response}; headers are {api_response.headers}. "
    )
    if api_response.headers.get("X-RateLimit-Remaining") == "0":
        resettime = api_response.headers.get("X-RateLimit-Reset")
        if resettime is not None:
            resettime = int(resettime)
        else:
            raise RuntimeError("Reset time value 'X-RateLimit-Reset' resettime is None")
        waittime = ratehandle.wait_until_calc(reset_time=resettime)
    else:
        waittime = 1
    logger.error(
        f"Waiting {waittime} seconds as API rate limit remaining is {api_response.headers.get('X-RateLimit-Remaining')} and reset time is {api_response.headers.get('X-RateLimit-Reset')} in epoch seconds."
    )
    raise RateLimitError(waittime=waittime)


def raise_if_response_error(
    api_response: Response, commit_hash: str, repo_name: str, logger: Logger
):
    """
    This will handle 404s, 429s and 403s. And returns if all is ok.
    """

    if api_response.status_code == 200:
        return

    raise_if_response_needs_retry(api_response=api_response, logger=logger)

    if api_response.status_code == 404:
        raise RepoNotFoundError(
            f"API response not OK for repo {repo_name}; API response is: {api_response}; headers are: {api_response.headers}."
        )
    else:
        raise UnexpectedAPIError(
            f"API response not OK, please investigate for commit {commit_hash} at repo {repo_name}; API response is: {api_response}; headers are: {api_response.headers}."
        )


# https://docs.python.org/3/library/typing.html#generics
T = TypeVar("T")  # this naming follows convention for this type of thing


def run_with_retries(
    fn: Callable[[], T],
    logger: Logger,
    max_retries=25,
):
    """
    run `fn` until either:
        a) it returns without error or
        b) `fn` exits with `rateLimitError` and number of retries reaches `max_retries` or
        c) some other error occurs
    """
    assert max_retries > 0
    retries = 0
    while retries < max_retries:
        try:
            return fn()
        except RateLimitError as e:
            retries += 1
            sleep(e.waittime)  # in seconds
            logger.debug(f"Sleep of {e.waittime} seconds complete.")
    raise RuntimeError("Hit maximum number of retries")
