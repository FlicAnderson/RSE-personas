"""Set up default logger details"""

import logging

# set the default logging params 
def get_default_logger(console: bool, set_level_to='INFO', log_name="logs/functionname_logs.txt"):
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
    try: 
        set_level_to in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    except ValueError as e:
        raise ValueError(f"set_level_to value '{set_level_to}' not recognised; select one of 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.")
    
    logger = logging.getLogger('coding-smart-logger')
    fh = logging.FileHandler(log_name)
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s:%(message)s')
    fh.setFormatter(formatter)
    if (logger.hasHandlers()):
        logger.handlers.clear()
    logger.addHandler(fh)
    if console:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter_console = logging.Formatter('%(levelname)s:%(message)s')
        ch.setFormatter(formatter_console)
    logger.addHandler(ch)
    if set_level_to == 'DEBUG':
        logger.setLevel(logging.DEBUG)
    elif set_level_to == 'INFO':
        logger.setLevel(logging.INFO)
    elif set_level_to == 'WARNING':
        logger.setLevel(logging.WARNING)
    elif set_level_to == 'ERROR':
        logger.setLevel(logging.ERROR)
    logger.propagate = False

    return logger