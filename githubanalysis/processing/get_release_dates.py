""" Function to get release data (especially dates of releases) for a GitHub repo."""

import pandas as pd
import requests


def get_release_dates(repo_name, config_path='githubanalysis/config.cfg', per_pg=100, verbose=True):
    """
    Takes repo name, creates new dataframe of release info especially dates (pd.DataFrame object) for that repository.
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param config_path: filepath of config.cfg file containing GitHub Access Token. Default='githubanalysis/config.cfg'.
    :type: str
    :param verbose: print status info? Default= true
    :type: bool
    :return repo_releases: dataframe with release info including dates and versions if found for the repo.
    :type: pd.DataFrame
    """

    if(repo_name is None):
        raise TypeError('`repo_name` is empty. Please supply name of repo to retrieve release info for.')

    # get release dates
    base_releases_url = f"https://api.github.com/repos/{repo_name}/releases"
    api_response = requests.get(url=base_releases_url)

    if api_response == 404:
        # status NOT OK
        print("API ERROR: Resource not found. There may be no releases for this repo")

    if api_response == 200:
        # status OK

        # pull data as json then convert to pandas dataframe for ease of use
        release_info = api_response.json()
        repo_releases = pd.DataFrame.from_dict(release_info)

        # pull out release author username as new column in df.
        repo_releases['release_author'] = repo_releases[['author']].apply(lambda x: [x.get('login') for x in x])

        # drop unnecessary columns from df (including author: succeeded by new 'release_author' column)
        repo_releases = repo_releases.drop(
            columns=['url', 'assets_url', 'upload_url', 'html_url', 'author', 'target_commitish', 'prerelease',
                     'assets', 'tarball_url', 'zipball_url']
        )
        # remaining columns aka $ repo_releases.columns:
        # Index(['id', 'node_id', 'tag_name', 'name', 'draft', 'created_at', 'published_at', 'body', 'release_author'],
        #       dtype='object')

        return repo_releases
