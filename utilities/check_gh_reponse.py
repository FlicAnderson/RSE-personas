from requests import Response

from logging import Logger
import githubanalysis.processing.gh_API_rate_limit_handler as ratehandle


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


def raise_if_resoponse_error():
    """
    if status is 200: return
    else:
        call raise_if_response_needs_retry()
        if it doesn't raise:
            if status is 404:
                raise RepoNotFoundError() <- need to make this c.f. RateLimitError or UnexpectedAPIError
            else:
                raise UnexpectedAPIError()
    done!
    """
