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

