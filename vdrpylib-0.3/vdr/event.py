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

class Event:
    """Represents an event in the EPG data, i.e. a program.
    """

    def __init__(self):
        """Constructs an Event object with all fields set to None.
        """
        self.channel = None
        self.id = None
        self.start = None
        self.dur = None
        self.tableID = None
        self.title = None
        self.subtitle = None
        self.desc = None
        self.source = None
        self.vps = None
        

    def __str__(self):
        """Returns a string representation for this event in the
        format of VDR's epg.data file.
        """
        s = 'E ' + str(self.id) + ' ' + str(self.start) + ' ' + str(self.dur)
        if self.tableID is not None and self.tableID != 0:
            s = s + ' ' + self.tableID
        s = s + '\n'
        if self.title is not None:
            s = s + 'T ' + self.title + '\n'
        if self.subtitle is not None:
            s = s + 'S ' + self.subtitle + '\n'
        if self.desc is not None:
            s = s + 'D ' + self.desc + '\n'
        s = s + 'e\n'
        return s
    
    
    def __cmp__(self, other):
        """Compares this event against another by their start times.
        """
        return cmp(self.start, other.start)
    

    def parseheader(self, str):
        """Parses a string containing an event specification in the
        format of VDR's epg.data file.
        
        The first argument is the specification string to parse.
        
        Returns true if the specification string could be parsed
        successfully, false else.
        """
        tokens = str.split()
        if len(tokens) < 3 or len(tokens) > 4:
            return 0
        self.id = int(tokens[0])
        self.start = int(tokens[1])
        self.dur = int(tokens[2])
        if len(tokens) == 4:
            self.tableID = tokens[3]
        return 1
