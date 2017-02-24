# -*- coding: utf-8 -*-

# Required PIL and igraph
#   pip install Pillow
#   pip install python-igraph

# Usage:
#   python forced_pigeon.py -layout drl -output pigeon_grid_fruchterman_reingold.png

import argparse
import collections
from igraph import *
import json
import math
from PIL import Image, ImageDraw, ImageFont
from pprint import pprint
import random
import sys

# input
parser = argparse.ArgumentParser()
# http://igraph.org/python/doc/tutorial/tutorial.html#layout-algorithms
parser.add_argument('-layout', dest="LAYOUT_ALGORITHM", default="fruchterman_reingold", help="Layout algorithm, e.g. fruchterman_reingold, kamada_kawai, drl, large_graph")
parser.add_argument('-output', dest="OUTPUT_FILE", default="mm-billi-pigeon.png", help="Path to output png file")

# init input
args = parser.parse_args()

# config
PIGEON_FILE = "pigeon.png"
GRAPH_FILE = "graph/combined-billi.json"
OUTPUT_FILE = args.OUTPUT_FILE
DPI = 300
MARGIN = 1.0 * DPI
FONT_SIZE = 13
FONT_LIGHT = 'Aleo-Light.otf'
FONT_DARK = 'Aleo-Bold.otf'
# http://igraph.org/python/doc/tutorial/tutorial.html#layout-algorithms
# e.g. fruchterman_reingold, grid_fruchterman_reingold, kamada_kawai, drl, large_graph
LAYOUT_ALGORITHM = args.LAYOUT_ALGORITHM

def class2Label(c):
    return c.split(":")[-1].upper()

def lim(value, bounds):
    if value < bounds[0]:
        return bounds[0]
    elif value > bounds[1]:
        return bounds[1]
    else:
        return value

def norm(value, bounds):
    return lim(1.0 * (value - bounds[0]) / (bounds[1] - bounds[0]), (0.0, 1.0))

# get pigeon as reference
pImage = Image.open(PIGEON_FILE)
pData = list(pImage.getdata())
(width, height) = pImage.size
print "Read pigeon image data with dimensions %s x %spx" % ("{:,}".format(width), "{:,}".format(height))

# area of pigon is all the black pixels
# pigeonArea = len([p for p in pData if p[0] < 255*0.5])
# print "Area of pigeon is %spx" % "{:,}".format(pigeonArea)

# get pigeon bounds
# pPixels = [(int(i%width), int(i/width)) for i, p in enumerate(pData) if p[0] < 255*0.5]
# pxs = [p[0] for p in pPixels]
# pys = [p[1] for p in pPixels]
# pxBound = (min(pxs), max(pxs))
# pyBound = (min(pys), max(pys))
# pW = pxBound[1] - pxBound[0]
# pH = pyBound[1] - pyBound[0]
# print "Pigeon dimensions: %s x %spx, offset: %s x %spx" % ("{:,}".format(pW), "{:,}".format(pH), pxBound[0], pyBound[0])

# get graph data
nodeCounter = {}
nodes = []
links = []
with open(GRAPH_FILE) as f:
    graph = json.load(f)
    # normalize data
    for l in graph["links"]:
        s = l["source"]
        t = l["target"]
        links.append((s, t))
    # count frequencies of nodes
    # nodeCounter = collections.Counter(nodes)
    links = random.sample(links, 100)
    for link in links:
        nodes += list(link)
    # we're going to ignore nodes w/ no links
    nodes = list(set(nodes))

# print graph info
nodeCount = len(nodes)
linkCount = len(links)
edges = [(nodes.index(l[0]), nodes.index(l[1])) for l in links]
print "Read graph with %s nodes and %s links" % ("{:,}".format(nodeCount), "{:,}".format(linkCount))

# get ideal distance k between two vertices
# k = C * math.sqrt(1.0 * pigeonArea / nodeCount)
# print "Ideal distance between two vertices: %spx" % k
# print "5 most common nodes:"
# print nodeCounter.most_common(5)
# print "First 5 nodes:"
# for n in nodes[:5]:
#     pprint(n)
# print "First 5 links"
# for l in links[:5]:
#     pprint(l)

# build graph
print "Building graph, may take a while..."
g = Graph()
g.add_vertices(nodeCount)
g.add_edges(edges)
layout = g.layout(LAYOUT_ALGORITHM)

# get bounds and convert to pixels
xs = [p[0] for p in layout]
ys = [p[1] for p in layout]
xBound = (min(xs), max(xs))
yBound = (min(ys), max(ys))
labels = []
cWidth = width - MARGIN * 2
cHeight = height - MARGIN * 2
for i, p in enumerate(layout):
    nx = norm(p[0], xBound)
    ny = norm(p[1], yBound)
    x = int(round(nx * cWidth + MARGIN))
    y = int(round(ny * cHeight + MARGIN))
    pigeon = False
    pi = int(y * width + x)
    if pData[pi][0] < 255 * 0.5:
        pigeon = True
    labels.append({
        "label": class2Label(nodes[i]),
        "pigeon": pigeon,
        "point": (x, y)
    })

# draw output file
print "About to output file"
fnt = ImageFont.truetype(FONT_LIGHT, FONT_SIZE)
fntBold = ImageFont.truetype(FONT_DARK, FONT_SIZE)
out = Image.new('RGB', (width, height), (255,255,255))
d = ImageDraw.Draw(out)
for l in labels:
    f = fnt
    if l["pigeon"]:
        f = fntBold
    # calculate center of text
    tw, th = d.textsize(l["label"])
    (tx, ty) = l["point"]
    tp = (tx - tw/2, ty - th/2)
    d.text(tp, l["label"], font=f, fill=(0,0,0))
out.save(OUTPUT_FILE, "PNG")
print "Saved to file %s" % OUTPUT_FILE
