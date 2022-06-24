import os
import streamlit as st
import pandas as pd
import numpy as np
from data_analysis import plot_hist, plot_pie_chart
from cryptography.fernet import Fernet

link = st.secrets['url']

@st.cache(ttl=60)
def read_data(drop_nan=True):

    df = pd.read_csv(link)

    if drop_nan:
        df = df.dropna()

    return df

@st.cache(ttl=60)
def sum_data(df):
    players = pd.unique( df['Player'] )
    sum_df = pd.DataFrame( columns=['Player','Holes Played', 'Total Points'] )
    for player in players:
        played = len( df[ df['Player']==player ] )
        points = df[ df['Player']==player ]['Points'].sum()
        sum_df = sum_df.append( { 'Player' : player, 'Holes Played': played, 'Total Points': points }, ignore_index=True )
    return sum_df

def getfname( chart, var, filters=None, split=None ):
    chart_map = { 'Histogram': 'hist', 'Pie Chart': 'pie' }
    chartname = chart_map[chart]
    varname = var.replace(' ','_').lower()

    path = f'plots/{varname}'
    fname = f'{chartname}'

    if filters is not None:
        if len(filters.keys())>0:
            path += '/filters'
            path += '/' + ''.join( [filt.replace(' ','') for filt in filters.keys()] )
            for fkey, flst in filters.items():
                fname += '_f'+fkey.replace(' ','')
                if fkey == 'Player':
                    for pl in flst:
                        fname += pl.split()[0][0] + pl.split()[1][0]
                elif fkey == 'Par':
                    for hl in flst:
                        fname += str(hl)
                elif fkey == 'Course':
                    for cs in flst:
                        fname += cs
                else:
                    for el in flst:
                        fname += el.replace(' ','')

    if split is not None:
        fname += '_sp_' + split.replace(' ','_').lower()

    os.system(f'mkdir -p {path}')

    fname = f'{path}/{fname}.png'

    return fname

if __name__ == '__main__':

    st.set_page_config( page_title='GASH Cup 2022 Data Analysis',
                        page_icon='gsh-logo.jpg' )

    st.title('GASH Cup 2022 Data Analysis')

    #data_load_state = st.text('Loading data...       (hit R to refresh)')
    st.text('Data is cached for performance (hit R to refresh)')

    df = read_data()

    ### DATA STUFF HERE ###

    col1, col2 = st.columns(2)
    with col1:
        chart_option = st.selectbox('Select type of plot', ('Histogram','Pie Chart'), index=1)
    with col2:
        col_option = st.selectbox('Select variable to plot', ('Gross Score','Net Score', 'Gross Shots', 'Net Shots','Stableford Points','Hole','Player'), index=0 )
        col_option = col_option.replace('Stableford Points','Points')

    fcol1, fcol2, fcol3, fcol4 = st.columns(4)

    with fcol1:
        filter_players = st.multiselect('Filter Players', pd.unique(df['Player']) )
    with fcol2:
        filter_pars = st.multiselect('Filter Holes By Par', pd.unique(df['Par']) )
    with fcol3:
        filter_course = st.multiselect('Filter Course', pd.unique(df['Course']) )
    with fcol4:
        shots = ['Albatros','Eagle','Birdie','Par','Bogey','Double Bogey','Triple Bogey']
        sels = ['Blob']
        sels += [ f'Gross {shot}' for shot in shots if shot in pd.unique( df['Gross Score']) ]
        sels += [ f'Net {shot}' for shot in shots if shot in pd.unique( df['Net Score']) ]
        sels += [ f'{pt}pt' for pt in [0,1,2,3,4,5] ]
        filter_score = st.multiselect('Filter Score By', sels)

    # process filters
    filters = {}
    if len(filter_players)!=0:
        filters['Player'] = filter_players
    if len(filter_pars)!=0:
        filters['Par'] = filter_pars
    if len(filter_course)!=0:
        filters['Course'] = filter_course
    if len(filter_score)!=0:
        for filt in filter_score:
            if filt=='Blob':
                if 'Net Score' not in filters.keys():
                    filters['Net Score'] = []
                filters['Net Score'].append('Blob')
            if filt.startswith('Net'):
                if 'Net Score' not in filters.keys():
                    filters['Net Score'] = []
                filters['Net Score'].append( filt.split()[-1] )
            if filt.startswith('Gross'):
                if 'Gross Score' not in filters.keys():
                    filters['Gross Score'] = []
                filters['Gross Score'].append( filt.split()[-1] )
            if filt.endswith('pt'):
                if 'Points' not in filters.keys():
                    filters['Points'] = []
                filters['Points'].append( filt.split('pt')[0] )

    if chart_option == 'Histogram':
        split_by = st.selectbox('View Separate Contributions By', (None,'Player','Round','Course','Par','Points','Gross Score','Gross Shots','Net Score','Net Shots'))
        c1, c2 = st.columns(2)
        with c1:
            stack = st.checkbox('Stacked?', value=False)
        with c2:
            legend = st.checkbox('Legend?', value=True)
        fig = plot_hist(df, col_option, filters=filters, split=split_by, stacked=stack, legend=legend)
    elif chart_option == 'Pie Chart':
        split_by = None
        fig = plot_pie_chart(df, col_option, filters=filters)

    fname = getfname(chart_option, col_option, filters=filters, split=split_by)
    #st.write(fname)
    #fig.savefig(fname)
    #upload(fname)

    st.pyplot(fig)

    st.subheader('Raw Data')
    st.write(df)

    #import time
    #time.sleep(5)
    #make_charts(df)
