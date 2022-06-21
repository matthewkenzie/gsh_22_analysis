import streamlit as st
import pandas as pd
import numpy as np
#from gsheetsdb import connect
from data_analysis import plot_hist, plot_pie_chart

# create google sheets connection
#conn = connect()

# perform SQL query on the google sheet
# st.cache will rerun when query changes or after 10 mins

link = st.secrets['url']

@st.cache
def read_data(drop_nan=True):
    #url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/'
    #protocol = f'export?gid={subsheet_id}&format=csv'

    #link = url + protocol

    df = pd.read_csv(link)
    #sheet_url = st.secrets['public_gsheets_url']
    #query = f'SELECT * FROM "{link}"'

    #rows = conn.execute(query)
    #df = pd.DataFrame( rows.fetchall() )
    #df.columns = rows.keys()

    #df = pd.read_sql( query, conn )

    if drop_nan:
        df = df.dropna()

    #df = df.astype( dtype={'Hole': np.int32, 'Par': np.int32},  )

    return df

@st.cache
def sum_data(df):
    players = pd.unique( df['Player'] )
    sum_df = pd.DataFrame( columns=['Player','Holes Played', 'Total Points'] )
    for player in players:
        played = len( df[ df['Player']==player ] )
        points = df[ df['Player']==player ]['Points'].sum()
        sum_df = sum_df.append( { 'Player' : player, 'Holes Played': played, 'Total Points': points }, ignore_index=True )
    return sum_df


st.title('GASH Cup 2022 Data Analysis')

#data_load_state = st.text('Loading data...       (hit R to refresh)')
st.text('Data is cached for performance (hit R to refresh)')

df = read_data()

sum_df = sum_data(df)

#st.write(sum_df)

#data_load_state.text('Loading data... done! (hit R to refresh)')

### DATA STUFF HERE ###

col1, col2 = st.columns(2)
with col1:
    chart_option = st.selectbox('Select type of plot', ('Histogram','Pie Chart'), index=1)
with col2:
    col_option = st.selectbox('Select variable to plot', ('Gross Score','Net Score', 'Gross Shots', 'Net Shots','Stableford Points','Hole'), index=0 )
    col_option = col_option.replace('Stableford Points','Points')

fcol1, fcol2, fcol3 = st.columns(3)

with fcol1:
    filter_players = st.multiselect('Filter Players', pd.unique(df['Player']) )
with fcol2:
    filter_pars = st.multiselect('Filter Holes By Par', pd.unique(df['Par']) )
with fcol3:
    filter_course = st.multiselect('Filter Course', pd.unique(df['Course']) )

# process filters
filters = {}
if len(filter_players)!=0:
    filters['Player'] = filter_players
if len(filter_pars)!=0:
    filters['Par'] = filter_pars
if len(filter_course)!=0:
    filters['Course'] = filter_course

if chart_option == 'Histogram':
    split_by = st.selectbox('View Separate Contributions By', (None,'Player','Round','Course','Par','Points','Gross Score','Gross Shots','Net Score','Net Shots'))
    c1, c2 = st.columns(2)
    with c1:
        stack = st.checkbox('Stacked?', value=False)
    with c2:
        legend = st.checkbox('Legend?', value=True)
    fig = plot_hist(df, col_option, filters=filters, split=split_by, stacked=stack, legend=legend)
elif chart_option == 'Pie Chart':
    fig = plot_pie_chart(df, col_option, filters=filters)

st.pyplot(fig)

st.subheader('Raw Data')
st.write(df)

