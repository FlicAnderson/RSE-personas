"""Function to get release data (especially dates of releases) for a GitHub repo."""

import pandas as pd
import requests


def get_release_dates(repo_name, verbose=True):
    """
    Takes repo name, creates new dataframe of release info especially dates (pd.DataFrame object) for that repository.
    :param repo_name: cleaned `repo_name` string without GitHub url root or trailing slashes.
    :type: str
    :param verbose: print status info? Default= true
    :type: bool
    :return repo_releases: dataframe with release info including dates and versions if found for the repo.
    :type: pd.DataFrame
    """

    # if repo_name is None:
    #    raise TypeError('`repo_name` is empty. Please supply name of repo to retrieve release info for.')

    # get release dates
    base_releases_url = f"https://api.github.com/repos/{repo_name}/releases"
    api_response = requests.get(url=base_releases_url)

    try:
        if api_response.status_code == 200 and verbose:
            print(f"API response status OK: {api_response}")

        # pull data as json then convert to pandas dataframe for ease of use
        release_info = api_response.json()
        repo_releases = pd.DataFrame.from_dict(release_info)

        if len(repo_releases.columns) == 0:
            raise Exception(f"Repo {repo_name} contains NO releases.")

        if verbose:
            print(repo_releases.shape)

        # pull out release author username as new column in df.
        repo_releases["release_author"] = repo_releases[["author"]].apply(
            lambda x: [x.get("login") for x in x]
        )

        # drop unnecessary columns from df (including author: succeeded by new 'release_author' column)
        repo_releases = repo_releases.drop(
            columns=[
                "url",
                "assets_url",
                "upload_url",
                "html_url",
                "id",
                "author",
                "node_id",
                "target_commitish",
                "prerelease",
                "assets",
                "tarball_url",
                "zipball_url",
            ]
        )

        repo_releases["created_at"] = pd.to_datetime(
            repo_releases["created_at"], utc=True
        )
        repo_releases["published_at"] = pd.to_datetime(
            repo_releases["published_at"], utc=True
        )

        repo_releases["repo_name"] = repo_name
        # remaining columns aka $ repo_releases.columns:
        # Index(['tag_name', 'name', 'draft', 'created_at', 'published_at', 'body', 'release_author', 'repo_name'],
        #       dtype='object')

        if verbose:
            last_release = repo_releases.sort_values(
                by=["published_at"], ascending=False
            )
            last_release_date = pd.to_datetime(
                last_release["published_at"][0], utc=True
            )
            last_release_name = last_release["name"][0]
            print(
                f"There have been {len(repo_releases)} releases published at repo {repo_name}. The last release was {last_release_name}, released on {last_release_date}."
            )

        return repo_releases

    except:
        if api_response.status_code == 404:  # status NOT OK
            print(
                f"API ERROR: {api_response}. There may be no releases for this repo, or an API exception."
            )
            repo_releases = pd.DataFrame()
            return repo_releases
        else:
            if len(repo_releases.columns) == 0:
                print(
                    f"Repo {repo_name} contains NO releases."
                )  # This version prints, not the above if: exception()
            repo_releases = pd.DataFrame()
            return repo_releases
