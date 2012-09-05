#!/usr/bin/python

# Soren Hansen wrote the original version of this script.
# James Blair hacked it up to include email addresses from gerrit.

import calendar
import datetime
import json
import optparse
import paramiko
from pprint import pprint
import sys
import csv
import re

MAILTO_RE = re.compile('mailto:(.*)')
USERNAME_RE = re.compile('username:(.*)')
accounts = {}

class Account(object):
    def __init__(self, num):
        self.num = num
        self.emails = []
        self.username = None

def get_account(num):
    a = accounts.get(num)
    if not a:
        a = Account(num)
        accounts[num] = a
    return a

for row in csv.reader(open('accounts.csv')):
    num, email, pw, external = row
    num = int(num)
    a = get_account(num)
    if email and email != '\\N' and email not in a.emails:
        a.emails.append(email)
    m = MAILTO_RE.match(external)
    if m:
        if m.group(1) not in a.emails:
            a.emails.append(m.group(1))
    m = USERNAME_RE.match(external)
    if m:
        if a.username:
            print a.num
            print a.username
            raise Exception("Already a username")
        a.username = m.group(1)

username_accounts = {}
for a in accounts.values():
    username_accounts[a.username] = a

atcs = []

optparser = optparse.OptionParser()
optparser.add_option('-p', '--project', default='nova', help='Project to generate stats for')
optparser.add_option('-o', '--output', default='out.csv', help='Output file')
options, args = optparser.parse_args()

QUERY = "project:%s status:merged" % options.project

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.load_system_host_keys()
client.connect('review.openstack.org', port=29418, key_filename='/home/corvus/.ssh/id_rsa', username='corvus')
stdin, stdout, stderr = client.exec_command('gerrit query %s --all-approvals --format JSON' %
                                            QUERY)
changes = []

done = False
last_sortkey = ''
tz = datetime.tzinfo
start_date = datetime.datetime(2011, 8, 30, 07, 00, 00)
end_date = datetime.datetime(2012, 8, 29, 06, 59, 00)

count = 0
earliest = datetime.datetime.now()
while not done:
    for l in stdout:
        data = json.loads(l)
        if 'rowCount' in data:
            if data['rowCount'] < 500:
                done = True
            continue
        count += 1
        last_sortkey = data['sortKey']
        if 'owner' not in data:
            continue
        if 'username' not in data['owner']:
            continue
        account = username_accounts[data['owner']['username']]
        approved = False
        for ps in data['patchSets']:
            if 'approvals' not in ps:
                continue
            for aprv in ps['approvals']:
                if aprv['type'] != 'SUBM':
                    continue
                ts = datetime.datetime.fromtimestamp(aprv['grantedOn'])
                if ts < start_date or ts > end_date:
                    continue
                approved = True
                if ts < earliest:
                    earliest = ts
        if approved and account not in atcs:
            atcs.append(account)
    if not done:
        stdin, stdout, stderr = client.exec_command('gerrit query %s resume_sortkey:%s --all-approvals --format JSON' % (QUERY, last_sortkey))

print 'project: %s' % options.project
print 'examined %s changes' % count
print 'earliest timestamp: %s' % earliest
writer = csv.writer(open(options.output, 'w'))
for a in atcs:
    writer.writerow([a.username] + a.emails)
print
