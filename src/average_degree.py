#!/usr/bin/env python 
# -*- coding: utf-8 -*-
import json
import networkx
import time
import sys, getopt

# Using python time module, parse year:year_day:hours:min:seconds, convert to seconds
def parse_time(t):
	temp = t.replace("+0000 ", "")
	time_struct = time.strptime(temp)
	# convert year:day_of_year:hours:min:seconds to seconds
	return time_struct.tm_year * 365 * 86400 + time_struct.tm_yday * 86400 + time_struct.tm_hour * 3600 + time_struct.tm_min * 60 + time_struct.tm_sec

# Formatting issue, the keys are not properly found in the dictionary
# i.e. there is a single key 'text”:”Apache”,”indices'
# Known style limitation: brute force get hashtag string
def get_hashtags(hashtags):
	nodes = []
	for entry in hashtags:
		nodes.append(entry["text"])
	return nodes

# Class to read the twitter file, compute the 60 second rolling average
class TwitterReader(object):
	def __init__(self, data_file):
		self.G = networkx.Graph()
		self.rolling_averages = []
		self.time_range = None
		self.parse_data(data_file)


	# Parse the file, get time and hashtags
	def parse_data(self, data_file):
		f = open(data_file, 'r')
		temp = f.readlines()
		f.close()

		for val in temp:
			try:
				j = json.loads(val)
				t = parse_time(j["created_at"])
				nodes = get_hashtags(j["entities"]["hashtags"])
				# If there are hashtags, update graph
				if len(nodes) > 0:
					self.update_graph(t, nodes)
			except:
				pass


	# Add nodes/edges to the graph
	def update_graph(self, t, nodes):
		if self.time_range is None:
			self.time_range = (t, t + 60)

		# Case where we have to "shift" the 60 second window
		# Must remove old edges (and nodes if need be) from the graph
		if t > self.time_range[1]:
			self.time_range = (t - 60, t)
			self.remove_old()

		# Add nodes to the graph (if a node already exists in graph, time_added will be updated)
		for node in nodes:
			self.G.add_node(node)
			self.G.node[node]['time_added'] = t

		# Add edges to the graph (if an edge already exists in graph, time_added will be updated)
		if len(nodes) > 1:
			for i in range(len(nodes)):
				for j in range(i+1, len(nodes)):
					self.G.add_edge(nodes[i], nodes[j])
					self.G.edge[nodes[i]][nodes[j]]['time_added'] = t

		# Save rolling averages
		self.rolling_averages.append(sum(self.G.degree().values()) / len(self.G.node))


	# Get rid of obsolete edges/nodes
	def remove_old(self):
		for edge in self.G.edges():
			if self.G.edge[edge[0]][edge[1]]['time_added'] < self.time_range[0]:
				self.G.remove_edge(edge[0], edge[1])

			# Also have to check that the nodes involved in the edge were added at an appropriate time
			if self.G.node[edge[0]]['time_added'] < self.time_range[0]:
				self.G.remove_node(edge[0])

			if self.G.node[edge[1]]['time_added'] < self.time_range[0]:
				self.G.remove_node(edge[1])

	# Save the rolling averages
	def save(self, sample_out):
		f = open(sample_out, 'w')
		for val in self.rolling_averages:
			f.write(str(val) + "\n")
		f.close()

# parse command line arguments
def main(argv):
   	inputfile = ''
   	outputfile = ''
   	try:
		opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
	except getopt.GetoptError:
      		print 'average_degree.py -i <inputfile> -o <outputfile>'
      		sys.exit(2)
   	for opt, arg in opts:
      		if opt == '-h':
         		print 'average_degree.py -i <inputfile> -o <outputfile>'
         		sys.exit()
      		elif opt in ("-i", "--ifile"):
         		inputfile = arg
      		elif opt in ("-o", "--ofile"):
			outputfile = arg
   	print 'Input file is "', inputfile
   	print 'Output file is "', outputfile

	tr = TwitterReader(inputfile)
	tr.save(outputfile)


if __name__ == "__main__":
	main(sys.argv[1:])
