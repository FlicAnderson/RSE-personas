import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from pandas.errors import EmptyDataError


def plot_repo_issues_data(repo_data_df, repo_name, xaxis='ticket_number', add_events=False, save_out=True, save_name='issues_data_plot', save_type='png', save_out_location='images/'):
    """
    Plot issue ticket data from GitHub repositories.
    :param repo_data_df: data to plot
    :type: pd.DataFrame
    :param repo_name: cleaned `repo_name` string without github url root or trailing slashes.
    :type: str
    :param xaxis: What to plot on x-axis: 'ticket_number' / 'project_length' /
    :type: str
    :param add_events: Plot release dates as vertical line? Default: False
    :type: bool
    :param save_out: save plot object to file? Default=True
    :type: bool
    :param save_name: filename prefix to save plot object as. Default='issues_data_plot'
    :type: str
    :param save_type: file type to save plot as ('pdf' or 'png') . Default='png'
    :type: str
    :param save_out_location: Desired file location path as string. Default = "data/"
    :type: str
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


    if xaxis == 'ticket_number':
        # do actual plotting:
        (
            sns.set_theme(),
            sns.set_palette('colorblind'),
            sns.lmplot(x='number', y='close_time', data=repo_data_df,
                       hue='pull_request_bool',
                       height=5,
                       legend=False,
                       #ci=95,  # Confidence Interval %; can use 'sd' for standard deviations instead
                       scatter_kws={'alpha':0.65},
                       line_kws={'lw': 1.5}   #'color': 'red'
                        )
            .set(title=f"Time in days to close GitHub issues from {repo_name}",
                 xlabel="GitHub Issue Ticket Number",
                 ylabel="Time to Close Issue (days)"
                 )
            .add_legend(title="Pull Requests?"),
            plt.axhline(y=np.mean(repo_data_df.close_time), linestyle = '--',
                     color='black')  # add mean line with average close time for this set of issues

        )



    if xaxis == 'project_time':
        # plot:
        sns.set_theme()
        sns.set_palette('colorblind')

        g = sns.FacetGrid(data=repo_data_df, col='pull_request_bool', hue='pull_request_bool', height=5)
        g.map(sns.scatterplot, 'days_since_start', 'close_time')
        g.set(title=f"Time (days) to close at {repo_name}")
        g.set_axis_labels("Time Since Repo Creation (days)", "Time to Close Issue (days)")
        g.add_legend(title="Pull Requests?")
        g.refline(y=np.mean(repo_data_df.close_time), linestyle='--',
                  alpha=0.5)  # add mean line w/ average close time for repo

        if add_events is not False:
            for event in add_events:
                g.refline(x=event, ymin=0, ymax=1, color='black', linestyle=':', alpha=0.75)


    if save_out:
        # create filename to use from repo_name
        save_out_filename = f'{save_name}_{xaxis}__{repo_name.replace("/", "_")}'

        # build path + filename + file extension string
        plot_file = f'{save_out_location}{save_out_filename}.{save_type}'

        plt.savefig(plot_file, bbox_inches='tight')
        plt.close()

    else:

        plt.show()
        plt.close()
