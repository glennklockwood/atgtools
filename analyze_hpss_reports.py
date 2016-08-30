#!/usr/bin/env python
#
#  Tool to scrape the daily HPSS report emails from Gmail and report aggregate
#  statistics.
#
#  Relies on the Gmail API which must be configured separately.  Follow the
#  instructions at the following URL:
#
#   https://developers.google.com/gmail/api/quickstart/python
#

import httplib2
import os
import pandas

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import json
import base64
import cStringIO as StringIO

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/gmail-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Quickstart'

def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)

    ### get a list of matching message IDs
    message_id_list = []
    messages = service.users().messages()
    request = messages.list(userId='me', q='from:hpss@flanders.nersc.gov')
    while request is not None:
        output = request.execute()
        for message in output['messages']:
            message_id_list.append( message['id'] )
        request = messages.list_next(request, output)
    print "Found %d matching HPSS report e-mails" % len(message_id_list)

    ### retrieve each message id
    LINE_FMT = ['users', 'io_gb', 'ops', 'write_gb', 'write_ops', 'read_gb', 'read_ops', 'copy_gb', 'copy_ops']
    data_dict = {}
    for message_id in message_id_list:
        output = messages.get(userId='me', id=message_id).execute()
        message_body = base64.b64decode( output['payload']['body']['data'] )

        ### parse the body of each e-mail.  assume we only care about the first
        ### set of data ("Archive : IO Totals by HPSS Mover Host")
        for line in StringIO.StringIO( message_body ).readlines():
            if line.startswith('HPSS Report for Date'):
                date = line.split()[4]
                print "Analyzing report for %s" % date
            elif line.startswith('Total'):
                args = line.split()
                data_dict[date] = {}
                for i in range(len(args)-1):
                    data_dict[date][LINE_FMT[i]] = float(args[i+1])
            elif line.startswith('HPSS ACCOUNTING:'):
                data_dict[date]['hpss_accounting'] = float(line.split()[2])
                break

    ### convert dict of data into a DataFrame
    df = pandas.DataFrame.from_dict( data=data_dict, orient='index' )
    df.index.name = 'date'
    print df.to_csv(path_or_buf=None, columns=sorted(df.keys()))


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-quickstart.json')

    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print 'Initializing credentials and storing to ' + credential_path

    return credentials

if __name__ == '__main__':
    main()
