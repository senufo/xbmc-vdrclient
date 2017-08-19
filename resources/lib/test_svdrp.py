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
#VDR_HOST = '127.0.0.1'
VDR_HOST = '192.168.1.6'
VDR_PORT = 6419
#VDR_PORT = 2001

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
#client.send_command('lstc')
#client.send_command('lstr')
#cmd_svdrp = '1:37:2012-04-27:1730:1745:50:30:C Ã  dire:'
#client.send_command('NEWT %s' % cmd_svdrp)
#client.close()
#exit()

#num = 0
#nbrep = len(client.read_response())
#print "LEN = %s " %nbrep
#ev = event.Event()
records = []
#nbEPG = len(self.vdrpclient.read_response())
NbEPG = 500
for i in range(1,NbEPG):
    print "=" * 30
    ev = event.Event()
    print ('lste %d' % i)
    #client.send_command('lstr %d' % i)
    client.send_command('lste %d' % i)
    """
    C I-1-1-1007 TMC 
    E 61765 1297366800 7800 0 FF 
    T La nuit au musée 
    D Catégorie : Comédie/Film|Comédie. Récemment embauché comme agent de sécurité
    au Musée de New York, Larry fait une découverte stupéfiante : tout le musée
    prend vie à la nuit tombée !||Réalisation : Shawn Levy||Avec : Ben Stiller,
    Carla Gugino, Robin Williams, Dick Van Dyke, Mickey Rooney, Ricky Gervais, Steve
    Coogan, Bill Cobbs 
    G 14 
    X 2 03 fra  
    F 25 
    P 50 
    L 99 
    @ <epgsearch><channel>42 -
    TMC</channel><update>0</update><eventid>61765</eventid><bstart>600</bstart><bstop>1800</bstop></epgsearch><pin-plugin><protected>no</protected></pin-plugin> 
    End of recording information 

    C 	<channel id> <channel name>
    E 	<event id> <start time> <duration> <table id> <version>
    T 	<title>
    S 	<short text>
    D 	<description>
    G 	<genre> <genre>...
    R 	<parental rating>
    X 	<stream> <type> <language> <descr>
    V 	<vps time>
    e
    c
    """
    for num, flag, message in client.read_response():
        #print "%d, %s, %s " % (num, flag, message)
        if num != 550:
            #Parse l'EPG renvoyé par VDR
            if message[0] == 'T':
                ev.title = message[2:]
                print "TITLE = %s " % ev.title
            elif message[0] == 'C':
                ev.channel = message[2:]
                print "channel : %s" % ev.channel
            elif message[0] == 'S':
                ev.subtitle = message[2:]
                print "subTITLE = %s " % ev.subtitle
            elif message[0] == 'D':
                Description  = message[2:]
                ev.desc = Description.replace('|','\n')
                print "desc : %s" % ev.desc
            elif message[0] == 'E' and message != 'End of EPG data':
                try:
                 print "End : %s " % message
                 if 1:
                    heure = message[2:].split(' ')
                    print "HEURE = %s " % heure
                    #(year,mois, mday, heure, min, sec) = time.gmtime(int(ev.start))
                    #Tient compte du fuseau horaire
    #                if time.daylight != 0:
    #                    time_start = int(ev.start) - time.altzone
    #                else:
    #                    time_start = int(ev.start)
    #                stop = time_start + ev.dur
                    #time_start = time.gmtime(int(heure[0]))
                    #time_stop = time.gmtime(int(heure[1]))
                    time_start = time.gmtime(int(heure[1]))
                    print '------------'
                    #print (year,mois, mday, heure, min, sec)
                    print '------------'
                    #Debut, Fin et Nom de l'EPG
                    ev.heure_start = '%02d:%02d' % (time_start.tm_hour,time_start.tm_min)
                    ev.date = '%02d-%02d-%04d' % (time_start.tm_wday,
                                                  time_start.tm_mon,time_start.tm_year)
                    ev.duree = '%04d' % int(heure[2])
                    epg_data = ('%02d:%02d : %04d-%02d-%02d' % (time_start.tm_hour,time_start.tm_min,
                         time_start.tm_year,time_start.tm_mon, time_start.tm_wday
                         ))
                    print "EPD = ->%s<-, duree = %s, start = %s" % (ev.date, ev.duree, ev.heure_start)
                except:
                    print ">>>>>>>>>>>ERREUR<<<<<<<<<<<<<<<<<<<"
                    ev.date = "XX"
        #print '=>%s : %s : %s : %s' % (ev.date,ev.heure_start, ev.duree, ev.title)
        records.append(ev) 
    else:
        i = 600
        break
client.close()

for record in records:
    print "=" * 60
    print '%s : %s : %s : %s' % (record.date,record.heure_start, record.duree,
                                 record.title)
    #print '%s' % ev.desc
exit()

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

client.send_command('lste 8')

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
        ev.start = ev.start - time.altzone
        time_start = time.gmtime(int(ev.start))
        stop = ev.start + ev.dur
        time_stop = time.gmtime(int(stop))
        print "DAYLIGHT ", time.daylight
        print "ALTZONE", time.altzone
        #print '%02d:%02d - %02d:%02d' % (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min)
        #print '\nTitre = %s\nSousTitre = %s\n Desc = %s ' % (
        #                                ev.title,ev.subtitle,ev.desc)
        #print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)a
        print ('%02d:%02d - %02d:%02di => %s' %
            (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
            ev.title))
        Titre, SousTitre, Description = ('','','')
client.close()

