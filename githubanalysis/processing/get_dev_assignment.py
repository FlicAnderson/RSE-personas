""" Function to get assignment type for given dev in given GH repo. """

import sys
import os
import pandas as pd
import logging

import utilities.get_default_logger as loggit

class DevAssigner:

    # if not given a better option, use my default settings for logging
    logger: logging.Logger
    def __init__(self, logger: logging.Logger = None) -> None:
        if logger is None:
            self.logger = loggit.get_default_logger(console=False, set_level_to='INFO', log_name='logs/get_dev_assignment_logs.txt')
        else:
            self.logger = logger

    def get_dev_assignment(self, dev_name, repo_name):
        """
        For developer dev_name in repo repo_name; 
        Assign dev_name to assignment category based on issue tickets and PRs;  
        Return assignment_type category. 
        
        :param dev_name: developer GH username  
        :type: string 
        :param repo_name: GH repository name  
        :type: string
        :returns: `assignment_type` of dev_name for repo_name.
        :type: string

        """
        
        #check dev_name is valid (e.g. not NaN or empty string or whatever)

        #check issues/PRs data file exists already; if not, get that.  

        # 

