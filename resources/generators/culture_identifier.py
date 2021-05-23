# Provides a 'classify' function to convert a list of values to their closest matching archetypes.

import pandas as pd
from math import pi, cos, sin, sqrt
from operator import itemgetter

framework = pd.read_csv("culture_framework.csv")
framework.set_index('Values', inplace=True)

archetypes = framework.columns.to_list()

col2abbv = dict(zip( [a[0] for a in archetypes], archetypes ))

# Framework has X axis from [-1, 1] / [independence, interdependence]
#               Y axis from [-1, 1] / [stability, flexibility]
# 8 archetypes = 45 degree (pi/4) difference between the two,
#                           starting from 45/2 (pi/8) from 0 degs/rads.
#               NOTE: Actual ranges are from +- 0.924
CPI = cos(pi/8)
SPI = sin(pi/8)

# Find locations of each archetype on unit circle
# (starting at 0 and going CCW)
locs = dict()
locs[col2abbv['C']] = (+CPI, +SPI)
locs[col2abbv['P']] = (+SPI, +CPI)
locs[col2abbv['L']] = (-SPI, +CPI)
locs[col2abbv['E']] = (-CPI, +SPI)
locs[col2abbv['R']] = (-CPI, -SPI)
locs[col2abbv['A']] = (-SPI, -CPI)
locs[col2abbv['S']] = (+SPI, -CPI)
locs[col2abbv['O']] = (+CPI, -SPI)

def _find_average_point(values):
    pt = [0, 0]
    for value in values:
        row = framework.loc[value]
        for arch in archetypes:
            if row[arch] > 0:
                # archetype is included. add it's location.
                arch_pt = locs[arch]
                pt[0] += arch_pt[0]
                pt[1] += arch_pt[1]
    pt[0] /= len(values)
    pt[1] /= len(values)
    return pt

dist = lambda p1,p2: sqrt( ((p1[0]-p2[0])**2)+((p1[1]-p2[1])**2) )
def _rank_archetype(point, min_score=0.5):
    adists = [
        (a, dist(point, locs[a])) for a in archetypes
        ]
    adists.sort(key=itemgetter(1))
    aranks = [( a[0], round(1-(a[1]/2),3) ) for a in adists]
    aranks = [a for a in aranks if a[1] >= min_score]
    return aranks

def classify(values, min_score=0.5):
    pt = _find_average_point(values)
    ranks = _rank_archetype(pt, min_score)
    return ranks
    
