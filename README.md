# coding-smart
PhD research software research code. 

[![python-code-checking](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml/badge.svg)](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml)


## Environment  

Code was written in a Linux Ubuntu 22.04 LTS environment within [conda version `23.11.0`](https://docs.conda.io/projects/miniconda/en/latest/miniconda-other-installer-links.html) for `Python 3.10`.  A conda environment yaml file containing exact package versions required for running this code is stored within the repo within the main `coding-smart` repo folder as `coding-smart-github.yml`.   


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
(coding-smart-github) flic@demeter:~/clonezone/coding-smart$ ls -F
LICENSE         coding-smart-github.yml      githubanalysis/           logs/                   setup.py    zenodocode/
README.md       coding-smart.code-workspace  githubanalysis.egg-info/  repo-analysis-ideas.md  tests/
code-readme.md  data/                        images/                   requirements.txt        utilities/

(coding-smart-github) flic@eidf103-vm:~/clonezone/coding-smart$ pip install -e .
Obtaining file:///home/eidf103/eidf103/flic/clonezone/coding-smart
  Preparing metadata (setup.py) ... done
Installing collected packages: githubanalysis
  Running setup.py develop for githubanalysis
Successfully installed githubanalysis-1.0
 ```
1) Check that the installation and setup has worked by running the setup test script ([TODO - issue ticket exists](https://github.com/FlicAnderson/coding-smart/issues/48)). 

### Regenerating environment setup files 

If adding a new package to the conda enviroment, create a NEW **updated environment yaml file for conda** in the repo directory by running `conda env export > coding-smart-github.yml` after the new package has been installed.  
This file contains the precise package builds used on the system, allowing closer reproducibility.
The repository also contains a `requirements.txt` file which contains less specific package information, which may be easier to use on other systems. 

To update the **`requirements.txt` pip file**, run `pip list --format=freeze | grep -vE "^mkl-.*" | grep -vE "^githubanalysis.*" > requirements.txt` from the repo directory root.  
This creates the requirements file, but removes any packages starting `mkl-`, and the `githubanalysis` package created by the setup script and generated via `pip install -e .`. 
Leaving those packages in breaks the Github Actions Continuous Build/Integration environment, so this will avoid those issues.  
The standard command is `pip list --format=freeze > requirements.txt`



## Developing / Running This Code

Code was developed locally in [WSL2:Ubuntu](https://learn.microsoft.com/en-us/windows/wsl/setup/environment) within [VS Code IDE](https://code.visualstudio.com/docs/remote/wsl) and run on a remote [EIDF data science Virtual Machine](https://edinburgh-international-data-facility.ed.ac.uk/services/computing/virtual-desktops) using ssh to connect and run, and git version control to push/pull code versions back and forth between remote VM and local development environment.  

This required setting up SSH keys between local, remote machines and Github ([GH's ssh setup details here](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)). 

The following details how the code was developed and run, and should be adjusted if your operating system or filesystem setups vary from those used by @FlicAnderson!   

Further details on my WSL setup and SSH key setup process:   
```
# in WSL: 
# check git installed (installed git for Windows, but it's a default in Ubuntu) 

    git --version
    git config --global credential.helper "/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe"

# update programs etc  
    sudo apt update && sudo apt upgrade

# checked the security certificates were up to date, they were.
    sudo apt-get install wget ca-certificates
    sudo apt-get update

# generate RSA SSH key using new hostname (this is for adding to SAFE to connect to EIDF VM)
    cat .ssh/id_rsa.pub
    ssh-keygen
    cat .ssh/id_rsa.pub

# checked I can connect to EIDF VM; created the ssh config file:
    ssh -J flic@eidf-gateway.lo.ca.ti.on flic@00.00.0.00
    nano .ssh/config

# make clonezone directory to clone repos into
    mkdir clonezone
    cd clonezone/

# create GPG key to add to GitHub 
    gpg --full-generate-key
    gpg --list-secret-keys --keyid-format=long
    gpg --armor --export 00000000000000000

# create more detailed SSH key to add to GitHub  
    ssh-keygen -t ed25519 -C "email@ad.re.ss"
    cat ~/.ssh/id_ed25519.pub

# clone the git repo finally (within clonezone folder) 
    git clone git@github.com:FlicAnderson/coding-smart.git

```
Local SSH `config` file example contents (within WSL2: Ubuntu filesystem):
```
# file at ~/.ssh/config
Host eidf
User flic
Hostname 00.00.0.00
Proxyjump flic@eidf-gateway.lo.ca.ti.on
ProxyCommand ssh -W %h:%p eidf-gateway@epcc.ed.ac.uk
LocalForward 8888 localhost:8888
IdentityFile ~/.ssh/id_rsa
```

This config allows the EIDF VM to be connected to by running `ssh eidf` in the local terminal.  It also allows jupyter notebook server to forward to the local browser using port forwarding.  The jupyter notebook can be viewed in the local browser by clicking through to the localhost link which can be found by sending a cancel command (`Ctrl + C`) in the terminal session running the notebook server to view the links and selecting `n` to prevent shutdown of the server. The links should open in the local browser if the port forwarding is set up correctly.
```
Serving notebooks from local directory: /home/eidf103/eidf103/flic/clonezone/coding-smart/githubanalysis/notebooks
3 active kernels
Jupyter Notebook 6.5.2 is running at:
http://localhost:8888/?token=0123401234abcdabcdabcd012340123401234abcdabcd
 or http://127.0.0.1:8888/?token=0123401234abcdabcdabcd012340123401234abcdabcd
Shutdown this notebook server (y/[n])? n
resuming operation...
```

Files can be pulled from the remote EIDF VM by `scp` for example by running  `scp eidf:/home/eidf103/eidf103/flic/clonezone/coding-smart/data/big20top10-dev_assignments_2024-03-11.csv ./data/` to pull a data csv file from the remote VM to local `data` folder.

Code was developed with the following set up:   

    A) a remote terminal connected to the EIDF system - this runs a matching [conda](https://anaconda.org/anaconda/conda) environment `coding-smart-github`, activated using `conda activate coding-smart-github`;  `tmux` terminal sessions, listed using `tmux list-sessions`, and `tmux attach` to create a new session 'notebook' which runs the jupyter notebook in one session, and can be switched away from without exiting by using `Ctrl + b` then `d` to detatch from that session which lets me exit the ssh VM and keeps the notebook running; scripts are run from a separate tmux terminal session, for example `python githubanalysis/processing/get_all_devs_assignment.py 'JeschkeLab/DeerLab' 'all-issues_JeschkeLab-DeerLab_2024-03-11' 'contributors_JeschkeLab-DeerLab_2024-03-11'`. 

    B) a local terminal running WSL2: Ubuntu, for git pushing/pulling from local. This could be done from VS Code IDE (C), but it's easier to keep track of file changes separately in the terminal.   

    C) a local VS Code IDE connected to the WSL2: Ubuntu install, also connected to the local `coding-smart` repository folder, for editing the code files. Changes are made in this program, then saved, then pushed to the remote repo on GH.   

Development process example: 

A code change would be made to the file (for example `README.md`) in local VS Code IDE (C) and the change saved.    
Local terminal (B) would show these changes when `git status` is run on the repo folder.   
The changes would be committed and pushed from here (B).   
Swapping to remote terminal (A), in a tmux session that isn't already running a jupyter notebook server, `git pull` would collect the code change from GitHub, and allow the newly updated code to be run (either within a jupyter notebook after attaching that tmux session, or via the terminal with python) on the EIDF VM system.  

**NOTE: Changes are made locally first, rather than changes made remotely on the VM and pulled down.**   
It IS possible to connect locally running VS Code to a remote VM and develop remotely that way, but it's more hassle to keep everything connected nicely and creates more headaches. 

Care needs to be taken when developing in git branches to avoid confusion!

### Linting and Formatting

[`ruff`](https://docs.astral.sh/ruff/) is installed and used in developing this code, and has been set up to run on a GitHub Actions Continuous Build/Integration setup, but can also be run manually.  

For linting checks:  
  - `python -m ruff check [folderpath]` from the repository folder (e.g. `python -m ruff check githubanalysis/` will run **linting checks** on all non-excluded file types within the githubanalysis folder)   
  - `python -m ruff check [folderpath] --fix` will MAKE the proposed non-risky changes (leaving potentially dangerous ones out) 

For formatting checks: 
  - `python -m ruff format --diff` can be run to SHOW the diffs of potential **formatting changes** but they will not be made  
  - `python -m ruff format` will actually MAKE the formatting changes which would be compared using the `--diff` flag.    

Running these periodically and applying the suggested fixes is recommended.  


## Filesystem  

Within `coding-smart` repo, the key folders are:  
 - `githubanalysis` - holds the `githubanalysis` python module code for getting, processing, analysing and visualizing github repository info.  
 - `zenodocode` -  this holds code for obtaining DOI records for software from zenodo's API to gather github urls for research software repositories.  
 - `utilities` - this holds generally useful functions (e.g. logging setup).  
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


#### Generating datasets (Processing) 

The data collection processing workflow should operate roughly as follows: 

1) Setup  
```
# load conda environment and go to root directory of repo:  
$ conda activate coding-smart-github
$ cd clonezone/coding-smart
```
(Do any git pulls here to get latest content, check branch etc.)


2) Get Zenodo record IDs to query  
![get_software_ids.py](docs/coding-smart-get_software_ids.jpg)

```
# get N software record IDs from Zenodo:  
$ python zenodocode/get_software_ids.py 2500   
```
Input: number of software record IDs to return from Zenodo
Output: csv file of software record IDs: `data/zenodo_ids_xN_YYYY-MM-DD.csv`
Logging: `logs/get_software_ids_logs.txt` 


3) Get metadata for Zenodo IDs, grab all GitHub URLs 
![get_gh_urls.py](docs/coding-smart-get_gh_urls.jpg)
```
# get github URLs for the zenodo IDs (results in <2500 records since not all have github repos...):
$ python zenodocode/get_gh_urls.py data/zenodo_ids_x2500_2024-02-08.csv   
```
Input: csv file of Zenodo software IDs  
Output: csv file of Github URLs and their Zenodo software record IDs: `data/gh_urls_YYYY-MM-DD.csv`
Logging: `logs/get_gh_urls_logs.txt` 


4) Create a 'todo' file of GitHub repo names from URLs and collate data gathering info 
![create_todo_file.py](docs/coding-smart-create_todo_file.jpg) 
```
$ python githubanalysis/processing/create_todo_file.py data/gh_urls_2024-02-08.csv  
```
Input: csv file of Zenodo IDs and GitHub URLs   
Output: csv 'todo' file with repo names, Github URLs, Zenodo IDs and various data gathering task statuses per repo: `data/todo_YYYY-MM-DD.csv`
Logging: `logs/create_todo_file_logs.txt` 


5) Process 'todo' file, get stats for each repo and writing out in blocks of 10  
![gather_gh_stats.py](docs/coding-smart-gather_gh_stats.jpg)
```
$ python githubanalysis/processing/gather_gh_stats.py data/todo_2024-02-08.csv  
```
Input: csv 'todo' file of repo names  
Output: csv file of stats per repo: `data/gh_stats_YYYY-MM-DD.csv`
Logging: `logs/gather_gh_stats_logs.txt` 

6) Filter repo stats to exclude repos  
```
$ TODO python githubanalysis/processing/generate_test_set.py data/gh_stats_YYYY-MM-DD.csv
```
Input: csv file of stats per repo  
Output: : `data/test_set_repos_YYYY-MM-DD.csv`
Logging: `logs/generate_test_set_logs.txt` 


#### Generating datasets (Analysis) 

Still to be developed.  


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

The [tl;dr Legal summary of this license](https://www.tldrlegal.com/license/bsd-3-clause-license-revised) summarises this license as: 
>  The BSD 3-clause license allows you almost unlimited freedom with the software so long as you include the BSD copyright and license notice in it (found in Fulltext). 
