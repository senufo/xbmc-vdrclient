# -*- coding: utf-8 -*-
"""
This class represents a program channel.
"""
import string
import re

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
    def __init__(self, line = None, key = None, name = None):
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

        if self.vpid == '0' and len(self.apids):
            self.radio = True
            self.tv = False
        elif self.vpid == '0' and len(self.apids) == 0:
            self.radio = False
            self.tv = False
        else:
            self.radio = False
            self.tv = True

    def parse_line(self, definition):
        """Parses a standard channel specification as can be found in
        SVDP lstc command.
        
        All fields of this channel object are set according to the 
        specification string given in the first argument.
        """
        tokens = definition.strip().split(':')
        self.name = tokens[0]
        self.no, self.name = re.split(' ', self.name, maxsplit=1)
        #print "iNO = %s" % self.no
        self.nametokens = self.name.split(';')
        self.name_tok = self.nametokens[0]
        if len(self.nametokens)>1:
            provider = self.nametokens[1]

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

        #print "%s, %s,%s,%s,%s,%s,%s,%s,%s,%s,%si" % (
        #    name,nametokens,name_tok,freq,pol,source,srate,vpid,apids,tpid,ca)


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

