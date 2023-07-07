# Code

This is where the code for the project will be held. 

### TESTS 

To run main pytest tests on code, from `coding-smart/` folder (ensuring all packages from requirements.txt are installed, especially `pytest`), run: `pytest tests/ --runxfail -v
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

## Possible Functions Required: 

#### General / Utility: 
- [ ] Parse list of urls to pull out repositories  
- [x] Clean repo url to get repo_name [repo_name_clean()](githubanalysis/processing/repo_name_clean.py)  
- [x] Authenticate to GitHub API using access token [setup_github_auth()](githubanalysis/processing/setup_github_auth.py)  
- [x] Connect to repo x through github api [get_repo_connection()](githubanalysis/processing/get_repo_connection.py)  
- [ ] RUN DATA PROCESSING WORKFLOW [clean_data.py](githubanalysis/processing/clean_data.py)
- [x] Write out data to file to avoid repeating API requests [write_out_repo_data()](githubanalysis/processing/write_out_repo_data.py) 

#### Issue Ticket Usage:  
- [ ] Check for issue ticket use at repo X   
- [x] Get all issue ticket info from repo X  [get_all_pages_issues()](githubanalysis/processing/get_all_pages_issues.py)
- [x] Get (number of) open issues from repo X (printed by get_all_pages_issues())
- [x] Get (number of) closed issues from repo X  (printed by get_all_pages_issues())
- [ ] Get issue X ticket author  
- [ ] Get assigned dev for issue X 
- [ ] Get closing author of issue X 
- [ ] Get issue X discussion  
- [ ] Calculate linked issues to issue X   
- [x] Calculate time to close issue X [calc_issue_close_time()](githubanalysis/analysis/calc_issue_close_time.py)
- [~] Calculate average time to close issue per dev [calc_per_dev_mean_close_time()](githubanalysis/analysis/calc_per_dev_mean_close_time.py)
- [ ] Calculate number of ticket authors in repo X   
- [ ] Calculate measure of issue ticket creation frequency     
- [ ] Calculate measure of issue ticket closure frequency     
- [ ] Plot average time to close issues in list   
- [ ] Plot number of issue ticket authors over time  
- [ ] Plot issue ticket creation over time for repo  
- [ ] Plot issue ticket closure over time [plot_repo_issues_data()](githubanalysis/visualization/plot_repo_issues_data.py)   

#### Pull Requests:
- [ ] Check for PR usage at repo X
- [ ] Check for PR closure rates over time at repo X []() 
- [ ] Get PRs for repo X  
- [ ] Get linked issues / PRs for issue X    
- [ ] Check PR code reviewed before merge  
- [ ] Count PR reviews assigned to each repo dev  
- [ ] Check PR link to branches  
- [ ] Check for pre-merge testing  

#### Commits:
- [ ] Calculate number of devs (committers) in repo X  
- 

#### Testing:  
- [ ] Check for 'tests' folder / 'test_*' / '*_test' file structure in repo X  
- [ ] Check for test package imports in repo X
- [ ] Check for 'regression' tests in repo X
- [ ] Check for 'unit' tests in repo X 
- [ ] Check for 'assertions' in repo X 
- [ ] Check for 'test coverage' calculation in repo X 

#### Code Documentation:  


#### Automation:  






## Concepts to Identify & Describe: 

Concepts: 
 - 'repo'  
 - 'PR' - (?)branched code tagged for checking before merge to main code  
 - 'code reviewer' - someone who marks PR as checked/approved before merge (?probably should not be the author of the PR?)
 - 'dev' - someone who commits to the repo  
 - 'main dev' - someone who may review PRs to code, contributes significant proportion of code commits, merges branches, 
 - 'project member' - someone who touches the repo (e.g. adds issue but does not commit, is listed as repo team member, may have various admin levels?; could include project management or PI who is not actively invovled in day to day?)   

Need to figure out how I can differentiate between devs and main devs, also things like "do documentation-only commits count as development for the purposes of assigning 'main dev' role?" 
