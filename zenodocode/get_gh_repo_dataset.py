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



# this bit
if __name__ == "__main__":
    main()
