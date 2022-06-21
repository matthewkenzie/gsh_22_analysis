import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_theme()
import streamlit as st

def data_mapper(vals):
    unique = np.sort( np.unique(vals) )

    map_dict = {}

    if 'Par' in unique or 'Birdie' in unique or 'Bogey' in unique or 'Double Bogey' in unique:
        order = [ 'Albatros', 'Eagle', 'Birdie', 'Par', 'Bogey', 'Double Bogey', 'Triple Bogey', 'Blob' ]
    else:
        order = list(unique)

    map_dict = { key: i+0.5 for i, key in enumerate(order) }

    ret = np.empty_like(vals)

    for i, val in enumerate(vals):
        ret[i] = order.index(val)+0.5

    return ret, order, map_dict

def data_mapping(vals):
    if type(vals)==list:
        return [ data_mapper(val) for val in vals ]
    else:
        return data_mapper(vals)


def plot_hist(df, column, filters=None, split=None, stacked=False, legend=True, ax=None):
    """ plot histogram of data

    Parameters
    ----------
    df : pandas.DataFrame
        the data
    column : str
        name of the data column to plot
    filters : dict of str to str, optional
        mapping of key and values to filter on
    split : str, optional
        split to apply (different series) by
        column name
    """

    if column not in df.columns:
        return

    if filters is not None and type(filters)!=dict:
        return

    if split is None:
        legend = False

    data = df

    if filters is not None:

        for key, value in filters.items():

            if type(value)==list:
                data = data[ data[key].isin(value) ]
            else:
                data = data[ data[key]==value ]

    if ax is None:
        fig = plt.figure()
        ax = plt.gca()

    vals = data[column].values
    vals, xlabels, map_dict = data_mapping(vals)

    labels = None
    rwidth=0.8

    if split is not None:
        if split in df.columns:
            labels = np.unique( data[split].values )

            vals = [ np.vectorize(map_dict.get)(data[ data[split]==label ][column].values) for label in labels]


    ax.hist( vals, bins=len(xlabels), range=(0,len(xlabels)), label=labels, rwidth=rwidth, stacked=stacked )

    ax.set_xticks(np.arange(len(xlabels))+0.5)

    xlabels = [ str(xlabel).replace(' ','\n') for xlabel in xlabels ]
    ax.set_xticklabels(xlabels)

    if labels is not None and legend:
        ax.legend(title=split)

    column = column.replace('Points','Stableford Points')
    ax.set_title(column)

    if ax is None:
        fig.tight_layout()

    fig = plt.gcf()
    return fig

def plot_pie_chart(df, column, filters=None, ax=None):

    if column not in df.columns:
        return

    if filters is not None and type(filters)!=dict:
        return

    data = df

    if filters is not None:

        for key, value in filters.items():

            if type(value)==list:
                data = data[ data[key].isin(value) ]
            else:
                data = data[ data[key]==value ]

    if ax is None:
        fig = plt.figure()
        ax = plt.gca()

    vals = data[column].values
    vals, xlabels, map_dict = data_mapping(vals)
    nh, xe = np.histogram( vals, bins=len(xlabels), range=(0,len(xlabels)) )

    mask = nh!=0
    nh = nh[mask]
    xlabels = np.array(xlabels)[mask]

    ax.pie(nh,labels=xlabels, autopct='%1.1f%%')

    column = column.replace('Points','Stableford Points')
    ax.set_title(column)

    if ax is None:
        fig.tight_layout()

    fig = plt.gcf()
    return fig

#df = read_data()

#st.write('Raw data')
#st.write(df)

#fig = plot_hist(df, 'Gross Score', filters={'Player': ['Will Cherry', 'Matt Kenzie', 'Chris Rogers']}, split='Player' )
#st.pyplot(fig)

#plot_hist(df, 'Gross Shots')
#plot_hist(df, 'Net Shots')
#plot_hist(df, 'Gross Score')
#plot_hist(df, 'Net Score')

#plot_hist(df, 'Gross Score', filters={'Player': ['Will Cherry', 'Matt Kenzie', 'Chris Rogers']}, split='Player' )
#plot_hist(df, 'Gross Score', split='Course' )
#plot_hist(df, 'Points')



#plt.show()
