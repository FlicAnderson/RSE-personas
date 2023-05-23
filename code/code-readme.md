# Code

This is where the code for the project will be held. 

### TESTS 

To run all pytest tests on code, from `coding-smart/code` folder, run:   

```commandline
(coding-smart-github) flic@persephone:~/coding-smart/code$ pytest test/
============================= test session starts ==============================
platform linux -- Python 3.10.9, pytest-7.3.1, pluggy-1.0.0
rootdir: /home/flic/coding-smart/code
plugins: anyio-3.5.0, cov-4.0.0
collected 5 items                                                              

test/test_repo_name_clean.py ...FF                                       [100%]

=================================== FAILURES ===================================
__________________________ test_repo_name_clean_comma __________________________

    def test_repo_name_clean_comma():
        # Arrange
    
        repo_example = 'https://github.com/edcarp/edcarp.github.io, https://github.com/ropensci/software-review'
    
        # Act & Assert
        with pytest.raises(ValueError):
>           repo_name_clean(repo_example)
E           TypeError: 'module' object is not callable

test/test_repo_name_clean.py:55: TypeError
________________________ test_repo_name_clean_semicolon ________________________

    def test_repo_name_clean_semicolon():
        # Arrange
    
        repo_example = 'https://github.com/edcarp/edcarp.github.io; https://github.com/ropensci/software-review'
    
        # Act & Assert
        with pytest.raises(ValueError):
>           repo_name_clean(repo_example)
E           TypeError: 'module' object is not callable

test/test_repo_name_clean.py:66: TypeError
=========================== short test summary info ============================
FAILED test/test_repo_name_clean.py::test_repo_name_clean_comma - TypeError: 'module' object is not callable
FAILED test/test_repo_name_clean.py::test_repo_name_clean_semicolon - TypeError: 'module' object is not callable
========================= 2 failed, 3 passed in 0.09s =========================
```
This example is currently showing my poor pytest test writing skills but is informative on running one set of tests at least.  
