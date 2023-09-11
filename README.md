# coding-smart
PhD research software research code. 

[![python-code-checking](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml/badge.svg)](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml)


## Filesystem  

Within `coding-smart` repo, the key folders are:  
 - `githubanalysis` - holds the `githubanalysis` python module code for getting, processing, analysing and visualizing github repository info.  
 - `tests` - contains `{pytest}` test code for testing project code.     
 - `data` - this will contain raw, cleaned and analysed data for the project.   
 - `images` - will hold analysis result visualisations and other relevant images.

Within `githubanalysis` folder, subfolders will hold submodules of python code with different goals: 
 - `processing` - subpackage of code relating to getting, cleaning and preparing data for analysis.    
 - `analysis` - subpackage of code for data analysis.  
 - `visualisation` - subpackage of code for data viz.


## Environment  

Code was written in a linux Ubuntu 22.04 LTS environment.  

A conda environment yaml file for running this code is stored within the repo within the `code/githubanalysis/` folder as `coding-smart-github.yml`.   


#### GitHub Authentication  

This code expects a GitHub Personal Access Token stored in a file called `config.cfg` locally.  
This PAT should have read access to repo permissions, and in my case also has GitHub Workflow permissions. 

#### License  
Licensed under BSD 3-Clause "New" or "Revised" License.
