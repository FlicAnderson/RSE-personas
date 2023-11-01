""" Checks whether given GitHub repository is eligible for analysis."""

import githubanalysis.processing.setup_github_auth as ghauth


def check_repo_eligibility(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Checks whether given GitHub repository meets eligibility
    criteria for analysis in coding-smart study when given
    'username' and 'repo_name' repository name. Returns bool.

    NOTE: Requires `access_token` setup with GitHub package.

    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: file path of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param per_pg: number of items per page in paginated API requests. Default=100, overwrites GitHub default 30.
    :type: int
    :param verbose: return status info. Default: True
    :type: bool
    :returns: repo_eligible
    :type: bool

    Examples:
    ----------
    >>> check_repo_eligibility('riboviz/riboviz')
    TODO
    """

    # This function will require output from githubanalysis.processing.summarise_repo_stats() function.
    # Will return repo_eligible = True if repo meets inclusion/exclusion criteria.
        # Criteria should be set either in separate config file or as function arguments (ease of use/reproducibility)
    # This function MAY sit better outside of main analysis 'pipeline'
        # it could be used to output eligible repo names to separate csv file.
        # once repo has been established to be eligible, then probably unlikely to need to rerun this on same repo?
        # Perhaps consider this more as a stand alone tool?

    # Dev Numbers:
        # repo has > 1 dev
        # repo has < 1000 devs

    # Commits:
        # > 100 commits? > 500?

    # Has PRs:
        # has PRs

    # Is RS:
        # (will be TRUE since the gh repo url should have come via zenodocode therefore has associated DOI)

    # Issue Tickets:
        # uses issue tickets
        # has > 10 issue tickets

    # Recent Activity:
        # has commit within last 12 months? 18 months?
        # last PR activity within last 12 months?
    
    # Repo Age:
        # repo is established, >3 years old.

    # Licence:
        # has open license allowing me to work w/ it

    # Accessibility:
        # repo is set to public

    # Repo Content:
        # repo contains code, not just docs or data.
        # look for file endings.

    # Repo Language:
        # contains some of: python, (shell?), (R?), java, C, C++, (FORTRAN???)

    # Repo Architecture:
        # Not HPC only; ideally intended to run on desktops, moderate servers, NOT HPC systems.
        # exclude any repos with scheduler code ? submission scripts for HPC architecture?
