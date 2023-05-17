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

- assertions used  
- off-the-shelf unit testing library

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
    
 - use of asserts / testing expectations  
    - use of {testthat}  
    - stopifnot() 
    - stop()  
    - tryCatch()  
    - testing input data types

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

 - packages / envs are managed and versioned  
    - use of {packrat} / {renv} / etc packages for managing packages and dependencies  
    - code which creates versioning metadata to output files  
    - logging files generated  
    - info in docs about what dependencies/requirements needed and which versions esp.  
    - docker files  
    - singularity files  
    - conda env files  

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

