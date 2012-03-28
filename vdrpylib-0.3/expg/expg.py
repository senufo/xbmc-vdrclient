#! /usr/bin/env python

#####################################################################
# Copyright 2002 Stefan Goetz
#####################################################################
# This file is part of vdrpylib.
# 
# vdrpylib is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# vdrpylib is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with vdrpylib; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#####################################################################

import vdr.event
import vdr.vdr

import re
import time
import os
import sys
import urllib
import getopt
import string


def striphtml(s):
	"""Strips html from a string.
	
	Some known HTML character codes are converted, all others as well
	as HTML tags are removed.
	
	The return value is a copy of s stripped from HTML.
	"""
	s = s.replace('&#196;', 'Ä')
	s = s.replace('&#214;', 'Ö')
	s = s.replace('&#220;', 'Ü')
	s = s.replace('&#228;', 'ä')
	s = s.replace('&#246;', 'ö')
	s = s.replace('&#252;', 'ü')
	s = s.replace('&#223;', 'ß')
	s = s.replace('&amp;', '&')
	pat_tag = re.compile('(<.*?>)|(&.*?;)')
	result = pat_tag.search(s)
	while result:
		if result.group(1) is not None:
			start, end = result.span(1)
		else:
			start, end = result.span(2)
		s = s[0:start].rstrip() + ' ' + s[end:].lstrip()
		result = pat_tag.search(s)
	return s



# demultiplex to channel specific functions
def retrieveepg(channel, time):

	if not retrievers.has_key(channel.sid):
		print 'No parser implemented for this channel!'
		return None
		
	func, arg = retrievers[channel.sid]
	return func(channel, time, arg)



def retrieveorfepg(channel, tm, arg):
	pat_start = re.compile('>(\d{1,2}:\d\d)</')
	pat_title = re.compile('<font size="-1"><b>(.+)</b></td>')
	pat_sub = re.compile(' size=-1 color=#[36C]{4}00>\(&quot;(.+)&quot;\)<| size=-1 color=#[36C]{4}00>([^<]+)<| size=-1 color=#[36C]{4}00><b>([^<]+)</b><')
	pat_desc = re.compile(' size=-1 color=#[36C]{4}00><b>[^<>]*</b><br>(.*)<br>| size=-1 color=#[36C]{4}00>[^<>]*<br><b>[^<>]*</b><br>(.*)<br>')
	tableID = None
	new_event_counter = 0
	
	# Determine latest known EPG event, the tableID and whether we
	# can learn new events from the current page at all
	ev_cur = ev_prev = None
	if len(channel.events) > 0:
		ev_prev = channel.events[-1]
		tableID = ev_prev.tableID
		# a page displayes all programs from 6:00 same day till 5:59 next day
		if ev_prev.start >= (tm + (3600 * 30)):
			return 0
		if ev_prev.dur != 0:
			ev_prev = None

	url = 'http://tv.orf.at/program/orf' + str(arg) + '/' + time.strftime('%Y%m%d', time.localtime(tm)) + '/index.html'
	try:
		fh = urllib.urlopen(url)
	except:
		print 'Unable to retrieve URL ' + url
		return

	line = fh.readline()
	while line:
		line = line.strip()
		result = pat_start.search(line)
		if result is not None:
			if ev_cur is not None:
				if channel.addevent(ev_cur):
					new_event_counter = new_event_counter + 1
				ev_prev = ev_cur

			(hour, min) = map(int, result.group(1).split(':'))
			if hour < 6:
				hour = hour + 24

			ev_cur = vdr.event.Event()
			ev_cur.source = 'www'
			ev_cur.start = tm + hour * 3600 + min * 60
			ev_cur.dur = 0
			if ev_prev is not None:
				ev_prev.dur = ev_cur.start - ev_prev.start

			#print 'Found start time: ' + time.ctime(ev_cur.start)
		result = pat_title.search(line)
		if result is not None:
			if ev_cur is not None:
				ev_cur.title = result.group(1)
			#print 'Found title: ' + result.group(1)
		result = pat_sub.search(line)
		if result is not None:
			if ev_cur is not None:
				ev_cur.subtitle = result.group(result.lastindex)
			#print 'Found subtitle: ' + result.group(result.lastindex)
		result = pat_desc.search(line)
		if result is not None:
			if ev_cur is not None:
				ev_cur.desc = striphtml(result.group(result.lastindex)).strip()
			#print 'Found description: ' + result.group(result.lastindex)
		line = fh.readline()
	
	fh.close()
	return new_event_counter



def retrieveardepg(channel, tm, arg):
	pat_table = re.compile(' <tr>(.*?\d{1,2}:\d\d.*?) </tr>', re.M | re.S)
	pat_event = re.compile('<td.*?(\d{1,2}:\d\d).*?</td>\s*<td.*?>(.*?)</td>', re.M | re.S)
	pat_url_title = re.compile('\s*<a href="(.*?)".*?>\s*(.*?)\s*</a>\s*<br>\s*(.*?)\s*(<br><a|$)', re.M | re.S)
	pat_url_title2 = re.compile('\s*<a href="(.*?)".*?>\s*(.*?)\s*</a></td></tr></table>\s*(.*?)\s*</font>', re.M | re.S)
	pat_url_title3 = re.compile('<font.*?>(.*?)</font>')
	tableID = None
	new_event_counter = 0
	
	# the ard page is referenced by a day counter relative to today - get this value:
	tm_tup = time.localtime() 
	tm_int = int(time.mktime(tm_tup[0:3] +  (0, 0, 0) + tm_tup[6:]))
	rel_days = int((tm - tm_int) / (24 * 3600))
	url = 'http://programm.das-erste.de/liste1.asp?sender=' + str(arg) + '&stag=' + str(rel_days)

	# Determine latest known EPG event, the tableID and whether we
	# can learn new events from the current page at all
	ev_cur = ev_prev = None
	if len(channel.events) > 0:
		ev_prev = channel.events[-1]
		tableID = ev_prev.tableID
		# a page contains all programs from 5:30 same day till 5:29 next day
		if ev_prev.start >= (tm + (3600 * 24) + (3600 * 5) + 1800):
			return 0
		if ev_prev.dur != 0:
			ev_prev = None

	try:
		fh = urllib.urlopen(url)
		str_html = fh.read()
		fh.close()
	except:
		print 'Unable to retrieve URL ' + url
		return

	start = 0
	while 1:
		result = pat_table.search(str_html, start)
		if result is None:
			break
		start = result.end(1)
		str_event = result.group(1)
		ev_prev = ev_cur
		ev_cur = vdr.event.Event()
		ev_cur.source = 'www'
		ev_cur.dur = 0
		
		# determine start time and info
		result = pat_event.search(str_event)
		str_info = result.group(2)
		(hour, min) = map(int, result.group(1).split(':'))
		if hour <= 5 and min < 30:
			hour = hour + 24
		ev_cur.start = tm + hour * 3600 + min * 60
		ev_cur.dur = 0
		ev_cur.tableID = tableID

		# determine duration of previous event
		if ev_prev is not None:
			ev_prev.dur = ev_cur.start - ev_prev.start
		
		# add event to channel (must be after setting the start time
		# of this and the duration of the previous event)
		if channel.addevent(ev_cur):
			new_event_counter = new_event_counter + 1
		else:
			continue

		# determine title, subtitle and description
		result = pat_url_title.search(str_info)
		if result is None:
			result = pat_url_title2.search(str_info)
		if result is not None:
			ev_cur.title = striphtml(result.group(2)).strip()
			ev_cur.subtitle = striphtml(result.group(3)).strip()
			url = 'http://programm.das-erste.de/' + result.group(1)
			ev_cur.desc = getarddesc(url)
		else:
			result = pat_url_title3.search(str_info)
			if result is not None:
				ev_cur.title = striphtml(result.group(1)).strip()
			else:
				print 'Could not find event title where expected in ' + str_info
		
	return new_event_counter


def getarddesc(url):
	desc = ''
	try:
		fh = urllib.urlopen(url)
		str_html = fh.read()
		fh.close()

		pat_desc = re.compile('<!-- BEGIN: AUSGABE PF_BUILDITEM -->(.*)<!-- END: AUSGABE PF_BUILDITEM -->', re.M | re.S)
		result = pat_desc.search(str_html)
		desc = striphtml(result.group(1)).strip()
	except:
		print 'Failed to retrieve description from ' + url
		pass
	
	return desc


def print_usage():
	"""Prints available options.
	"""
	print 'Usage: ' + sys.argv[0] + """ [OPTION]... CHANNEL...
Retrieve EPG data from the WWW for the specified channels
OPTION can be one of:
    -h                  show this help message
    -l                  list the channels supported by expg
    -q                  query only, don't modify EPG data of VDR
    -c <filename>       The path to VDR's channels.conf file from which to read
                        the known channels (default: '/video/channels.conf').
    -d <days ahead>     number of days into the future for which EPG data is to
                        be retrieved.
    -e <filename>       The file name from which to read the known EPG data
                        (default: '/video/epg.data').
    -t <host:port>      the address to make SVDRP connections to
                        (default: 'localhost:2001')
CHANNEL can be one of:
    <idx>               an index into your list of channels to select the
                        first, second, ..., <n>th channel
    <sid>               the service ID of a channel
    <name>              the name of a channel (not case sensitive, beginning of
                        name is sufficient, e.g. 'aR' to select channel 'ARD'"""

# Associate channel or service IDs with retrieval functions
retrievers = {}
# ARD
retrievers[28106] = (retrieveardepg, 1)
# NDR
#retrievers[28224] = (retrieveardepg, 2)
# WDR
#retrievers[28111] = (retrieveardepg, 4)
# SWR
#retrievers[28113] = (retrieveardepg, 5)
# B1
#retrievers[28206] = (retrieveardepg, 6)
# DW-TV
#retrievers[9005] = (retrieveardepg, 7)
#retrievers[9016] = (retrieveardepg, 7)
# ORB
#retrievers[28205] = (retrieveardepg, 8)
# 3SAT
#retrievers[28007] = (retrieveardepg, 9)
# KiKa
#retrievers[28008] = (retrieveardepg, 10)
# BR-alpha
#retrievers[28112] = (retrieveardepg, 11)
# EinsFestival
#retrievers[28202] = (retrieveardepg, 12)
# Phoenix
#retrievers[28114] = (retrieveardepg, 13)
# MDR
#retrievers[28204] = (retrieveardepg, 14)
# EinsMuXx
#retrievers[28203] = (retrieveardepg, 15)
# arte
#retrievers[28109] = (retrieveardepg, 16)
# Hessen-3
#retrievers[28108] = (retrieveardepg, 17)
# BR3
#retrievers[28107] = (retrieveardepg, 18)
# ORF1
retrievers[13001] = (retrieveorfepg, 1)
# ORF2
retrievers[13002] = (retrieveorfepg, 2)


# default parameters
days_ahead = 2
query_only = 0
list_channels = 0
channels = []

# other global data
vdr_inst = vdr.vdr.VDR()

# check parameters
try:
	opts, rest = getopt.getopt(sys.argv[1:], 'hlqc:d:e:t:')
	for opt in opts:
		if opt[0] == '-c':
			vdr_inst.channelfile = opt[1]
		elif opt[0] == '-d':
			days_ahead = int(opt[1])
		elif opt[0] == '-e':
			vdr_inst.epgfile = opt[1]
		elif opt[0] == '-h':
			raise Exception
		elif opt[0] == '-l':
			list_channels = 1
		elif opt[0] == '-q':
			query_only = 1
		elif opt[0] == '-t':
			h = opt[1].split(':')
			vdr_inst.host = h[0]
			if len(h) > 1:
				vdr_inst.port = int(h[1])
except:
	print_usage()
	sys.exit(1)

# get channels
print 'Retrieving channel info from VDR...'
vdr_inst.readchannels()
if len(vdr_inst.channels) == 0:
	vdr_inst.retrievechannels()
print 'Found ' + str(len(vdr_inst.channels)) + ' channels'

# list channels if requested
if list_channels:
	print 'expg currently supports these channels:'
	
	def sortchans(x, y):
		r = cmp(x[1], y[1])
		if r == 0:
			return cmp(x[0], y[0])
		return r

	chans = []
	for sid in retrievers.keys():
		if vdr_inst.channels.has_key(sid):
			chans.append((sid, vdr_inst.channels[sid].name))
		else:
			chans.append((sid, '-???-'))
	chans.sort(sortchans)
	for ch in chans:
		print string.ljust(ch[1], 20) + ' (SID: ' + str(ch[0]) + ')'
	sys.exit(1)	

# identify channels specified by user
for opt in rest:
	ch = vdr_inst.getchannel(opt)
	if ch is not None:
		channels.append(ch)
	else:
		print 'Cannot identify channel from ' + opt

if len(channels) == 0:
	print 'Unable to identify any channel'
	print_usage()
	sys.exit(1)

# get epg data
print 'Retrieving EPG data from VDR...'
epgevents = 0
try:
	epgevents = vdr_inst.readepg()
except:
	pass
if epgevents == 0:
	epgevents = vdr_inst.retrieveepg()

try:
	for chan in channels:
		print 'Processing channel: ' + chan.name + ' with ' + str(len(chan.events)) + ' known events'

		for days in range(0, days_ahead):
			# setup time to midnight of program's day
			tm_tup = time.localtime(time.time() + (days * 24 * 3600)) 
			tm_int = int(time.mktime((tm_tup[0], tm_tup[1], tm_tup[2], 0, 0, 0, tm_tup[6], tm_tup[7], tm_tup[8])))
			print '   retrieving data for ' + time.ctime(tm_int),
			ret = retrieveepg(chan, tm_int)
			if ret is None:
				print 'Error while retrieving EPG data'
				raise Exception
			else:
				print '   found ' + str(ret) + ' new events',
			print ''
			#print str(chan)

	if not query_only:
		def f(x): return x.source is not None and x.source == 'www'
		for ch in channels:
			ch.events = filter(f, ch.events)
		if len(ch.events) > 0:
			print 'Transmitting new events to VDR...'
			if not vdr_inst.updateepg(channels):
				print 'Error while sending EPG data to VDR'
		else:
			print 'No new events to transmit to VDR'
except:
	print "An error occurred, VDR's EPG data is not being modified"

vdr_inst.close()

