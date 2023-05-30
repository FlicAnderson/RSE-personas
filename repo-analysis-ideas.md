# Repo Analysis Ideas

## AIM: Looking for evidence of SE dev practices.  
## QUESTIONS TO ANSWER: 
 * which SE techs improve RS or RS development?  
 * how do they improve it?  
 * when is it most useful to use these techs? (e.g. intial construction? refactoring? maintenance?)  
 * by how much do they improve RS/devXP?  
 * why do people use/not use these techs?  


### SE TECHS: Issue Tracking  
 - issue tracking used  
 - issue tracking linked to PRs  
 - issue tracking linked to other issues  
 - issue tracking linked to branches  
 - issues assigned to dev  
 - issues have labels  
 - issues well-defined and helpful; limited in scope; not conceptual     

### SE TECHS: PRs  
 - PRs used  
 - PRs reviewed before merge! 
 - PR reviews assigned to dev  
 - PRs linked to issues & branches  
 - PRs checked with regression testing before merge

### SE TECHS: Testing  
- unit testing  
    - test unit of behaviour, not unit of implementation. (e.g. test 'data -> plot' rather than 'data' and 'plot')  
- assertions used  
- test coverage  
    test coverage should be high - 
- off-the-shelf unit testing library  
- small testable units, with integration tests and functional tests to check everything works together  

### SE TECHS: Version Control  
- version control is used  (e.g. git repos)

### SE TECHS: Automate 
- are workflows automated? e.g. build tools, github actions etc  
- scripts used  

### SE TECHS: Defensive Programming  

 - documenting code   
    - evidence of roxygen  
    - docstrings  
    - comments in functions  
    - examples of use of function documented w/in function  
    - docs/ folder  
    - repo wiki  
    - functions contain help()/--help info equiv  
    - sphinx / knitr / RMarkdown rendering from webhooks etc   
    - has a vignette or tutorial or demo or similar  
    - function may have a class (functionname).doc in python  
    - code documentation is TRUE and accurate  
    
 - use of asserts / testing expectations  
    - use of {testthat}  
    - stopifnot() 
    - stop()  
    - tryCatch()  
    - testing input data types  
    - test the code YOU write, not other people's code (eg don't test external libraries unless TOTALLY necessary)  

 - external code use is explicit  
    - package::function() syntax in R  
    - name external packages used  
    - requirements/importing info is clear  
    - doesn't use 'require()' for packages

 - functions are modular and orthoganal and SHORT  
    - function doesn't contain HUGE nLOC of non-function-call code 
      - (ie big function chunks should call OTHER functions, 
        rather than lots of NEW non-function code) 
    - lack of repeating code / copypasta from elsewhere/'code repeats' 
    - each function does ONE task  
    - "low coupling and high cohesion" - unrelated parts don't mix; related parts can talk easily  
    - function is short (not more than 20-30 lines of code max)  
    - (modules are ~500 lines max length)
    - code may use pipes / chaining operators and functions to combine smaller functions  
    - logic is broken out into separate functions (rather than mixing long code with lots of logic - harder to test/understand side-effects)  
    - evidence of refactoring  (might have mentions of )

 - packages / envs are managed and versioned  
    - use of {packrat} / {renv} / etc packages for managing packages and dependencies  
    - code which creates versioning metadata to output files  
    - logging files generated  
    - info in docs about what dependencies/requirements needed and which versions esp.  
    - docker files  
    - singularity files  
    - conda env files  
    - 'globals are bad'  
    - ROpenci / sim communities may have a specific 'way' of managing 

 - software is itself packaged  
    - DESCRIPTION folder  
    - code/ or src/ folder 
    - docs/ folder etc  
    - data/ folder  
    - package can be installed / has installation docs  
    - is supported in package repos e.g. CRAN, bioconda channels etc.  
    - repo structure follows package format for that language  
    - loading instructions there  

 - follows a style and uses tools to verify/conform  
    - uses linters  {lintR}; {styler}; pylint; etc 
    - lists linters in package dependencies or includes them in conda envs etc  
    - details on how to follow repo/project style in docs  
    - code in repo is stylistically consistent to itself  
    - correct assignment operator (e.g. <- not = in R)   
    - indentation is consistent  
    - not too many levels of indentation (e.g no more than 1 or 2 levels in) aaro readability 
    - style guide (PEP8 for python)
    - 

 - use of user-defined non-default error messages / user-friendly error handling   
    - message() used  
    - non-default error messages present in code  
    - uses system status output codes e.g. 0, 100, 200  
    - troubleshooting present in docs  
    - conditionals present &  condition handling is used  
    - arguments handled  
    - stop() used to throw errors (tho this is possibly used for assertions tbh)  
    - tryCatch()  
    - checking arguments of functions for validity etc  
   
 - functions have explicit returns  
    - uses return in python  
    - use return() in R  
    - especially use return() 'if returning early' (e.g. for errors / conditional situations)   
    - avoid multiple return statements w/in the same function body (e.g. R doesn't allow this I think...)


- YAGNI: You Ain't Gonna Need It  
    - commented out code should be removed 
    - code that doesn't run / for future cases should be removed  
    - code is bad. Try to have as little as possible. (less maintenance, potential for error) - means high LOC isn't a great metric for 'good big project' as REALLY GOOD projects shouldn't have HUGE codebases... :D  

- DRY: Don't Repeat Yourself (or others)  
    - use existing types and methods, it's likely they'll be faster than writing your own  
    - (it's ok to repeat yourself a bit in tests tbh - tests are used individually rather than being part of a system you're trying to build)   



 - (from SWEBOK: Construction) SOFTWARE CONSTRUCTION FUNDAMENTAL: minimizing complexity  
    - writing simple code  
    - using standards  
    - modular design  
    - etc.  

 - (from SWEBOK: Construction) SOFTWARE CONSTRUCTION FUNDAMENTAL: anticipating change  
    - expecting changes in codebase and environment 
    - build extensible software  

 - (from SWEBOK: Construction) SOFTWARE CONSTRUCTION FUNDAMENTAL: constructing for verification  
    - building for maximum bug find/fixability  
    - following coding standards  
    - code reviews  
    - unit tetsing  
    - automated testing  
    - avoiding/restricting complex/hard to understand language structures etc  

 - (from SWEBOK: Construction) SOFTWARE CONSTRUCTION FUNDAMENTAL: reuse  
    - using existing libraries    
    - using existing modules  
    - using other code or 'commercial off-the-shelf' bits    
    - 'construction FOR reuse'  
    - 'construction WITH reuse'  

 - (from SWEBOK: Construction) SOFTWARE CONSTRUCTION FUNDAMENTAL: standards in construction  
    - applying dev standards (may be internal or external)  
    - language choice  
    - usage standards  
    - 'communication standards' - e.g. doc formats/contents  
    - languages ()

## Ideas to investigate: 

Come up with hypotheses, and then visualise these kinds of things to see whether there's other sources of info to verify this (e.g. ask folks). 
e.g. "if there's lots of opening/closing of issue tickets, but few code-based commits (e.g. low additions/deletions), does this show that a repo is in maintenance mode?" 
then write code to get the rates of open/close or addition/deletions across a certain window of time, then apply code to a repo in known mode (e.g. 'maintenance mode'), and see if it detects it.

Easy Qs:  

Q: does repo use issue tracking in github? (should be easy to determine)  
A: cannot use `has_issues` boolean, as this merely shows whether issues are enabled (for example https://github.com/FlicAnderson/20230215-JournalClub-BestPractices/issues has never had any issues, but `has_issues` returns True because they are enabled in repo settings. See: [repos parameter docs](https://docs.github.com/en/rest/repos/repos?apiVersion=2022-11-28)). 
Instead must try something else.  

Q: is issue tracking used by all devs in team? (cf issue authors and commit authors?)   

Q: is issue tracking currently stagnant or active? (slightly more detailed than 'is/is not used', but might look at rate of closing/opening within N time period)  

Q: are all issues closed by the opening author? (if not a 1-person dev team, if all issues are closed by the person who opens them is that a project management choice? Or is there no cross-working by devs?)  

Q: are issues always assigned to a dev? (is there a field for assignment/responsibility?)  

Medium Qs:  
Q: at which stage of the sw lifecycle / sw project is issue tracking used? (perhaps could look at additions/deletions in commits over time? e.g. frequent commits possibly = construction, lots of churn in code = construction, less churn = maintenance?, lots of issue tickets but no commits = design / requirements / project mgmt / end of support?)  

Q: Are PRs linked to issues? (if PRs are listed amongst issue tickets in GH api, need separate PR field to distinguish. How could I find linking info? How are links recorded in the GH system?)  
Q: how does issue ticket open/closing/progress relate to development surges/effort? (again, addition/deletions in commits cf. issue dates - how would I deal with dev-breaks like 'christmas hols' rather than 'end of project' or 'prolonged lull in development'?)  

Hard Qs:  
Q: does repo use non-GH methods of tracking issues? (harder to identify)   
Q: what kinds of information are held in issues? (this could be things like 'code approaches tried', links to similar issues which may have the same root or could all be fixed in the same development sweep, does issue discussion include code, how many people are involved in issue ticket discussion)  
