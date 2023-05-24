# coding-smart
PhD research software research code. 


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


#### License  
Licensed under BSD 3-Clause "New" or "Revised" License.
