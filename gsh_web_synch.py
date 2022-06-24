import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from paramiko import SSHClient, AutoAddPolicy
from cryptography.fernet import Fernet
from data_analysis import plot_hist, plot_pie_chart
from gsh_web_app import read_data, getfname
import time
from argparse import ArgumentParser

def upload(fnames, mkdirs=False, prog=True, stream=st):

    key = st.secrets['key']
    fernet = Fernet(key.encode())
    password = fernet.decrypt( st.secrets['encode'].encode() ).decode()
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(AutoAddPolicy())
    ssh.connect('lxplus.cern.ch',username=st.secrets['user'], password=password)
    remote = '/eos/user/m/mkenzie/www/gsh/data'
    ## put files (directories need to exist)
    sftp = ssh.open_sftp()
    if prog:
        bar = stream.progress(0.)
        tot = len(fnames)
    for i, fname in enumerate(fnames):
        sftp.put(fname, f'{remote}/{fname}')
        if prog:
            bar.progress( i/tot )
    if prog:
        bar.progress(1.)
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

def make_charts(df, tot=None, stream=st):
    out_df = pd.DataFrame( columns=['Player','Course','Variable','Chart','Image'] )
    head_url = 'https://mkenzie.web.cern.ch/mkenzie/gsh/data/'
    upload_fs = []

    #players = ['All'] + list(pd.unique( df['Player'] ) )
    #courses = ['Any'] + list(pd.unique( df['Course'] ) )
    # need these so it makes blank charts when no scores have been added
    players = ['All', 'Adam Hunter', 'AJ Paul', 'Alex Moffatt', 'Chris Rogers', 'Dan Bruton', 'Elliott Grigg', 'Matt Kenzie', 'Rob Campain', 'Stu Treasure', 'Will Cherry']
    courses = ['Any','Constable', 'Gainsborough']
    variables = ['Gross Score','Net Score','Gross Shots','Net Shots', 'Points','Player']
    splits = ['None','Player','Round']

    if tot is not None:
        prog = stream.progress(0)
        ncomp = 0

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
                        out_df = out_df.append( {**row, **{'Chart': 'Histogram', 'Image': head_url+hname+'?v=2'} }, ignore_index=True )
                        upload_fs.append(hname)
                        if tot is not None:
                            ncomp += 1
                            prog.progress( ncomp/tot )
                    else:
                        if split == 'Player' and player != 'All':
                            continue
                        if split == 'Round' and course != 'Any':
                            continue
                        if split == 'Player' and variable == 'Player':
                            continue

                        # not stacked
                        hname = save_hist(df, variable, filters=filters, split=split, stacked=False, legend=True)
                        out_df = out_df.append( {**row, **{'Chart': f'Histogram by {split}', 'Image': head_url+hname+'?v=2'}}, ignore_index=True )
                        upload_fs.append(hname)
                        if tot is not None:
                            ncomp += 1
                            prog.progress( ncomp/tot )
                        # stacked
                        hname = save_hist(df, variable, filters=filters, split=split, stacked=True, legend=True)
                        out_df = out_df.append( {**row, **{'Chart': f'Stacked Histogram by {split}', 'Image': head_url+hname+'?v=2'}}, ignore_index=True )
                        upload_fs.append(hname)
                        if tot is not None:
                            ncomp += 1
                            prog.progress( ncomp/tot )
                # then pie charts
                if variable != 'Player':
                    pname = save_pie(df, variable, filters=filters)
                    out_df = out_df.append( {**row, **{'Chart': 'Pie Chart', 'Image': head_url+pname+'?v=2'}}, ignore_index=True )
                    upload_fs.append(pname)
                    if tot is not None:
                        ncomp += 1
                        prog.progress( ncomp/tot )

                if player == 'All' and variable == 'Player':
                    for score in ['Blob','Eagle','Birdie','Par','Bogey','Double Bogey','Triple Bogey']:
                        spec_filters = { **filters, **{'Gross Score': [score] } }
                        pname = save_pie(df, variable, filters=spec_filters)
                        out_df = out_df.append( {**row, **{'Chart': f'Pie Chart {score}s', 'Image': head_url+pname+'?v=2'}}, ignore_index=True )
                        upload_fs.append(pname)
                        if tot is not None:
                            ncomp += 1
                            prog.progress( ncomp/tot )

    if tot is not None:
        prog.progress( 1. )

    assert( len(out_df) == len(upload_fs) )
    os.system('mkdir -p csv')
    out_df['Player'].replace( { 'All': '- Summary of All Players -' }, inplace=True )
    out_df['Course'].replace( { 'Any': '- Any Course -' }, inplace=True )
    out_df.to_csv( 'csv/AppAnalysis.csv' )

    return out_df, upload_fs

def unique_dirs(upload_fs):
    unique = set()
    for fil in upload_fs:
        path, base = os.path.split(fil)
        unique.add(path)
    return unique

if __name__ == '__main__':

    parser = ArgumentParser()
    parser.add_argument('-N','--no-upload', dest='noupload', default=False, action='store_true', help='Do not run the upload')
    parser.add_argument('-t','--synch-time', dest='synchtime', default='5', help='Re-synch time')
    args = parser.parse_args()

    try:
        synchtime = int(args.synchtime)
    except:
        synchtime = None

    st.set_page_config( page_title='GASH Cup 2022 Data Synch',
                        page_icon='gsh-logo.jpg' )

    c1, c2 = st.columns([6,1])
    with c1:
        st.title('GASH Cup 2022 Data Synch')
    with c2:
        st.image('gsh-logo.jpg', width=100)

    st.text(f'Data is synched every {synchtime} minutes')

    statusholder = st.empty()

    lastupdate = None
    run = True
    while run:
        if lastupdate is None:
            statusholder.text('Waiting for first synch...')
        else:
            statusholder.success(f'Last synched on {lastupdate}')

        #with pageholder.container():
        data_status = st.empty()
        data_status.text('Downloading data...')
        df = read_data()
        data_status.text('Downloading data... done')

        chart_status = st.empty()
        chart_status.text('Making charts...')
        chart_prog_bar = st.empty()
        out_df, upload_fs = make_charts(df, tot=491, stream=chart_prog_bar)
        chart_status.text('Making charts... done')

        with open('dirlist.txt','w') as f:
            for uniq in unique_dirs(upload_fs):
                f.write(uniq+'\n')

        if not args.noupload:
            upload_status = st.empty()
            upload_status.text('Uploading...')
            upload_prog_bar = st.empty()
            upload( upload_fs, mkdirs=False, prog=True, stream=upload_prog_bar )
            upload_status.text('Uploading... Done.')

        df_status = st.empty()
        with df_status.container():
            st.text('Synched data:')
            st.write( out_df )

        lastupdate = time.strftime("%d/%m/%y - %H:%M:%S")
        st.balloons()
        if synchtime is None:
            run = False
        else:
            with statusholder.container():
                st.success(f'Last synched on {lastupdate}')
                with st.spinner('Waiting for next synch...'):
                    time.sleep(synchtime*60)
            data_status.empty()
            chart_status.empty()
            chart_prog_bar.empty()
            if not args.noupload:
                upload_status.empty()
                upload_prog_bar.empty()
            df_status.empty()
