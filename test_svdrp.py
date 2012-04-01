#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Autorecord favorite VDR programs via SVDRP.
# Copyright (C) Kenneth Falck 2011.
# Distribution allowed under the Simplified BSD License.
import telnetlib
import event
import time
from datetime import datetime, timedelta
import re
import sys

# VDR server
VDR_HOST = '127.0.0.1'
VDR_PORT = 6419
VDR_PORT = 2001

class SVDRPClient(object):
    def __init__(self, host, port):
        self.telnet = telnetlib.Telnet()
        self.telnet.open(host, port)
        self.read_response()
    
    def close(self):
        self.telnet.close()
    
    def send_command(self, line):
        #print '>>>', line
        self.telnet.write(line + '\r\n')
    
    def read_line(self):
        line = self.telnet.read_until('\n', 10).replace('\n', '').replace('\r', '')
        #print '<<<', line
        if len(line) < 4: return None
        return int(line[0:3]), line[3] == '-', line[4:]
    
    def read_response(self):
        response = []
        line = self.read_line()
        if line: response.append(line)
        while line and line[1]:
            line = self.read_line()
            if line: response.append(line)
        return response
    
    def confirm_shutdown(self):
        self.send_command('PLUG shutdown CONF')
        line = self.read_response()
        num, dummy, message = line[0]
        return int(num), message
    
client = SVDRPClient(VDR_HOST, VDR_PORT)
#num, message = client.confirm_shutdown()
#client.send_command('chan')
#client.send_command('help')
client.send_command('lstc')
#num = 0
#message = client.read_line()
#print num, message
channels = []
for num, flag, message in client.read_response():
    tokens = message.strip().split(':')
    name = tokens[0]
    m =  re.search('\d+ ',name)
    no, name = re.split(' ',name,maxsplit=1)
    #print "iNO = %s, %s" % (m.group(0), m.group(1))
    print "iNO = %s" % no
    nametokens = name.split(';')
    name_tok = nametokens[0]
    if len(nametokens)>1:
        provider = nametokens[1]

    freq = int(tokens[1])
    pol = tokens[2]
    source = tokens[3]
    srate = int(tokens[4])
    vpid = tokens[5]
    apids = tokens[6]
    tpid = int(tokens[7])
    ca = tokens[8]
    sid = tokens[9]
    nid = tokens[10]
    tid = tokens[11]
    rid = tokens[12]

    tokens = apids.split(';')
    apids = map(str, tokens[0].split(','))

    if len(tokens) == 2:
        dpids = map(str, tokens[1].split(','))

    #id = string.join([self.source, nid, tid,
    #                               sid, rid], '-')

    print "%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%si" % (
        name,nametokens,name_tok,freq,pol,source,srate,vpid,apids,tpid,ca)
    channels.append(name)

client.send_command('lste 1')

for channel in channels:
    print channel
Titre, SousTitre, Description = ('','','')
ev = event.Event()
for num, flag, message in client.read_response():
    print message
    if message[0] == 'T':
        ev.title = message[2:]
    elif message[0] == 'S':
        ev.subtitle= message[2:]
    elif message[0] == 'D':
        Description  = message[2:]
        ev.desc = Description.replace('|','\n')
    elif message[0] == 'E' and message != 'End of EPG data':
        # event start
        ev.parseheader(message[2:])
        ev.source = 'vdr'
        print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)
        #START = Wed Apr 11 01:10:00 2012
        print 'START = %s ' % time.ctime(int(ev.start))
        #time.struct_time(tm_year=2012, tm_mon=4, tm_mday=10, tm_hour=23, tm_min=10, tm_sec=0, tm_wday=1, tm_yday=101, tm_isdst=0) 
        print 'getitme = %s ' % time.gmtime(int(ev.start))
        #ev.channel = ch

    if message[0] == 'e':
        #(year,mois, mday, heure, min, sec) = time.gmtime(int(ev.start))
        time_start = time.gmtime(int(ev.start))
        stop = ev.start + ev.dur
        time_stop = time.gmtime(int(stop))
        #print '%02d:%02d - %02d:%02d' % (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min)
        #print '\nTitre = %s\nSousTitre = %s\n Desc = %s ' % (
        #                                ev.title,ev.subtitle,ev.desc)
        #print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)a
        print ('%02d:%02d - %02d:%02di => %s' %
            (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
            ev.title))
        Titre, SousTitre, Description = ('','','')
client.close()

