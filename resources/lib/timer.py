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

#####################################################################
# Todo:
#####################################################################
# Find a nice way to represent the channel as an object


#####################################################################
# imports
#####################################################################
import re
import string
from types import *


#####################################################################
# module wide variables
#####################################################################
# a regex describing the format of a timer specification string
#2 0:45:MTWTF--:1830:2000:50:99:Stargate Atlantis:<epgsearch><channel>45 - NRJ
#12</channel><update>0</update><eventid>56590</eventid><bstart>600</bstart><bstop>1800</bstop></epgsearch><pin-plugin><protected>no</protected></pin-plugin>

#_pat = re.compile('((?P<index>\d+) )?(?P<id>\d+):(?P<channel>\d+):(?P<day>\d{0,2}|.{7}):(?P<start>\d+):(?P<stop>\d+):(?P<prio>\d+):(?P<lifetime>\d+):(?P<name>[^:]*):(?P<summary>.*)')
_pat = re.compile('((?P<index>\d+) )?(?P<id>\d+):(?P<channel>\d+):(?P<day>\d{4}-\d{2}-\d{2}|.{7}):(?P<start>\d+):(?P<stop>\d+):(?P<prio>\d+):(?P<lifetime>\d+):(?P<name>[^:]*):(?P<summary>.*)')


#####################################################################
# module wide functions
#####################################################################
def parsetime(t):
    """Converts a string containing a start or stop time in VDR's
    standard format ('hhmm') to the number of seconds since
    midnight.
    """
    return int(t[0:2]) * 3600 + int(t[2:4]) * 60


def strtime(t):
    """Converts the numeric start and stop time into a string
    with VDR's standard format ('hhmm').
    """
    return string.zfill(str(int(t / 3600)), 2) + string.zfill(str(int(t / 60) % 60), 2)


def parserecurrence(s):
    """Converts the given string from VDR's representation of
    recurring timers to a list with 7 elements evaluating to true
    or false.
    """
    recurrence = [ 0 ] * 7
    for counter in range(0, 7):
        recurrence[counter] = (not (s[counter] == '-'))
    return recurrence


def strrecurrence(r):
    """Converts the internal recurrence representation into a string
    with VDR's format.
    """
    s = ''
    for x in r:
        if x:
            s = s + 'X'
        else:
            s = s + '-'
    return s


#####################################################################
# class definitions
#####################################################################
class Timer:
    """This class represents a VDR timer.
    
    The index variable is an integer containing the index of this
    timer into the total list of timers of a VDR instance.
    
    The name variable is a string containing the name of this timer
    also serving as the name for the corresponding recording.
    
    The summary variable is a string containing the name of this
    timer also serving as the name for the corresponding recording.
    
    The channel variable is an instance of class Channel containing
    the channel this timer should record on.
    
    The start variable is an integer containing the number of seconds
    after midnight specifying the start time of the timer.
    
    The stop variable is an integer containing the number of seconds
    after midnight specifying the stop time of the timer.
    
    The day variable is an integer. If the recurrence variable is
    None, it contains the day of month on which the recording is to
    take place. If the recurrence variable is not None, day specifies
    the day of month on which the recurring recording is to take
    place the first time.
    
    The recurrence variable is a 7-element list containing values
    evaluating either to true or false. Each element represents a
    week day, element 0 being Monday through element 6 being Sunday.
    Their values indicate whether the recording shall take place at
    the corresponding week day. If the recurrence variable is not
    None, day specifies the day of month on which the recurring
    recording is to take place the first time.
    If the recurrence variable is None, this is a one-shot timer.
    
    The prio variable is an integer containing the priority of this
    timer. Values may range between 1 and 99.

    The lifetime variable is an integer containing the lifetime of
    this timer in days. Values may range between 1 and 99.
    
    The active variable is an integer evaluating to true if this
    timer is active and evaluating to false otherwise.
    """

    def __init__(self, s = None, index = None, vdr = None):
        """Creates a new Timer object.
        
        The optional s argument is expected to be a string containing
        a timer specification as can be found in VDR's timers.conf
        file or as returned by the LSTT SVDRP command.
        
        The optional index argument is expected to be an integer
        containing the index of this timer into the global list of
        timers of a VDR instance. The index of a timer can only be
        derived from its specification string (i.e. the s argument)
        when it it's in the SVDRP format. When reading VDR's
        timers.conf file the timer indexes are encoded implicitely in
        the line number and have thus to be passed explicitely to
        this constructor.
        
        The optional vdr argument is expected to an instance of class
        VDR. When specified, this class can offer more advanced
        abstractions than without it in which case it merely serves
        as a data container.
        """
        self.index = index
        self.name = None
        self.summary = None
        self.channel = None
        self.start = None
        self.stop = None
        self.day = None
        self.recurrence = None
        self.prio = None
        self.lifetime = None
        self.active = None
        self.vdr = vdr
        
        if s is not None:
            self.parse(s)
            print "PARSE TIMER" 
    
    def parse(self, s):
        """Parses a timer definition and updates the data of this
        object accordingly.
        
        The s argument is expected to be a string containing
        a timer specification as can be found in VDR's timers.conf
        file or as returned by the LSTT SVDRP command. Note that only
        the SVDRP version allows to derive the index of a timer from
        the specification string.
        
        The return value evaluates to true if the string s could be
        parsed successfully.
        """
        print 'S 184 = %s ' % s
        if s is not None and isinstance(s, StringType) and len(s) > 5:
            s = s.strip()
            print 'S = %s ' % s
            if s[0:3] == '250':
                s = s[4:]
            res = _pat.match(s)
            if res is not None:
                if res.group('index') is not None:
                    self.index = int(res.group('index'))
                self.active = int(res.group('id'))
                self.channel = int(res.group('channel'))
                d = res.group('day')
                if len(d) == 7:
                    self.day = d
                    self.recurrence = parserecurrence(d)
                else:
                    #self.day = int(d)
                    self.day = d
                    self.recurrence = None
                self.start = parsetime(res.group('start'))
                self.stop = parsetime(res.group('stop'))
                self.prio = int(res.group('prio'))
                self.lifetime = int(res.group('lifetime'))
                self.name = res.group('name')
                if self.name is None:
                    self.name = ''
                self.summary = res.group('summary')
                if self.summary is None:
                    self.summary = ''
                return 1
        return 0
    
    
    def __cmp__(self, other):
        """Compares two Timer objects by their indexes.
        """
        return cmp(self.index, other.index)


    def __str__(self):
        """Returns a string representation of this object in the
        format of VDR's timers.conf file.
        """
        day = ''
        if self.recurrence is not None:
            day = strrecurrence(self.recurrence)
        else:
            day = str(self.day)
        return string.join(map(str, [self.active, self.channel, day, strtime(self.start), strtime(self.stop), self.prio, self.lifetime, self.name, self.summary]), ':')


    def getchannel(self):
        """Returns the channel this timer refers to.
        
        In contrast to the numeric channel variable, this function
        returns a channel object if the vdr variable is not None.
        
        The return value is a instance of class Channel or None if
        this timer refers to no or an invalid channel or the vdr
        variable is None.
        """
        if self.vdr and self.vdr.channels and self.channel:
            return self.vdr.getchannel(self.channel)
        return None
            
