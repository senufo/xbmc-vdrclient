#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Autorecord favorite VDR programs via SVDRP.
# Copyright (C) Kenneth Falck 2011.
# Distribution allowed under the Simplified BSD License.
import telnetlib
import event
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
client.send_command('lste 1')
#client.send_command('lstc')
#num = 0
#message = client.read_line()
#print num, message
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
        #ev.channel = ch

    if message[0] == 'e':
        print '\nTitre = %s\nSousTitre = %s\n Desc = %s ' % (
                                        ev.title,ev.subtitle,ev.desc)
        print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)
        Titre, SousTitre, Description = ('','','')
client.close()

