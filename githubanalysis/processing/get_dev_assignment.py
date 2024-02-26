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

    def get_dev_assignment(self, repo_name, dev_name, issues_data):
        """
        For developer dev_name in repo repo_name; 
        Assign dev_name to assignment category based on issue tickets and PRs;  
        Return assignment_type category. 
        
        :param repo_name: GH repository name  
        :type: string
        :param dev_name: developer GH username  
        :type: string 
        :returns: `assignment_type` of dev_name for repo_name.
        :type: string

        """
        
        #check dev_name is valid (e.g. not NaN or empty string or whatever)

        #check issues/PRs data file exists already; if not, get that.  
        if issues_data is not None:
            issues_df = pd.read_csv(issues_file_extra_info, header=0) 

        # get issues/PRs data for developer dev_name
        
        # check assignments for dev_name

        #return assignment_type value 

        d_dict = {'dev_name': assignment, 'issues': None, 'PRs': None}
        assignment_df = pd.DataFrame(data=d_dict)

        return assignment_df

        
# this bit
if __name__ == "__main__":
    """
    get issue/PR assignment for specific dev in specific GH repo. 
    """

    logger = loggit.get_default_logger(console=True, set_level_to='DEBUG', log_name='logs/get_dev_assignment_logs.txt')

    dev_assigner = DevAssigner(logger)

    if len(sys.argv) == 4:
        repo_name = sys.argv[1]  # use second argv (user-provided by commandline)
        dev_name = sys.argv[2]  # use third argv (user-provided by commandline)
        issues_data = sys.argv[3] # use fourth argv as location of issues data if given  
    else:
        raise IndexError('Please enter a repo_name.')  

    assignment_df = dev_assigner.get_dev_assignment(dev_name=dev_name, repo_name=repo_name)
