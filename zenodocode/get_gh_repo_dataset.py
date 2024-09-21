"""Workflow for getting GitHub repo urls from Zenodo to create a 'Research Software repo dataset'."""

import zenodocode.setup_zenodo_auth as znconnect
import zenodocode.get_zenodo_ids as zngetids
import zenodocode.get_gh_urls as zngetghurls


def main():
    """
    get github urls
    process gh urls
    write out dataset for input to githubanalysis code
    """

    access_token = znconnect.setup_zenodo_auth(
        config_path="zenodocode/zenodoconfig.cfg", verbose=True
    )[1]

    # get zenodo IDs
    zngetids.get_zenodo_ids(
        auth=access_token,
        per_pg=20,
        total_records=1000,
        filename="zn_ids",
        write_out_location="data/",
        verbose=True,
    )

    # get github urls

    zngetghurls.get_gh_urls(
        auth=access_token,
        zenodo_ids_file="data/zn_ids.csv",
        per_pg=100,
        total_records=1000,
        filename="gh_urls",
        write_out_location="data/",
        verbose=True,
    )


# this bit
if __name__ == "__main__":
    main()
