import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from paramiko import SSHClient, AutoAddPolicy
from cryptography.fernet import Fernet
from data_analysis import plot_hist, plot_pie_chart
from gsh_web_app import read_data, getfname
import time

def upload(fnames, mkdirs=False):

    key = st.secrets['key']
    fernet = Fernet(key.encode())
    password = fernet.decrypt( st.secrets['encode'].encode() ).decode()
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('lxplus.cern.ch',username=st.secrets['user'], password=password)
    remote = '/eos/user/m/mkenzie/www/gsh/data'
    ## put files (directories need to exist)
    sftp = ssh.open_sftp()
    for fname in fnames:
        sftp.put(fname, f'{remote}/{fname}')
    sftp.close()
    ssh.close()

def save_hist(df, variable, filters=None, split=None, stacked=False, legend=True, upload=False):

    fig = plot_hist(df, variable, filters=filters, split=split, stacked=stacked, legend=legend)
    hname = getfname('Histogram', variable, filters=filters, split=split)
    if stacked:
        hname = hname.replace('.png','_stack.png')
    if legend:
        hname = hname.replace('.png','_leg.png')
    fig.savefig(hname)
    plt.close(fig)
    if upload:
        upload(hname)
    return hname

def save_pie(df, variable, filters=None, upload=False):

    fig = plot_pie_chart(df, variable, filters=filters)
    pname = getfname('Pie Chart', variable, filters=filters)
    fig.savefig(pname)
    plt.close(fig)
    if upload:
        upload(pname)
    return pname

def make_charts(df):
    out_df = pd.DataFrame( columns=['Player','Course','Variable','Chart','Image'] )
    head_url = 'https://mkenzie.web.cern.ch/mkenzie/gsh/data/'
    upload_fs = []

    players = ['All'] + list(pd.unique( df['Player'] ) )
    courses = ['Any'] + list(pd.unique( df['Course'] ) )
    variables = ['Gross Score','Net Score','Gross Shots','Net Shots', 'Points','Player']
    splits = ['None','Player','Round']

    # loop players
    for player in players:
        filters = {}
        if player != 'All':
            filters['Player'] = [ player ]
        # loop courses
        for course in courses:
            if course != 'Any':
                filters['Course'] = [ course ]
            # loop variables
            for variable in variables:
                if player != 'All' and variable == 'Player':
                    continue
                row = { 'Player': player, 'Course': course, 'Variable': variable }
                # loop splits for histograms
                for split in splits:
                    if variable=='Player':
                        continue
                    if split == 'None':
                        hname = save_hist(df, variable, filters=filters, split=None, stacked=False, legend=False)
                        out_df = out_df.append( {**row, **{'Chart': 'Histogram', 'Image': head_url+hname} }, ignore_index=True )
                    else:
                        if split == 'Player' and player != 'All':
                            continue
                        if split == 'Round' and course != 'Any':
                            continue
                        if split == 'Player' and variable == 'Player':
                            continue

                        # not stacked
                        hname = save_hist(df, variable, filters=filters, split=split, stacked=False, legend=True)
                        out_df = out_df.append( {**row, **{'Chart': f'Histogram by {split}', 'Image': head_url+hname}}, ignore_index=True )
                        upload_fs.append(hname)
                        # stacked
                        hname = save_hist(df, variable, filters=filters, split=split, stacked=True, legend=True)
                        out_df = out_df.append( {**row, **{'Chart': f'Stacked Histogram by {split}', 'Image': head_url+hname}}, ignore_index=True )
                        upload_fs.append(hname)
                # then pie charts
                if variable != 'Player':
                    pname = save_pie(df, variable, filters=filters)
                    out_df = out_df.append( {**row, **{'Chart': 'Pie Chart', 'Image': head_url+pname}}, ignore_index=True )
                    upload_fs.append(pname)

                if player == 'All' and variable == 'Player':
                    for score in ['Blob','Eagle','Birdie','Par','Bogey','Double Bogey','Triple Bogey']:
                        filters['Net Score'] = [ score ]
                        pname = save_pie(df, variable, filters=filters)
                        out_df = out_df.append( {**row, **{'Chart': f'Pie Chart {score}s', 'Image': head_url+pname}}, ignore_index=True )
                        upload_fs.append(pname)


    os.system('mkdir -p csv')
    out_df.to_csv( 'csv/AppAnalysis.csv' )

    return out_df, upload_fs

def unique_dirs(upload_fs):
    unique = set()
    for fil in upload_fs:
        path, base = os.path.split(fil)
        unique.add(path)
    return unique

if __name__ == '__main__':
    st.title('GASH Cup 2022 Data Synch')

    synchtime = 5
    st.text(f'Data is synched every {synchtime} minutes')

    run = True
    while run:
        st.write('Downloading data...')
        df = read_data()
        st.write('Downloading data... done')
        st.write('Making charts...')
        out_df, upload_fs = make_charts(df)
        st.write('Making charts... done')
        st.write('Uploading...')
        with open('dirlist.txt','w') as f:
            for uniq in unique_dirs(upload_fs):
                f.write(uniq+'\n')
        upload( upload_fs, mkdirs=False )
        st.write('Uploading... Done.')
        st.write( out_df )
        st.write('Waiting for next synch')
        print('Waiting')
        run = False
        time.sleep(synchtime*60)
