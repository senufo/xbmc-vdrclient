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

import os.path
import re
import string
import struct
import time
from types import *

import svdrp


class Recording:
    """This class represents a VDR recording.
    
    Data about a recording can either be obtained via SVDRP or by
    disk access (which gives more accurate information).
    
    Note that when setting an SVDRP object as a recording's source,
    this SVDRP object is implicitely accessed in some of the getXXX()
    functions. Further accesses go to cache but the SVDRP connection
    may not be closed until after the first access to those getXXX()
    functions.
    """

    def __init__(self, source = None, index = None):
        """Creates a new Recording object.
        
        The optional source argument is expected to be an SVDRP object or a
        string containing a recording description in the format as
        returned by the SVDRP LSTR command or a string containing
        the path to a recording.
        
        The index is expected to be an integer containing the index
        of this recording into the total list of recordings of a VDR
        instance (base 1). If the source argument is a recording
        description the index is derived from that description rather
        than from the index argument which may thus be ommitted.
        
        With SVDRP connections it is more efficient to run the LSTR
        command once and create a Recording object per line than
        creating multiple Recording object with an SVDRP object and
        varying indexes as this requires as many executions of the
        LSTR command.
        """
        self.source = source
        self.index = index
        self.name = None
        self.summary = None
        self.start = None
        self.prio = None
        self.lifetime = None
        self.marks = None
        self.resume = None
        
        if source is not None:
            self.init(source, index)
    
    
    def init(self, source, index = None):
        """Initialize the data associated with this recording object
        from the given source.
        
        The source argument is expected to be an SVDRP object or a
        string containing a recording description in the format as
        returned by the SVDRP LSTR command or a string containing
        the path to a recording.
        
        The index is expected to be an integer containing the index
        of this recording into the total list of recordings of a VDR
        instance (base 1). If the source argument is a recording
        description the index is derived from that description rather
        than from the index argument which may thus be ommitted.
        
        With SVDRP connections it is more efficient to run the LSTR
        command once and create a Recording object per line than
        creating multiple Recording object with an SVDRP object and
        varying indexes as this requires as many executions of the
        LSTR command.
        """
        print "SOURCE = %s " % source
        #if isinstance(source, svdrp.SVDRP) and index is not None:
        #    pat = re.compile('250[ -]' + str(index) + ' ')
        #    result = source.write_cmd('LSTR\n')
        #    if result[0:3] != '250':
        #        print 'lstr returned: ' + result
        #    for line in result.split('\n'):
        #        line = line.strip()
        #        if pat.match(line):
        #            self.init(line)
                    
        #elif isinstance(source, StringType) and len(source) > 5 and source[:3] == '250':
        if isinstance(source, StringType) and len(source) > 5 and source[:3] == '250':
            tokens = source.strip()[4:].split(None, 3)
            if len(tokens) == 4:
                self.index = int(tokens[0])
                if len(tokens[1].split('.')) == 2:
                    tokens[1] = tokens[1] + '.' + time.strftime('%Y')
                self.start = int(time.mktime(time.strptime(tokens[1] + ' ' + tokens[2].replace('*', ''), '%d.%m.%Y %H:%M')))
                self.name = tokens[3]
                if tokens[2].find('*'):
                    self.resume = 0
                else:
                    self.resume = -1
        
        #elif isinstance(source, StringType) and os.path.isdir(source):
        elif os.path.isdir(source):
            pat = re.compile('(/video\d*/)?(.*)/(\d{4}-\d\d-\d\d\.\d\d\.\d\d)\.(\d\d)\.(\d\d)\.rec/?')
            result = pat.match(source)
            if result is None:
                raise TypeError, 'path of recording has unknown format'
            self.index = index
            self.name = result.group(2)
            self.start = int(time.mktime(time.strptime(result.group(3), '%Y-%m-%d.%H.%M')))
            self.prio = int(result.group(4))
            self.lifetime = int(result.group(5))
        
        else:
            raise TypeError, 'argument source has invalid type'
    
    
    def getsource(self):
        """Returns the data source of this recording object.
        
        The return value is either a SVDRP object or a string
        containing the path to this recording.
        """
        return self.source
    
    
    def setsource(self, source):
        """Sets a data source for this recording object.
        
        The source argument is expected to be either a SVDRP object
        or a string containing the path to a recording.
        """
        if isinstance(source, svdrp.SVDRP) or \
            (isinstance(source, StringType) and \
            os.path.isdir(source)):
            self.source = source
        else:
            raise TypeError, 'argument source has invalid type'
    
    
    def getindex(self):
        """Returns the index of this recording.
        
        The return value is an integer representing the index of this
        recording into the complete list of recordings of a VDR
        instance.
        """
        return self.index
    
    
    def getname(self):
        """Returns the name of this recording.
        
        The return value is a string containing the name of this
        recording.
        """
        return self.name
    
    
    def getsummary(self):
        """Returns the summary of this recording.
        
        Depending on the source given at construction time, the
        summary for this recording is retrieved via SVDRP or from
        the summary.vdr file.
        
        The return value is a string containing the summary of this
        recording.
        """
        if self.summary is None:
            if isinstance(self.source, svdrp.SVDRP):
                self.summary = self.source.lstr(self.index)
            elif isinstance(self.source, StringType) and os.path.isdir(self.source):
                fh = open(os.path.join(self.source, 'summary.vdr'), 'r')
                self.summary = fh.read()
                fh.close()
        return self.summary
    
    
    def getstart(self):
        """Returns the start time of this recording.
        
        The return value is an integer containing the time when the
        recording started as seconds since the epoch.
        """
        return self.start
    
    
    def getprio(self):
        """Return the priority of this recording.
        
        The return value is an integer containing the priority of
        this recording (which is derived from the corresponding
        timer).
        """
        return self.prio
    
    
    def getlifetime(self):
        """Returns the lifetime of this recording.
        
        The return value is an integer containing the number of days
        since start this recording is guaranteed to not be deleted by
        VDR.
        """
        return self.lifetime
    
    
    def getmarks(self):
        """Returns the editing marks of this recording.
        
        The return value is a list of Mark objects representing the
        editing marks of this recording.
        """
        if self.marks is None:
            if isinstance(self.source, StringType) and \
                os.path.isdir(self.source) and \
                os.path.isfile(os.path.join(self.source, 'marks.vdr')):
                
                self.marks = []
                fh = open(os.path.join(self.source, 'marks.vdr'), 'r')
                line = fh.readline()
                while line:
                    mk = mark.Mark(line.strip())
                    self.marks.append(mk)
                    line = fh.readline()
                fh.close()
                
        return self.marks
    
    
    def getresume(self):
        """Returns the resume offset for this recording.
        
        The return value is an integer containing the resume offset
        of this recording.
        
        If the recording does not have a resume offset, the return
        value is -1. If the recording has an unknown resume offset
        (may occur when retrieving recording data via SVDRP), the
        return value is 0.
        """
        if self.resume is None:
            dfn = None
            if isinstance(self.source, StringType) and \
                os.path.isdir(self.source):
                if os.path.isfile(os.path.join(self.source, 'resume.vdr')):
                    fh = open(os.path.join(self.source, 'resume.vdr'), 'r')
                    nr = fh.read()
                    fh.close()
                    self.resume = struct.unpack('l', nr)[0]
                else:
                    self.resume = -1
            elif isinstance(self.source, StringType) and len(self.source) > 5 and self.source[:3] == '250':
                dfn = self.source
            elif isinstance(self.source, svdrp.SVDRP):
                dfn = self.source.lstr(self.index)
            
            if dfn is not None:
                tokens = dfn.strip()[4:].split(None, 3)
                if len(tokens) == 4:
                    if tokens[2].find('*'):
                        self.resume = 0
                    else:
                        self.resume = -1
        return self.resume
    
    
    def isnew(self):
        """Returns whether this recording is unwatched, i.e. whether
        it does not have a resume offset.
        """
        return self.getresume() == -1


    def __cmp__(self, other):
        """Compares two Recording objects by their start times.
        """
        return cmp(self.start, other.start)








