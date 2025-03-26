import pytest
from githubanalysis.processing.read_summary_stats_log import parse_log

import datetime


input = [
    "[2025-03-25 10:39:18,556] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/languages.",
    "[2025-03-25 10:39:18,918] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/stats/commit_activity.",
    "[2025-03-25 10:39:21,880] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/pulls?per_pg=1&state=all&sort=updated&direction=desc.",
    "[2025-03-25 10:39:22,433] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/issues?state=open&per_page=1.",
    "[2025-03-25 10:39:22,902] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/issues?state=closed&per_page=1.",
    "[2025-03-25 10:39:23,848] INFO:getting json via request url https://api.github.com/repos/openconnectome/m2g/commits?per_page=1.",
    "[2025-03-25 10:39:24,318] INFO:Stats for openconnectome/m2g: {'repo_name': 'openconnectome/m2g', 'initial_HTTP_code': 200, 'issues_enabled': True, 'repo_license': 'Apache-2.0', 'repo_visibility': True, 'repo_is_fork': False, 'devs': 25, 'repo_language': dict_keys(['Python', 'HTML', 'CSS', 'R', 'MATLAB', 'JavaScript', 'Shell', 'Nginx', 'C', 'C++', 'Makefile', 'M']), 'total_commits_last_year': 0, 'has_PRs': True, 'last_PR_update': datetime.datetime(2016, 1, 29, 21, 45, 2, tzinfo=datetime.timezone.utc), 'open_tickets': 16, 'closed_tickets': 205, 'repo_age_days': 5079, 'n_commits_main_branch': 1289}",
    "[2025-03-25 10:39:24,325] INFO:getting json via request url https://api.github.com/repos/LucijanaS/target-stars.",
    "[2025-03-25 10:39:24,648] INFO:API response at initial connection to LucijanaS/target-stars is <Response [200]>",
    "[2025-03-25 10:39:24,648] INFO:API response at initial connection to LucijanaS/target-stars for request https://api.github.com/repos/LucijanaS/target-stars is <Response [200]>.",
    "[2025-03-25 10:39:24,649] INFO:getting json via request url https://api.github.com/repos/LucijanaS/target-stars/contributors?per_page=1&anon=1.",
    "[2025-03-25 10:39:24,866] INFO:getting json via request url https://api.github.com/repos/LucijanaS/target-stars/languages.",
]

dict_keys = type(({}).keys())


def test_parse_log():
    exp_dict = {
        "repo_name": "openconnectome/m2g",
        "initial_HTTP_code": 200,
        "issues_enabled": True,
        "repo_license": "Apache-2.0",
        "repo_visibility": True,
        "repo_is_fork": False,
        "devs": 25,
        "repo_language": [
            "Python",
            "HTML",
            "CSS",
            "R",
            "MATLAB",
            "JavaScript",
            "Shell",
            "Nginx",
            "C",
            "C++",
            "Makefile",
            "M",
        ],
        "total_commits_last_year": 0,
        "has_PRs": True,
        "last_PR_update": datetime.datetime(
            2016, 1, 29, 21, 45, 2, tzinfo=datetime.timezone.utc
        ),
        "open_tickets": 16,
        "closed_tickets": 205,
        "repo_age_days": 5079,
        "n_commits_main_branch": 1289,
    }
    exp_name = "openconnectome/m2g"
    name, dict = parse_log(input)[0]
    assert exp_dict == dict
    assert exp_name == name
