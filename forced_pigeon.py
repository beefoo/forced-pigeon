# -*- coding: utf-8 -*-

# Required PIL and igraph
#   pip install Pillow
#   pip install python-igraph

# Usage:
#   python forced_pigeon.py -layout large_graph -output output/pigeon_large_graph.png
#   python forced_pigeon.py -layout fruchterman_reingold -output output/pigeon_fruchterman_reingold.png
#   python forced_pigeon.py -layout kamada_kawai -output output/pigeon_kamada_kawai.png
#   python forced_pigeon.py -edges True -output output/pigeon_fruchterman_reingold_user_edges.png
#   python forced_pigeon.py -edges True -uedges False -output output/pigeon_fruchterman_reingold_edges.png

import argparse
import collections
from igraph import *
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont
from pprint import pprint
import random
import sys

# input
parser = argparse.ArgumentParser()
# http://igraph.org/python/doc/tutorial/tutorial.html#layout-algorithms
parser.add_argument('-layout', dest="LAYOUT_ALGORITHM", default="fruchterman_reingold", help="Layout algorithm, e.g. fruchterman_reingold, kamada_kawai, drl, large_graph")
parser.add_argument('-output', dest="OUTPUT_FILE", default="output/pigeon_fruchterman_reingold.png", help="Path to output png file")
parser.add_argument('-edges', dest="EDGES", type=bool, default=False, help="Add edges?")
parser.add_argument('-uedges', dest="USER_EDGES", type=bool, default=True, help="If edges, add just edges?")

# init input
args = parser.parse_args()

# config
PIGEON_FILE = "pigeon.png"
GRAPH_FILE = "graph/combined-billi.json"
OUTPUT_FILE = args.OUTPUT_FILE
DPI = 300
MARGIN = 1.0 * DPI
FONT_SIZE = 16
FONT_LIGHT = 'Aleo-Light.otf'
FONT_DARK = 'Aleo-Bold.otf'
# http://igraph.org/python/doc/tutorial/tutorial.html#layout-algorithms
# e.g. fruchterman_reingold, grid_fruchterman_reingold, kamada_kawai, drl, large_graph
LAYOUT_ALGORITHM = args.LAYOUT_ALGORITHM
EDGES = args.EDGES
USER_EDGES = args.USER_EDGES

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

# get graph data
nodeCounter = {}
nodes = []
links = []
users = []
with open(GRAPH_FILE) as f:
    graph = json.load(f)
    # normalize data
    for l in graph["links"]:
        s = l["source"]
        t = l["target"]
        links.append((s, t))
        users.append(l["user"])
    # count frequencies of nodes
    # nodeCounter = collections.Counter(nodes)
    # links = random.sample(links, 100)
    for link in links:
        nodes += list(link)
    # we're going to ignore nodes w/ no links
    nodes = list(set(nodes))

# print graph info
nodeCount = len(nodes)
linkCount = len(links)
edges = [(nodes.index(l[0]), nodes.index(l[1])) for l in links]
print "Read graph with %s nodes and %s links" % ("{:,}".format(nodeCount), "{:,}".format(linkCount))

# config/init graph
preProcessedFilename = "preprocessed_%s.json" % LAYOUT_ALGORITHM
labels = []
cWidth = width - MARGIN * 2
cHeight = height - MARGIN * 2

# pre-processed data found, just read it directly
if os.path.isfile(preProcessedFilename):
    print "Using preprocessed data..."
    with open(preProcessedFilename) as f:
        layout = json.load(f)
        for l in layout:
            i = l[0]
            nx = l[1]
            ny = l[2]
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

# process graph from scratch
else:
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

    preprocessedData = []
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
        preprocessedData.append([i, nx, ny])

# now draw the links
if EDGES:
    lines = []
    for i, edge in enumerate(edges):
        if not USER_EDGES or (USER_EDGES and users[i]):
            p1i = edge[0]
            p2i = edge[1]
            p1 = labels[p1i]["point"]
            p2 = labels[p2i]["point"]
            lines.append([p1, p2])

# draw output file
print "About to output file"
fnt = ImageFont.truetype(FONT_LIGHT, FONT_SIZE)
fntBold = ImageFont.truetype(FONT_DARK, FONT_SIZE)
out = Image.new('RGB', (width, height), (255,255,255))
d = ImageDraw.Draw(out)
if EDGES:
    for line in lines:
        d.line(line, fill=(100,100,100), width=1)
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


if not os.path.isfile(preProcessedFilename):
    print "Dumping graph data into json..."
    with open(preProcessedFilename, 'w') as f:
        json.dump(preprocessedData, f)
