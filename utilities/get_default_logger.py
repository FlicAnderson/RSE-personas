"""Set up default logger details"""

import logging
from pathlib import Path


def _notebookify(name: str):
    path = Path(name)
    path = "../.." / path
    dir = path.parent
    suffix = path.suffix
    filename = f"{path.name.removesuffix(suffix)}_NOTEBOOK"

    return str(dir / f"{filename}{suffix}")


# set the default logging params
def get_default_logger(
    console: bool,
    set_level_to="INFO",
    log_name="logs/functionname_logs.txt",
    in_notebook=False,
):
    """
    This function sets up a default logger.

    :param console:
    :type: bool
    :param set_level_to:
    :type: str
    :param log_name:
    :type: str
    :returns: logger
    :type: ~logger
    """

    if set_level_to not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(
            f"set_level_to value '{set_level_to}' not recognised; select one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'."
        )
    if in_notebook:
        log_name = _notebookify(log_name)

    logger = logging.getLogger(log_name)
    fh = logging.FileHandler(log_name)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s:%(message)s")
    fh.setFormatter(formatter)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(fh)
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter_console = logging.Formatter("%(levelname)s:%(message)s")
        ch.setFormatter(formatter_console)
        logger.addHandler(ch)
    if set_level_to == "DEBUG":
        logger.setLevel(logging.DEBUG)
    elif set_level_to == "INFO":
        logger.setLevel(logging.INFO)
    elif set_level_to == "WARNING":
        logger.setLevel(logging.WARNING)
    elif set_level_to == "ERROR":
        logger.setLevel(logging.ERROR)
    # logger.propagate = False

    return logger
