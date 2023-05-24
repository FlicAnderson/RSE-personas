# Code

This is where the code for the project will be held. 

### TESTS 

To run main pytest tests on code, from `coding-smart/` folder (ensuring all packages from requirements.txt are installed, especially `pytest`), run: `pytest tests/`   

```commandline
(coding-smart-github) flic@persephone:~/coding-smart$ pytest tests/
========================================== test session starts ==========================================
platform linux -- Python 3.10.9, pytest-7.3.1, pluggy-1.0.0
rootdir: /home/flic/coding-smart
plugins: anyio-3.5.0, cov-4.0.0
collected 4 items                                                                                       

tests/test_repo_name_clean.py ....                                                                [100%]

=========================================== 4 passed in 0.01s ===========================================
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

