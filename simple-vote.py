#!/usr/bin/env python

import csv
from prettytable import PrettyTable
import sys

class Candidate(object):
    def __init__(self, name):
        self.name = name
        self.votes = []
        self.total_weight = 0
        self.total_votes = 0

    def addVote(self, vote):
        self.votes.append(vote)
        self.total_weight += vote.weight
        self.total_votes += 1

class Vote(object):
    def __init__(self, candidate, weight):
        self.candidate = candidate
        self.weight = weight

class Voter(object):
    def __init__(self):
        self.votes = []

def convert_to_eighths(x):
    mapping = {'00': 0,
               '12': 1,
               '25': 2,
               '38': 3,
               '50': 4,
               '62': 5,
               '75': 6,
               '88': 7}
    whole, dec = x.split('.')
    return int(whole)*8 + mapping[dec]

candidates = {}
voters = []
g_total_weight = 0

def get_candidate(name):
    o = candidates.get(name)
    if not o:
        o = Candidate(name)
        candidates[name] = o
    return o

count = 0
for row in csv.reader(open(sys.argv[1])):
    count += 1
    if count == 1:
        continue
    uid, vid, ts, poll, period, paper, weight, org, org2, org3, nplacards = row[:11]
    placards = row[11:]

    v = Voter()
    voters.append(v)
    for i in range(0, int(nplacards)*2, 2):
        p = Vote(placards[i], convert_to_eighths(placards[i+1]))
        v.votes.append(p)
        c = get_candidate(placards[i])
        c.addVote(p)
        g_total_weight += p.weight

cs = candidates.values()
cs.sort(lambda a, b: cmp(a.total_weight, b.total_weight))
cs.reverse()
t = PrettyTable(["Name", "Weighted", "%Weighted", "Voters", "%Voters"])
t.set_field_align("Name", 'l')
for c in cs:
    w = '%0.2f' % (float(c.total_weight)/g_total_weight*100.0)
    vrs = '%0.2f' % (float(c.total_votes)/len(voters)*100)
    t.add_row([c.name, '%6.2f' % (c.total_weight/8.0), w, c.total_votes, vrs])
print t

print 'voters', len(voters)
print 'total weighted votes', float(g_total_weight)/8
