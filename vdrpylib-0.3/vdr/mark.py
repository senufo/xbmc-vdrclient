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

import re

class Mark:
    """This class represents an editing mark of a VDR recording.

    The seconds variable is an integer representing the offset of
    this mark into the recording in seconds.
    
    The frames variable is an integer representing the offset of
    this mark into the recording relative to the position 
    indicated by the seconds variable. With 25 fps recordings the
    value of this variable ranges between 0 and 24.
    
    The comment variable is a string containing the comment of this
    mark. If there is no comment associated with this mark, this
    variable is None.
    """
    _pat = re.compile('(\d\d):(\d\d):(\d\d)(\.(\d+))?( (.*))?')

    def __init__(self, str = None):
        """Construct a new Mark object.
        
        The optional str argument is a string containing the
        specification of an editing mark in the format of VDR's
        marks.vdr file.
        """
        self.seconds = 0
        self.frames = 0
        self.comment = None
        
        if str is not None:
            self.parse(str)


    def parse(self, str):
        """Parse a string for editing mark data and update this
        object's data accordingly.
        
        The str argument is a string containing the
        specification of an editing mark in the format of VDR's
        marks.vdr file.
        """
        res = _pat.match(str)
        self.seconds = int(res.group(1)) * 3600 + int(res.group(2)) * 60 + int(res.group(3))
        if result.group(4) is None:
            self.frames = 0
        else:
            self.frames = int(result.group(5))
        self.comment = result.group(7)
    
    
    def __str__(self):
        """Returns a string representation of this mark in the format
        of VDR's marks.vdr file.
        """
        s = str(self.seconds / 3600) + ':' + str((self.seconds / 60) % 60) + ':' + str(self.seconds % 60)
        if self.frames != 0:
            s = s + '.' + str(self.frames)
        if self.comment is not None:
            s = s + ' ' + self.comment
        return s



        
