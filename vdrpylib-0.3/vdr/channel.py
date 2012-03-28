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

import string

class Channel:
    """This class represents a program channel.
    
    It is intended to a container for the technical channel data as
    as for EPG Event objects.
    
    VDR may place a single physical channel at several locations in
    its global list of channels. This class does not represent a slot
    in the global list of channels but a physical channel. Physical
    channels are assumed to be uniquely identifiable by their SID.
    
    The indexes variable is a list containing the indexes of this
    channel in the global list of channels of a VDR instance.
    
    The name variable is a string containing the name of this
    channel.
    
    The freq variable is an integer containing the frequency of this
    channel in Hz.
    
    The pol variable is a string of length one containing the
    polariazation of this channel. 'h' stands for horizontal, 'v' for
    vertical polarization.
    
    The diseqc variable is an integer containing the DiSEqC code for
    this channel.
    
    The srate variable is an integer containing the symbol rate of
    this channel.
    
    The vpid variable is an integer containing the video PID of this
    channel.
    
    The apids variable is a list of integers containing the audio
    PIDs of this channel.
    
    The dpis variable is a list of integers containing the dolby
    digital (AC3) PIDs of this channel.
    
    The tpid variable is an integer containing the teletext PID of
    this channel.
    
    The ca variable is an integer defining how the channel can be
    accessed over the available DVB cards.
    
    The sid variable is an integer containing the service ID of this
    channel.
    
    The events variable is a list of Event objects sorted by start
    time. The list should not be manipulated directly but only
    through the XXXevent() functions of this class.
    """
    def __init__(self, line = None, index = None, key = None, name = None):
        self.id = None
        self.indexes = []
        self.name = name
        self.provider = ''
        self.freq = None
        self.pol = None
        self.source = None
        self.srate = None
        self.vpid = None
        self.apids = []
        self.dpids = []
        self.tpid = None
        self.ca = None
        self.sid = None
        self.nid = None
        self.tid = None
        self.rid = None
        self.tv = False
        self.radio = False
        self.in_conf = False
        self.in_epg = False
        self.events = []

        if line:
            self.parse_line(line)
        if key:
            self.parse_key(key)
        if index:
            self.indexes.append(index)

        if self.vpid == '0' and len(self.apids):
            self.radio = True
            self.tv = False
        elif self.vpid == '0' and len(self.apids) == 0:
            self.radio = False
            self.tv = False
        else:
            self.radio = False
            self.tv = True

        
    def __str__(self):
        """Creates a string representation of this channel object
        in the format of VDR's channels.conf file.
        """
        apids = string.join([string.join(map(str, self.apids), ','), string.join(map(str, self.dpids), ',')], ';')
        return string.join(map(str, [self.name+";"+self.provider, self.freq, self.pol, self.source, self.srate, self.vpid, apids, self.tpid, self.ca, self.sid,self.nid,self.tid,self.rid]), ':')

    
        def dump(self):
                print 'name: %s' % self.name
                print 'provider: %s' % self.provider
                print 'freq: %s' % self.freq
                print 'pars: %s' % self.pars
                print 'source: %s' % self.source
                print 'srate: %s' % self.srate
                print 'vpid: %s' % self.vpid
                print 'tpid: %s' % self.tpid
                print 'ca: %s' % self.ca
                print 'sid: %s' % self.sid
                print 'nid: %s' % self.nid
                print 'tid: %s' % self.tid
                print 'rid: %s' % self.rid


    def parse_line(self, definition):
        """Parses a standard channel specification as can be found in
        VDR's channels.conf file.
        
        All fields of this channel object are set according to the 
        specification string given in the first argument.
        """
        tokens = definition.strip().split(':')
        name = tokens[0]
        nametokens = name.split(';')
        self.name = nametokens[0]
        if len(nametokens)>1:
            self.provider = nametokens[1]

        self.freq = int(tokens[1])
        self.pol = tokens[2]
        self.source = tokens[3]
        self.srate = int(tokens[4])
        self.vpid = tokens[5]
        apids = tokens[6]
        self.tpid = int(tokens[7])
        self.ca = tokens[8]
        self.sid = tokens[9]
        self.nid = tokens[10]
        self.tid = tokens[11]
        self.rid = tokens[12]

        tokens = apids.split(';')
        self.apids = map(str, tokens[0].split(','))

        if len(tokens) == 2:
            self.dpids = map(str, tokens[1].split(','))

        self.id = string.join([self.source, self.nid, self.tid,
                                       self.sid, self.rid], '-')

 
    def parse_key(self, key):
        tokens = key.split('-')

        self.source = tokens[0]
        self.nid    = tokens[1]
        self.tid    = tokens[2]
        self.sid    = tokens[3]
        try:
            self.rid    = tokens[4]
        except:
            print 'WARNING: %s contains no rid, setting to 0' % key
            self.rid    = '0'
          
        self.id     = key


    def addevent(self, ev):
        """Add an EPG event to the list of events for this channel.
        
        If the event has no ID one is assigned.
        
        The first argument shall be an Event object representing
        the event to be added. The start time of the event to add
        must be later than the end of any other event of this
        channel.
        
        The return value is the ID of the event if it satisfied the
        given restrictions and was added, else None is returned.
        """
                
        if len(self.events):
            if ev.start <= self.events[-1].start:
                print 'Bad event: %s' % ev.title
                return None

            if self.events[-1].start + self.events[-1].dur > ev.start:
                self.events[-1].dur = ev.start - self.events[-1].start

        if ev.id is None:
            if len(self.events) > 1:
                ev.id = (self.events[-2].id + 1) % 65536
            else:
                ev.id = 0

        self.events.append(ev)

        return ev.id
    
    
    def getepgstr(self):
        """Creates a string representation of this channel object
        in the format of VDR's epgdata file including all contained
        EPG events.
        """
        s = 'C ' + str(self.sid)
        if self.name is not None:
            s = s + ' ' + self.name
        s = s + '\n'
        for ev in self.events:
            s = s + str(ev)
        s = s + 'c\n'
        return s
