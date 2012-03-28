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

import cStringIO
import os.path
import re
import string

import channel
import event
import recording
import svdrp
import timer

class VDR:
    """This class represents a VDR instance and all its associated
    data.
    
    It is a container for channel objects and runtime-related data.
    It offers functions to retrieve channel and EPG data from the
    VDR files or via SVDRP.
    
    The channels variable is a dictionary containing integer objects
    with the service ID of a channel as key and Channel objects as
    values.
    
    The recordings variable is a list containing Recording objects.
    The recordings are sorted by their start time.
    
    The timers variable is a list containing Timer objects. The
    timers are sorted according to their index.
    
    The host variable is a string containing the name of the host
    running VDR.
    
    The port variable is an integer containing the port at which the
    SVDR protocol is available on host.
    
    The vdrfile variable is a string containing the path to the VDR
    executable.
    
    The videopath variable is a string containing the path to the VDR
    recordings (specify /video<n> with the lowest <n> in your system
    if you have multiple directories containing recordings).
    
    The following variables specify path names for VDR data files.
    They default to the VDR default file names. Their paths are
    derived from the videopath variable.
    
    The cafile variable is a string containing the name of VDR's 
    ca.conf file.
    
    The channelsfile variable is a string containing the name of
    VDR's channels.conf file.
    
    The epgfile variable is a string containing the path to VDR's 
    epg.data file.
    
    The setupfile variable is a string containing the path to VDR's 
    setup.conf file.
    
    The svdrpfile variable is a string containing the path to VDR's 
    svdrphosts.conf file.
    
    The timerfile variable is a string containing the path to VDR's 
    timers.conf file.
    """
    
    def __init__(self,
        host = 'localhost',
        port = svdrp.SVDRP_PORT,
        vdrfile = '/usr/local/bin/vdr',
        videopath = '/video',
        cafile = 'ca.conf',
        channelsfile = 'channels.conf',
        epgfile = 'epg.data',
        setupfile = 'setup.conf',
        svdrpfile = 'svdrphosts.conf',
        timerfile = 'timers.conf',
        close_connection=1):
        
        self.svdrp = None
        self.channels = {}
        self.recordings = []
        self.timers = []
        self.close_connection=close_connection
        
        self.host = host
        self.port = port
        
        self.vdrfile = vdrfile
        
        # determine all existing video paths
        self.videopath = videopath
        self.vpaths = self.getvpaths(self.videopath)
        
        # in the case of multiple video paths find where the
        # following files are located:
        self.cafile = self.findinvpaths(cafile)
        self.channelsfile = self.findinvpaths(channelsfile)
        self.epgfile = self.findinvpaths(epgfile)
        self.setupfile = self.findinvpaths(setupfile)
        self.svdrpfile = self.findinvpaths(svdrpfile)
        self.timerfile = self.findinvpaths(timerfile)
    
    
    def getvpaths(self, path):
        """Returns the available video paths (possibly) containing
        recordings in the system.
        """
        # XXX: this is so f#$#! broken, disabling
        return [path]
        
        pat = re.compile('([^0-9]*)([0-9]+)')
        result = pat.match(self.videopath)
        if result is None:
            return [path]
        else:
            paths = []
            #basepath = result.groups(1)
            basepath = result.group(1)
            print 'RLS: basepath is %s' % basepath
            print 'RLS: result is %s' % result.group(2)
            #curnr = int(result.groups(2))
            curnr = int(result.group(2))
        
        if basepath == None:
            basepath = ''
        curpath = basepath + str(curnr)
        while os.isdir(curpath):
            paths.append(curpath)
            curnr = curnr + 1
            curpath = basepath + str(curnr)
        return paths
    
    
    def findinvpaths(self, filename):
        """Tries to locate and verify the existence of a file in any
        of the vpaths.
        
        The filename variable is expected to be a string containing
        name of the file to be located.
        
        The return value is a string containing the full path of the
        file to be located. If no file with the specified name exists
        in any of the vpaths, None is returned.
        """
        for vpath in self.vpaths:
            path = os.path.join(vpath, filename)
            if os.path.isfile(path):
                return path
        return None
    
    
    def getsvdrp(self):
        """Returns an SVDRP object to the VDR instance represented by
        this VDR object.
        
        The connection is made to the remote endpoint identified by
        the host and port variables. If host or port are None, no
        connection can established and this function returns None.
        """
        if self.svdrp is None and self.host and self.port:
            self.svdrp = svdrp.SVDRP(self.host,
            self.port,close_connection=self.close_connection)
        return self.svdrp
    
    
    def close(self):
        """Closes the SVDRP connection to the VDR instance
        represented by this VDR object.
        """
        if self.svdrp is not None:
            self.svdrp.close()
            self.svdrp = None
    
    
    def getchannel(self, id):
        """Returns a channel by index, SID, or name.
        
        The id argument can be an integer which is either
        interpreted as an index of an channel if less than 1000 or as
        the service ID of a channel if greater or equal than 1000.
        The argument may also be a string containing the name of a
        channel. The specified string does not have to be a complete
        name as it is matched from the start of the name. If the
        string matches the start of multiple channel names, it is
        unspecified which channel is returned. The matching is
        performed case insensitively.
        
        The return value is a Channel object representing the
        channel found, or None if no channel could be identified from
        the first parameter
        """
        try:
            x = int(id)
            if x < 1000:
                # assume that this is a channel's index
                for ch in self.channels.values():
                    if x in ch.indexes:
                        return ch
            else:
                # assume that this is a channel's service ID
                if self.channels.has_key(x):
                    return self.channels[x]
        except:
            # a string, well, must be a channel's name then
            id = id.lower()
            id_len = len(id)
            for ch in self.channels.values():
                if ch.name.lower()[0:id_len] == id:
                    return ch
        
        return None
    
    
    def retrievechannels(self):
        """Retrieves the list of channels from VDR via SVDRP and adds
        them to the list of channels of this VDR object.
        
        The remote endpoint of the SVDRP connection used is
        identified by the host and port variables of this object.
        
        The return value is the list of Channel objects retrieved
        from VDR. If an error occurres the function returns None and
        the channel list of this VDR object is not modified.
        """
        counter = 0

        if self.getsvdrp() is None:
            return None

        schans = self.svdrp.lstc()

        for c in schans:
            self.addchannel(c)
            counter += 1
        
        return counter
    
    
    def readchannels(self):
        """Reads a list of channels from VDR's channels.conf file and
        adds them to this VDR object.
        
        This function reads the file named by the channelfile
        variable.
        
        The return value is the list of Channel objects read from the
        file.
        """
        fh = open(self.channelsfile, 'r')
        counter = 0

        line = fh.readline()
        while line:
            line = line.strip()
            if len(line) > 0 and line[0] != ':':
                counter = counter + 1
                c = channel.Channel(line, counter)
                c.in_conf = True
                self.addchannel(c)
            line = fh.readline()
        
        return counter
    
    
    def addchannel(self, channel):
        key = string.join([channel.source, channel.nid, channel.tid, 
                          channel.sid, channel.rid], '-')
        
        if not channel.id:
            channel.id = key
        
        self.channels[key] = channel
    
    
    def parseepg(self, fh):
        """Parses EPG data in the format of VDR's epg.data file and
        adds it to this VDR object.
        
        This function can also handle data with SVDRP line headers.
        
        The fh arguments is the file handle to read the data from.
        
        The return value is an integer containing the number of EPG
        events parsed.
        """
        ch = None
        ev = None
        counter = 0
        
        line = fh.readline()
        while line:
            line = line.strip()
            if line=='':
                continue
            
            # special handling of data coming in via SVDRP
            if line[0:4] == '215-':
                line = line[4:]
            if line[0:4] == '215 ':
                # EPG End
                break;
            
            if line[0:4] == '250 ':
                line = fh.readline()
                continue
            
            if line[0] == 'C':
                # channel start
                tokens = line.split()
                ch_id = tokens[1]
                
                if self.channels.has_key(ch_id):
                    ch = self.channels[ch_id]
                else:
                    ch = channel.Channel(key=ch_id)
                    ch.id = ch_id
                    ch.name = tokens[2]
                ch.in_epg = True
            elif line[0] == 'E':
                # event start
                ev = event.Event()
                ev.parseheader(line[2:])
                ev.source = 'vdr'
                ev.channel = ch
            elif line[0] == 'T':
                # title
                ev.title = line[2:]
            elif line[0] == 'S':
                # subtitle
                ev.subtitle = line[2:]
            elif line[0] == 'D':
                # description
                ev.desc = line[2:]
            elif line[0] == 'V':
                # description
                ev.vps = line[2:]
            elif line[0] == 'e':
                # event end
                ch.addevent(ev)
                ev = None
                counter = counter + 1
            elif line[0] == 'c':
                # channel end
                self.addchannel(ch)
                ch = None
            else:
                # unknown line identifier
                print 'Unable to parse line: ' + line
                break
            line = fh.readline()
        fh.close()
        return counter
    
    
    def retrieveepg(self, channelid=None, classifier=None):
        """Retrieves EPG data via SVDRP from VDR and adds it to this
        VDR object.
        
        The remote endpoint of the SVDRP connection used is
        identified by the host and port variables of this object.
        
        The return value is an integer containing the number of EPG
        events retrieved or None if an error occurred or no
        connection could be established.
        """
        counter = 0

        if self.getsvdrp() is None:
            return None

        cmd = 'lste'
        if channelid:
            cmd = cmd+' '+channelid

        if classifier:
            cmd = cmd+' '+classifier

        result = self.svdrp.write_cmd(cmd)
        fh = cStringIO.StringIO(result)
        return self.parseepg(fh)
    
    
    def readepg(self):
        """Reads EPG data from VDR's epg.data file and adds it to
        this VDR object.
        
        This function reads the file named by the epgfile variable.
        
        The return value is an integer containing the number of EPG
        events read.
        """
        fh = open(self.epgfile, 'r')
        return self.parseepg(fh)
    
    
    def updateepg(self, channels):
        """Transmit EPG data of this object to VDR.
        
        The channels argument is a list of Channel objects containing
        the Event objects to be added to VDR's EPG list.
        
        The return value is true if all EPG events were transmitted
        successfully, false else.
        """
        if self.getsvdrp() is None:
            return None
        return self.svdrp.pute(channels)
    
    
    def retrieverecordings(self):
        """Retrieves all available information about recordings from
        VDR via SVDRP and adds such Recording objects to this VDR
        object.
        
        The remote endpoint of the SVDRP connection used is
        identified by the host and port variables of this object.
        
        The return value is a list containing Recording objects or
        None if an error occurred or no connection could be
        established.
        """
        if self.getsvdrp() is None:
            return None
        result = self.svdrp.lstr()
        if result is not None:
            self.recordings = result
        return result
    
    
    def readrecordings(self):
        """Scans the  recordings directories for all available
        information about recordings and adds such Recording objects
        to this VDR object.
        
        The videopath variable of this object identifies the path(s)
        to be scanned.
        
        The return value is a list containing Recording objects or
        None if an error occurred.
        """
        self.recordings = []
        
        # what to do with every directory
        def visit(arg, dirname, names):
            if dirname[-4:] == '.rec':
                r = recording.Recording(dirname)
                arg.append(r)
        
        # recursively search all video paths
        for curpath in self.vpaths:
            os.path.walk(curpath, visit, self.recordings)
        
        # sort recordings by start time and set correct index
        self.recordings.sort()
        counter = 1
        for rec in self.recordings:
            rec.index = counter
            counter = counter + 1
        
        return self.recordings
    
    
    def retrievetimers(self):
        """Retrieves all available information about timers from
        VDR via SVDRP and adds such Timers objects to this VDR
        object.
        
        The remote endpoint of the SVDRP connection used is
        identified by the host and port variables of this object.
        
        The return value is a list containing Timer objects or
        None if an error occurred or no connection could be
        established.
        """
        if self.getsvdrp() is None:
            return None
        result = self.svdrp.lstt()
        if result is not None:
            self.timers = result
        return result
    
    
    def readtimers(self):
        """Reads VDR's timer file and adds the found Timer objects
        to this VDR object.
        
        The timerfile variable of this object identifies the file
        to be read.
        
        The return value is a list containing Timer objects or
        None if an error occurred.
        """
        self.timers = []
        
        try:
            index = 1
            fh = open(self.timerfile, 'r')
            line = fh.readline()
            while line:
                t = timer.Timer(line.strip(), index)
                if t.name is None:
                    print 'Could not parse line ' + str(index) + ' in file ' + self.timerfile + ': ' + line.strip()
                self.timers.append(t)
                line = fh.readline()
                index = index + 1
            fh.close()
        except IOError:
            return None
        
        return self.timers





