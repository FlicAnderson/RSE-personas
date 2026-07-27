# RSE-personas

# Project Quick Start

Research software supporting @FlicAnderson's PhD research. 

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20124656.svg)](https://doi.org/10.5281/zenodo.20124656)
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)
[![python-code-checking](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml/badge.svg)](https://github.com/FlicAnderson/coding-smart/actions/workflows/python-code-checking.yml)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/FlicAnderson/RSE-personas/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/FlicAnderson/RSE-personas)
[![SWH](https://archive.softwareheritage.org/badge/swh:1:dir:cf8176f6f8cbb3eff513e5f2d6206621bdf0dd27/)](https://archive.softwareheritage.org/swh:1:dir:cf8176f6f8cbb3eff513e5f2d6206621bdf0dd27;origin=https://github.com/FlicAnderson/RSE-personas;visit=swh:1:snp:a478d04aa42a30409e47a356e4c0c19062a69310;anchor=swh:1:rev:786a35215b8779f78c3acae5931d1dedc961a76a)

*A work in progress repository containing the research software used for research into creating and analysing Research Software Engineering Personas.*  

## Vision and Mission

- **Vision:** Working towards a tool to calculate RSE Personas for Research Software contributors.
- **Mission:** : Exploring RSE Personas: a novel data-driven concept for describing patterns of research software development behaviours within public active GitHub repositories to identify what data footprints can tell us about RSEs and their projects. 

## About

This repository supports the PhD thesis work of me (@FlicAnderson) towards creating and analysing research software development through the interactions developers or active users make with GitHub repositories via their contributions, such as commits, issue ticket engagement, pull requests, code review, and more.   

The project began in 2022 and is expected to complete by the end of 2027. 

## Roadmap & Milestones

- **Goals:** Clear overview of overarching and short-term goals.
- **Outcomes:** Description of expected results and deliverables.

## The Team

- **Members:** List of team members and their roles in the project.
- **Roles & Responsibilities:** [Team Directory](link-to-directory) outlines roles, responsibilities and their ways of working.

## Contributing

<!-- - **Guidelines:** [Contribution Guidelines](link-to-guidelines) for contributors. -->
<!-- - **Code of Conduct:** [Code of Conduct](link-to-coc) ensures a respectful project environment. -->
<!-- - **Resource Plans:** Details on available resources and recommended practices for the project team. -->

## Licensing

This project uses a [BSD-3-Clause](https://github.com/FlicAnderson/RSE-personas/tree/main?tab=BSD-3-Clause-1-ov-file#BSD-3-Clause-1-ov-file) License - see `LICENSE.md` for details. 

## Citing & Acknowledgement

- **Citation Instructions:** You can cite this repository by using the details at the DOI (https://doi.org/10.5281/zenodo.15458393), using the information in the citation file: `CITATION.cff`, or by following the 'Cite this repository' button.
- **Acknowledgment:** This repository has been built to support the ideas and research goals of my PhD project at The University of Edinburgh, and therefore would not exist without my patient and excellent supervisors @jsindt and @npch. It has also been vastly improved by the wisdom, advice and constructive code review efforts of @agango93, @dk949, @jjacobx and others!  


This repository uses the template created and maintained by The Turing Way team members and shared under CC-BY 4.0 for reuse: https://github.com/alan-turing-institute/reproducible-project-template.


## Contact

- **Reach Out:** Felicity (dot) Anderson @ ed.ac.uk


## Environment  

Code was written in a Linux Ubuntu 22.04 LTS environment within [conda version `23.11.0`](https://docs.conda.io/projects/miniconda/en/latest/miniconda-other-installer-links.html) for `Python 3.10`.  

A conda environment yaml file containing exact package versions required for running this code is stored within the repo within the main `coding-smart` repo folder as `coding-smart-github.yml`.   


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

Steps: 
    1) Ensure you are in the coding-smart-github conda environment and have the following packages in your environment  
    2) Create a classic access token via Github Authentication Settings and create a file called `config.cfg` with the following content:
```
[ACCESS]
token = <your-access-token-string>
```
    3) Ensure you've pasted in your token, but leave `[ACCESS]` and `token = `. 
    4) Ensure that the `.gitignore` file avoids committing this file (it is stored under `# private data` heading)


#### Zenodo Authentication  

This code expects a [Zenodo Access Token](https://zenodo.org/account/settings/applications/tokens/new/) stored in a file called `zenodoconfig.cfg`  within `coding-smart/zenodocode` folder.  
This token does not need `deposit:` permissions as it will only be used to read records, not upload.  
DO NOT allow this file to enter version control! 

This file should follow the same file and token format as above for the github `config.cfg` file. 


#### Dataset Collection and Data Processing Architecture: 

While the codebase is very much at the Work In Progress stage, with many features which have come about as a feature of Research Software time and training barriers, hopefully the following rough diagrams should act as a temporary guide to the interactions and relationships between different scripts in the repository, especially until greater documentation is added! 

The key to the diagram format is as follows: 
![Key to diagram of main RSE_personas repo scripts for data collection, processing and analysis](RSE_personas_diagram_key.pdf)

The main diagram can be seen here: 

![The main RSE_personas codebase flow diagram showing main GH API data collection, processing and analysis scripts](RSE_personas-codebase-flow-diagram.pdf)



#### Datasets and Data Processing: dealing with multiple versions of data files by retaining newest 

In order to ensure that the dataset comprises of the most recent data - for example if some repositories' data collection via the GH API has been run where there was an issue in the initial data collection run - it's sometimes necessary to move the older files to retain the 'cleanest' most up to date set of data.  

This means we may want to keep the most recent file, and move other older-dated copies to another folder. 

This is done by running the bash script in `data/` called `filesorter.sh`.  

The file is run with commandline arguments as follows: 
```
bash filesorter.sh "filename_glob_to_match" "existing_older_files_folder_name/"
```

In an example where we've needed to move older versions of Pull Request Code Review data (PRCR), this was done as follows: 

```
# from RSE-personas home / 'root' directory folder, go to data folder

$ cd data/  

# make folder to store 'older files' of the type desired (doing this in batches or by 'type' of data keeps things manageable and allows easier checking)  

$ mkdir older_PRCR 

# run the file sorting script via bash, using the name of the newly created folder as the last argument to the script, and giving the filename format string to match against for this batch of files (e.g. 'main' PRCR type first)

$ bash filesorter.sh "all-PR-reviews_json_main-reviews" "older_PRCR/"

# this returns no text after completion, but returns the prompt. 

```

You can check whether there are multiple-date versions of the file remaining or not using tab completion for a specific example. 

For example where initially we had two files:   
 - `all-PR-reviews_json_main-reviews__FlicAnderson-PR_test_2025-11-13`    
 - `all-PR-reviews_json_main-reviews__FlicAnderson-PR_test_2025-11-16`    
... after running the script, `ls` would show only `all-PR-reviews_json_main-reviews__FlicAnderson-PR_test_2025-11-16`.  


NOTE: Documentation supporting datasets, data processing and analysis requires further development!  See issue ticket [RSE-personas/#105](https://github.com/FlicAnderson/RSE-personas/issues/105) for further information


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
