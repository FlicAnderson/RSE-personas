""" Workflow for getting GitHub repo urls from Zenodo to create a 'Research Software repo dataset'."""

import sys
import zenodocode.setup_zenodo_auth as znconnect
import zenodocode.get_gh_urls as zngetghurls

def main():
    """
    get github urls
    process gh urls
    write out dataset for input to githubanalysis code
    """

    znconnect.setup_zenodo_auth(config_path='zenodocode/zenodoconfig.cfg', verbose=True)

    # get github urls

    zngetghurls.get_gh_urls(config_path='zenodocode/zenodoconfig.cfg', per_pg=20, total_records=100, filename='gh_urls', write_out_location='data/', verbose=True)

    # process gh urls

        # run summarise_repo_stats() on 1 repo name (X).

        # collect repo_stats for X, add to store (create new record in pandas.df from dict repo_stats)


        # run check_repo_eligibility in the pandas.df

        # collate eligible repos; drop ineligible repos.


    # write out dataset for input to githubanalysis code



# this bit
if __name__ == "__main__":
    main()
