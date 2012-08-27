#!/usr/bin/env python

# Verify that the voting receipts match CSV download

from bs4 import BeautifulSoup
import sys
import re
import csv

soup = BeautifulSoup(open(sys.argv[1]))

NAME_RE = re.compile(r'(.*) \(.*?\)')

table = soup.find_all('table')[-1]
count = 0
verified_ballots = []
for row in table.find_all('tr'):
    count += 1
    if count == 1:
        continue
    cols = row.find_all('td')
    receipt = cols[1].text
    names = cols[2].text
    if cols[1].span:
        # Overridden by another vote; ignore
        continue
    names = [x.group(1) for x in NAME_RE.finditer(names)]
    names.sort()
    verified_ballots.append(names)

count = 0
for row in csv.reader(open(sys.argv[2])):
    count += 1
    if count == 1:
        continue
    uid, vid, ts, poll, period, paper, weight, org, org2, org3, nplacards = row[:11]
    placards = row[11:]

    names = []
    for i in range(0, int(nplacards)*2, 2):
        names.append(placards[i])

    names.sort()
    i = verified_ballots.index(names)
    verified_ballots.pop(i)

if not verified_ballots:
    print "All ballots accounted for."
else:
    print "Unable to account for these ballots:"
    print verified_ballots
