# coding-smart
PhD research software research code. 

[![python-code-checking](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml/badge.svg)](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml)


## Environment  

Code was written in a Linux Ubuntu 22.04 LTS environment within [conda version `23.11.0`](https://docs.conda.io/projects/miniconda/en/latest/miniconda-other-installer-links.html) for `Python 3.10`.  A conda environment yaml file containing exact package versions required for running this code is stored within the repo within the main `coding-smart` repo folder as `coding-smart-github.yml`.   

Code was developed locally and run on a remote [EIDF data science Virtual Machine](https://edinburgh-international-data-facility.ed.ac.uk/services/computing/virtual-desktops) using ssh to connect and run, and git version control to push/pull code versions back and forth between remote VM and local development environment.  
This required setting up SSH keys between local, remote machines and Github ([GH's ssh setup details here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)). 


## Installation & Setup  

In order to run the code in this repo, follow these steps:  
 1) Clone the repo into an appropriate location, for example `~/clonezone`.   
 1) Install `conda` through either [miniconda](https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html) or anaconda. 
 ```
 # install miniconda 
$ mkdir -p ~/miniconda3
$ wget https://repo.anaconda.com/miniconda/Miniconda3-py310_23.11.0-2-Linux-x86_64.sh -O ~/miniconda3/miniconda3.sh
$ bash ~/miniconda3/miniconda3.sh -b -u -p ~/miniconda3
$ ~/miniconda3/bin/conda init bash

# close, reopen shell and check python & conda versions: 
(base) $ conda --version
conda 23.11.0

(base) $ python --version
Python 3.10.13

(base) $ which python
/home/flic/miniconda3/bin/python
 ```
 1) Create the conda environment from the yaml file `coding-smart-github.yml` using conda command `conda env create -f coding-smart-github.yml`. Alternatively, use the `requirements.txt` file to install packages using pip (this method is less recommended).  
 ```
 (base) flic@demeter:~/clonezone/coding-smart$ conda env create -f coding-smart-github.yml
Channels:
 - defaults
 - conda-forge
Platform: linux-64
Collecting package metadata (repodata.json): done
Solving environment: done
Downloading and Extracting Packages:
                                           
Preparing transaction: done                                                           
Verifying transaction: done                                                         
Executing transaction: |                                                                              
    Installed package of scikit-learn can be accelerated using scikit-learn-intelex.                                                                            
    More details are available here: https://intel.github.io/scikit-learn-intelex                                   For example:                                                                
        $ conda install scikit-learn-intelex        
        $ python -m sklearnex my_application.py                                                                    
done
Installing pip dependencies: / Ran pip subprocess with arguments:
['/home/flic/miniconda3/envs/coding-smart-github/bin/python', '-m', 'pip', 'install', '-U', '-r', '/home/flic/clonezone/coding-smart/condaenv.mtnnaren.requirements.txt', '--exists-action=b']
Pip subprocess output:
Requirement already satisfied: pyqt5-sip==12.11.0 in /home/flic/miniconda3/envs/coding-smart-github/lib/python3.10/site-packages/PyQt5_sip-12.11.0-py3.10-linux-x86_64.egg (from -r /home/flic/clonezone/coding-smart/condaenv.mtnnaren.requirements.txt (line 1)) (12.11.0)
done
#
# To activate this environment, use
#
#     $ conda activate coding-smart-github
#
# To deactivate an active environment, use
#
#     $ conda deactivate

(base) flic@demeter:~/clonezone/coding-smart$ conda activate coding-smart-github

(coding-smart-github) flic@demeter:~/clonezone/coding-smart$ 
 ```
 1) Create `githubanalysis` package from the root of the coding-smart repo directory by using the `setup.py` script and running pip command: `pip install -e .` This should be done WITHIN the activated conda environment `coding-smart-github`.  
 ```
 (coding-smart-github) flic@eidf103-vm:~/clonezone/coding-smart$ ls
LICENSE         coding-smart-github-prev.yml    data            repo-analysis-ideas.md  tests
README.md       coding-smart-github-remote.yml  githubanalysis  requirements.txt        zenodocode
code-readme.md  coding-smart-github.yml         images          setup.py

(coding-smart-github) flic@eidf103-vm:~/clonezone/coding-smart$ pip install -e .
Obtaining file:///home/eidf103/eidf103/flic/clonezone/coding-smart
  Preparing metadata (setup.py) ... done
Installing collected packages: githubanalysis
  Running setup.py develop for githubanalysis
Successfully installed githubanalysis-1.0
 ```
1) Check that the installation and setup has worked by running the setup test script ([TODO - issue ticket exists](https://github.com/FlicAnderson/coding-smart/issues/48)). 


## Filesystem  

Within `coding-smart` repo, the key folders are:  
 - `githubanalysis` - holds the `githubanalysis` python module code for getting, processing, analysing and visualizing github repository info.  
 - `zenodocode` -  this holds code for obtaining DOI records for software from zenodo's API to gather github urls for research software repositories.  
 - `tests` - contains `{pytest}` test code for testing project code.     
 - `data` - this will contain raw, cleaned and analysed data for the project.   
 - `images` - will hold analysis result visualisations and other relevant images.

Within `githubanalysis` folder, subfolders will hold submodules of python code with different goals: 
 - `processing` - subpackage of code relating to getting, cleaning and preparing data for analysis.    
 - `analysis` - subpackage of code for data analysis.  
 - `visualisation` - subpackage of code for data viz.
 


#### GitHub Authentication  

This code expects a 'classic' type [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) stored in a file called `config.cfg`  within `coding-smart/githubanalysis` folder.  
This token should have read access to repo permissions, and in my case also has GitHub Workflow permissions. 
DO NOT allow this file to enter version control! 


#### Zenodo Authentication  

This code expects a [Zenodo Access Token](https://zenodo.org/account/settings/applications/tokens/new/) stored in a file called `zenodoconfig.cfg`  within `coding-smart/zenodocode` folder.  
This token does not need `deposit:` permissions as it will only be used to read records, not upload.  
DO NOT allow this file to enter version control! 


#### Testing  

Some tests do exist for certain functions, which will be added to over time.  

To run main pytest tests on code, from `coding-smart/` folder (ensuring all packages from `requirements.txt` or `coding-smart-github.yml` are installed, especially `pytest`), run: `pytest tests/ --runxfail -v
`
This runs all test_*.py files, while `-v` (verbose) shows each test run, and `--runxfail` runs all tests marked as `xfail` (expected to fail) using pytest's `@pytest.mark.xfail(reason="example reason")` format.

```commandline
(coding-smart-github) flic@persephone:~/coding-smart$ pytest tests/ --runxfail -v
========================================== test session starts ==========================================
platform linux -- Python 3.10.9, pytest-7.3.1, pluggy-1.0.0 -- /home/flic/miniconda3/envs/coding-smart-github/bin/python
cachedir: .pytest_cache
rootdir: /home/flic/coding-smart
plugins: anyio-3.5.0, cov-4.0.0
collected 8 items

tests/test_repo_name_clean.py::test_repo_name_clean_notstr PASSED                                 [ 12%]
tests/test_repo_name_clean.py::test_repo_name_clean_notlist PASSED                                [ 25%]
tests/test_repo_name_clean.py::test_repo_name_clean_comma PASSED                                  [ 37%]
tests/test_repo_name_clean.py::test_repo_name_clean_semicolon PASSED                              [ 50%]
tests/test_setup_github_auth.py::test_config_file_not_exists PASSED                               [ 62%]
tests/test_setup_github_auth.py::test_per_page_25 PASSED                                          [ 75%]
tests/test_setup_github_auth.py::test_per_page_default100 PASSED                                  [ 87%]
tests/test_setup_github_auth.py::test_per_page_exceed100 PASSED                                   [100%]

=========================================== 8 passed in 0.13s ===========================================
```

To skip 'expected to fail' tests, such as those requiring access to the GH API access token stored locally only in the config.cfg file, you can remove the `--runxfail` flag:
```commandline
(coding-smart-github) flic@persephone:~/coding-smart$ pytest tests/ -v
========================================== test session starts ==========================================
platform linux -- Python 3.10.9, pytest-7.3.1, pluggy-1.0.0 -- /home/flic/miniconda3/envs/coding-smart-github/bin/python
cachedir: .pytest_cache
rootdir: /home/flic/coding-smart
plugins: anyio-3.5.0, cov-4.0.0
collected 8 items

tests/test_repo_name_clean.py::test_repo_name_clean_notstr PASSED                                 [ 12%]
tests/test_repo_name_clean.py::test_repo_name_clean_notlist PASSED                                [ 25%]
tests/test_repo_name_clean.py::test_repo_name_clean_comma PASSED                                  [ 37%]
tests/test_repo_name_clean.py::test_repo_name_clean_semicolon PASSED                              [ 50%]
tests/test_setup_github_auth.py::test_config_file_not_exists XPASS (Fails remotely: relies on...) [ 62%]
tests/test_setup_github_auth.py::test_per_page_25 XPASS (Fails remotely: relies on GH config ...) [ 75%]
tests/test_setup_github_auth.py::test_per_page_default100 XPASS (Fails remotely: relies on GH...) [ 87%]
tests/test_setup_github_auth.py::test_per_page_exceed100 XPASS (Fails remotely: relies on GH ...) [100%]

===================================== 4 passed, 4 xpassed in 0.13s ======================================
```

To check test coverage, use this format: `pytest --cov=githubanalysis tests/`
```commandline
(coding-smart-github) flic@persephone:~/coding-smart$ pytest --cov=githubanalysis tests/
========================================== test session starts ==========================================
platform linux -- Python 3.10.9, pytest-7.3.1, pluggy-1.0.0
rootdir: /home/flic/coding-smart
plugins: anyio-3.5.0, cov-4.0.0
collected 4 items

tests/test_repo_name_clean.py ....                                                                [100%]

---------- coverage: platform linux, python 3.10.9-final-0 -----------
Name                                Stmts   Miss  Cover
-------------------------------------------------------
githubanalysis/repo_name_clean.py      17      7    59%
-------------------------------------------------------
TOTAL                                  17      7    59%

=========================================== 4 passed in 0.03s ===========================================
```



#### Software License  
Licensed under BSD 3-Clause "New" or "Revised" License. 

The [tl;dr Legal summary of this license]https://www.tldrlegal.com/license/bsd-3-clause-license-revised) summarises this license as: 
>  The BSD 3-clause license allows you almost unlimited freedom with the software so long as you include the BSD copyright and license notice in it (found in Fulltext). 