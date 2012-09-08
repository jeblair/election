#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
from prettytable import PrettyTable
import sys

candidate_employers = {
    'Rob Hirschfeld': 'Dell',
    'Monty Taylor': 'HP',
    'Hui Cheng': 'SINA',
    'Joseph George': 'Dell',
    'Yujie Du': '99cloud',
    'Troy Toman': 'Rackspace',
    'Anne Gentle': 'Rackspace',
    'Thierry Carrez': 'Rackspace',
    'Tim Bell': 'CERN',
    'Tristan Goode': 'Aptira',
    'Jesse Andrews': 'Nebula',
    }

class Candidate(object):
    def __init__(self, name):
        self.name = name
        self.votes = []
        self.total_weight = 0
        self.total_votes = 0
        self.org_votes = {}
        self.employer = None

    def addVote(self, vote):
        self.votes.append(vote)
        self.total_weight += vote.weight
        self.total_votes += 1
        votes = self.org_votes.get(vote.org, [])
        votes.append(vote)
        self.org_votes[vote.org] = votes

class Vote(object):
    def __init__(self, candidate, weight, org):
        self.candidate = candidate
        self.weight = weight
        self.org = org

class Organization(object):
    def __init__(self, name):
        self.name = name
        self.voters = []
        self.slates = []

    def getSlate(self, slate):
        for s in self.slates:
            if s == slate:
                return s
        self.slates.append(slate)
        return slate

class Voter(object):
    def __init__(self):
        self.votes = []

class Slate(object):
    def __init__(self, candidates):
        self.candidates = candidates
        self.candidates.sort()
        self.count = 0

    def __eq__(self, other):
        return self.candidates == other.candidates

    def __str__(self):
        return ', '.join(self.candidates)

def convert_to_eighths(x):
    mapping = {'00': 0,
               '12': 1,
               '25': 2,
               '38': 3,
               '50': 4,
               '62': 5,
               '75': 6,
               '88': 7}
    if '.' in x:
        whole, dec = x.split('.')
    else:
        whole = x
        dec = '00'
    return int(whole)*8 + mapping[dec]

candidates = {}
orgs = {}
voters = []
g_total_weight = 0.0
g_total_votes = 0

def get_org(name):
    return orgs.get(name, orgs.get("Other"))

def get_candidate(name):
    o = candidates.get(name)
    if not o:
        o = Candidate(name)
        candidates[name] = o
    return o

all_ballots = {}
all_rows = []

count = 0
for row in csv.reader(open(sys.argv[1])):
    count += 1
    if count == 1:
        continue
    uid, vid, ts, poll, period, paper, weight, org, org2, org3, nplacards = row[:11]
    weight = convert_to_eighths(weight)
    row[6] = weight
    nplacards = int(nplacards)
    row[10] = nplacards
    ts = int(ts)
    row[2] = ts
    all_rows.append(row)

all_rows.sort(lambda a, b: cmp(a[2], b[2]))

for row in all_rows:
    uid, vid, ts, poll, period, paper, weight, org, org2, org3, nplacards = row[:11]
    placards = row[11:]

    vote_total = 0
    for i in range(0, nplacards*2, 2):
        value = convert_to_eighths(placards[i+1])
        vote_total += value

    old_ballot = all_ballots.get(uid)
    if old_ballot:
        if old_ballot[6] + weight <= 64:
            old_ballot[6] += weight
            old_ballot[10] += nplacards
            old_ballot.extend(placards)
            #print 'extending', uid
        else:
            all_ballots[uid] = row
            #print 'replacing', uid
    else:
        all_ballots[uid] = row

org_counts = {}
for row in all_ballots.values():
    (uid, vid, ts, poll, period, paper, weight,
     org, org2, org3, nplacards) = row[:11]

    bestorg = org
    if bestorg in ['None', 'Did Not Provide', '没有']:
        bestorg = "None"
    if bestorg == '':
        bestorg = 'Other'

    c = org_counts.get(bestorg, 0)
    c += 1
    org_counts[bestorg] = c

for name in ["Other", "None"] + candidate_employers.values():
    o = Organization(name)
    orgs[name] = o

for name, count in org_counts.items():
    if count >= 5:
        o = Organization(name)
        orgs[name] = o

for row in all_ballots.values():
    (uid, vid, ts, poll, period, paper, weight,
     org, org2, org3, nplacards) = row[:11]
    placards = row[11:]

    bestorg = org
    if bestorg in ['None', 'Did Not Provide', '没有']:
        bestorg = "None"
    if bestorg == '':
        bestorg = 'Other'

    o = get_org(bestorg)
    v = Voter()
    o.voters.append(v)
    voters.append(v)
    vote_total = 0
    for i in range(0, int(nplacards)*2, 2):
        weight = convert_to_eighths(placards[i+1])
        vote_total += weight
        p = Vote(placards[i], weight, o)
        v.votes.append(p)
        c = get_candidate(placards[i])
        c.addVote(p)
        g_total_weight += p.weight
        g_total_votes += 1

cs = candidates.values()
cs.sort(lambda a, b: cmp(a.total_weight, b.total_weight))
cs.reverse()
t1 = PrettyTable(["Name", "Weighted", "%Weighted", "Voters", "%Voters"])
t1.set_field_align("Name", 'l')
t2 = PrettyTable(["Name", "Employer", "%Employer", "%Major", "%Minor", "%None"])
t2.set_field_align("Name", 'l')
t2.set_field_align("Employer", 'l')
for c in cs:
    o = candidate_employers.get(c.name)
    if o:
        c.employer = get_org(o)
    w = '%0.2f %%' % (float(c.total_weight)/g_total_weight*100.0)
    vrs = '%0.2f %%' % (float(c.total_votes)/len(voters)*100)

    employer_count = 0.0
    other_major_count = 0.0
    other_minor_count = 0.0
    none_count = 0.0
    for org, ovotes in c.org_votes.items():
        if org == c.employer:
            employer_count += len(ovotes)
        else:
            if org.name == 'Other':
                other_minor_count += len(ovotes)
            elif org.name == 'None':
                none_count += len(ovotes)
            else:
                other_major_count += len(ovotes)
    t1.add_row([c.name, '%6.2f' % (c.total_weight/8.0), w, c.total_votes, vrs])
    employer_pct = (employer_count/c.total_votes*100)
    major_pct = (other_major_count/c.total_votes*100)
    minor_pct = (other_minor_count/c.total_votes*100)
    none_pct = (none_count/c.total_votes*100)
    values = []
    for v in [employer_pct, major_pct, minor_pct, none_pct]:
        values.append('% .0f %%' % v)

    if c.employer:
        t2.add_row([c.name, c.employer.name] + values)

print t1
print t2

print 'voters', len(voters)
print 'total weighted votes', float(g_total_weight)/8
print 'total votes', g_total_votes

#                           Number       Only           Including     Non
t = PrettyTable(["Name", "Affiliated", "Affiliated", "Affiliated", "Affiliated"])
t.set_field_align("Name", 'l')

os = orgs.values()
os.sort(lambda a, b: cmp(a.name, b.name))
for o in os:
    only_employer_count = 0
    including_employer_count = 0
    non_employer_count = 0
    total_count = 0
    for voter in o.voters:
        slate = Slate([v.candidate for v in voter.votes])
        slate = o.getSlate(slate)
        slate.count += 1
        any_employer = False
        only_employer = True
        for v in voter.votes:
            if get_candidate(v.candidate).employer == o:
                any_employer = True
            else:
                only_employer = False
        if any_employer:
            including_employer_count += 1
            if only_employer:
                only_employer_count += 1
        else:
            non_employer_count += 1
        total_count += 1

    if total_count:
        voe = float(only_employer_count)/total_count*100
        vfe = float(including_employer_count)/total_count*100
        ne = float(non_employer_count)/total_count*100
    else:
        voe = vfe = ne = 0.0

    if len(o.voters) >50 and vfe>10 and o.name not in ["Other", "None"]:
        t.add_row([o.name, len(o.voters), '% .0f %%' % voe, '% .0f %%' % vfe,
                   '% .0f %%'% ne])
print t
