import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from pandas.errors import EmptyDataError

def plot_repo_issues_counts_devs(repo_data_df, repo_name, save_out=True, save_name='issues_counts_devs_plot', save_type='png', save_out_location='images/', verbose=True):
    """
    Plot issue ticket data from GitHub repositories.
    :param repo_data_df: data to plot
    :type: pd.DataFrame
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param save_out: save plot object to file? Default=True
    :type: bool
    :param save_name: filename prefix to save plot object as. Default='issues_data_plot'
    :type: str
    :param save_type: file type to save plot as ('pdf' or 'png') . Default='png'
    :type: str
    :param save_out_location: Desired file location path as string. Default = "data/"
    :type: str
    :param verbose: return status info. Default: True
    :type: bool
    :return plot: issue data scatterplot.
    :type: ?plot?
    """

    # verify input is df
    if not isinstance(repo_data_df, pd.DataFrame):
        raise TypeError('Ensure input data is pd.DataFrame format.')

    if repo_data_df.empty is True:
        raise EmptyDataError('There is no data in dataframe repo_data_df.')

    if repo_name is None:
        if repo_data_df.repo_name.nunique() == 1:
            repo_name = repo_data_df.repo_name[0]  # use first repo_name value
        elif repo_data_df.repo_name.nunique() > 1:
            repo_name = 'multiple repos'
            print('Multiple repositories included in dataset')
        else:
            raise ValueError('Cannot obtain repo_name from dataset `repo_data_df`')
    else:
        repo_name = repo_name  # from function arguments.

    if save_out:
        # check there's a save_name if saving out the plot.
        if save_name is None:  # this shouldn't occur hopefully as there's a default.
            raise ValueError('save_name must be supplied for plot filename.')
        if not isinstance(save_name, str):
            raise ValueError('save_name must be a string.')

        # which file format to save as?
        if save_type not in ('png', 'pdf'):
            raise ValueError('save_type must be one of "png" (default) or "pdf".')

        # verify save_out_location is valid
        save_path = Path(save_out_location)
        if save_path.exists() is False:
            raise OSError('Read-in file does not exist at path:', save_path)

    # todo: check 'assigned_devs' column exists, error if not

    # reshape dataset to make taller on 'assigned_devs' column (ie 1x row:[dev1, dev2]; -> 2x rows: dev1; dev2
    exploded_devs = repo_data_df.apply(pd.Series).explode(column='assigned_devs')

    # calculate 25% of assigned tickets
    all_closed = len(repo_data_df.index)
    total_assigned = len(repo_data_df[[bool(x) for x in repo_data_df.assigned_devs]])
    #non_assigned = all_closed - total_assigned
    non_assigned_text = f'{all_closed - total_assigned} Unassigned tickets (N = {all_closed})'

    if verbose:
        print(exploded_devs['assigned_devs'].value_counts(dropna=False))  # print per-dev assignment counts

    # do actual plotting:
    exploded_devs['assigned_devs'].value_counts().plot.bar(column='assigned_devs', color='red', label='assigned tickets')

    plt.xlabel("Assigned To user")
    plt.ylabel("Number of issue tickets assigned")
    plt.title(f"Number of assigned issue tickets per dev for repo: {repo_name}")
    plt.axhline(y=(total_assigned*0.25), linestyle='--', color='black', label=f'25% ({total_assigned}) assigned issues')  # plot line at 25% of all closed assigned tickets
    plt.plot([], [], ' ', label=non_assigned_text)  # Create empty plot with blank marker containing the extra label
    plt.legend(loc='upper right')

    if save_out:
        # create filename to use from repo_name
        save_out_filename = f'{save_name}__{repo_name.replace("/", "_")}'

        # build path + filename + file extension string
        plot_file = f'{save_out_location}{save_out_filename}.{save_type}'

        plt.savefig(plot_file, bbox_inches='tight')
    plt.close()
