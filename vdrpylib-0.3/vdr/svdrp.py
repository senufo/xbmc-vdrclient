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

# import modules
import re
import string
import telnetlib
import time
from types import *

import channel
import recording
import timer

# SVDRP constants
SVDRP_PORT=2001
SVDRP_CMD_CHAN = 'chan'
SVDRP_CMD_CLRE = 'clre'
SVDRP_CMD_DELC = 'delc'
SVDRP_CMD_DELR = 'delr'
SVDRP_CMD_DELT = 'delt'
SVDRP_CMD_GRAB = 'grab'
SVDRP_CMD_HELP = 'help'
SVDRP_CMD_HITK = 'hitk'
SVDRP_CMD_LSTC = 'lstc'
SVDRP_CMD_LSTE = 'lste'
SVDRP_CMD_LSTR = 'lstr'
SVDRP_CMD_LSTT = 'lstt'
SVDRP_CMD_MESG = 'mesg'
SVDRP_CMD_MODC = 'modc'
SVDRP_CMD_MODT = 'modt'
SVDRP_CMD_MOVC = 'movc'
SVDRP_CMD_MOVT = 'movt'
SVDRP_CMD_NEWC = 'newc'
SVDRP_CMD_NEWT = 'newt'
SVDRP_CMD_NEXT = 'next'
SVDRP_CMD_PUTE = 'pute'
SVDRP_CMD_SCAN = 'scan'
SVDRP_CMD_STAT = 'stat'
SVDRP_CMD_UPDT = 'updt'
SVDRP_CMD_VOLU = 'volu'
SVDRP_CMD_QUIT = 'quit'


class SVDRP(telnetlib.Telnet):
    """A wrapper for VDR's SVDRP interface.
    
    An SVDRP object represents a telnet session to a VDR instance.
    SVDRP functionality is wrapped either at a text or at an object
    level where appropriate.
    
    Since the SVDRP class is derived from the telnetlib.Telnet class,
    the plain telnet interface may also be used to drive the
    protocol manually.

    close_connection makes SVDRP close the connection after each command
    because unfortunately the SVDRP interface only supports one open 
    connection (HELLO?!?!).
    """
    def __init__(self, host, port = SVDRP_PORT, close_connection = 1):
        self.host = host
        self.port = port
        self.close_connection = close_connection

        telnetlib.Telnet.__init__(self, self.host, self.port)
                #print 'RLS: after telnet init'

        if self.close_connection:
                    self.close()


    def open(self, host = None, port = SVDRP_PORT):
        """Connect to a host.
 
        The optional port argument is the port number to connect to.
        It defaults to the standard SVDRP port (2001).

        Don't try to reopen an already connected instance.
        """
        #print 'RLS: in open 1'
        if not host and not self.host:
            return

        if self.get_socket():
            return

        if host:
            #print 'RLS: in open 2'
            telnetlib.Telnet.open(self, host, port)
        else:
            #print 'RLS: in open 3'
            telnetlib.Telnet.open(self, self.host, self.port)

        #time.sleep(0.2)

        # consume all output
        result = ''
        while not result:
            #print 'RLS: reading very eager'
            result = self.read_very_eager()
            #print 'RLS: read'
        #print 'RLS: result="%s"' % result


    def close(self):
        try:
            self.write('quit\n')
        except:
            return
        
        self.read_all()
        telnetlib.Telnet.close(self)
        return 


    def read_reply(self):
        """Read a SVDRP-style reply.
        
        Reads input until a reply to an SVDRP command is found.
        
        The function returns a string containing the complete reply.
        
        The reply is expected to be delimited by a line starting with
        a 3-digit number followed by a blank, followed by arbitrary
        text and a terminating newline.
        """
        pat = re.compile('^\d\d\d ', re.M)
        reply = ''
        try:
            reply = self.read_some()
        except:
            # connection lost
            print "error 1 reading reply, connection lost"
            return reply
        x=reply[:-1].rfind('\n')
        if x==-1:
            x=0
        while not pat.search(reply[x:]):
            try:
                buffer = self.read_some()
                reply = reply + buffer
                x=reply[:-1].rfind('\n')
                if x==-1:
                    x=0
            except:
                # connection closed
                print "error 2 reading reply, connection lost"
                return reply
        reply+=self.read_very_eager()
        return reply


    def write_cmd(self, cmd, close = -1):
        """Send text to the server and return its reply.
        
        The cmd argument contains the string written to the
        underlying telnet object. It is made sure that the string
        ends in a newline character so that it is recognized as a
        command by VDR.
        
        The function returns a string containing VDR's reply.
        """
        if len(cmd) == 0:
            return ''
        
        self.open()

        if cmd[-1] != '\n':
            cmd = cmd + '\n'
        #print "cmd: #%s# " %(cmd)
        self.read_eager()
        self.write(cmd)
        #time.sleep(0.2)
        reply = self.read_reply()
        #print "X: "+reply

        if close > 0:
            self.close()
            #print 'RLS: want to close %d' % close
        elif close == -1 and self.close_connection:
            #print 'RLS: want to close %d' % close
            self.close()

        return reply

    
    def hitk(self, key):
        """Hit the given remote control key.
        
        The key argument is expected to be a string containing one
        of the key names understood by VDR.
        
        The return value is 0 if the command failed and 1 otherwise.
        """
        result = self.write_cmd('hitk ' + str(key) + '\n')
        if result[0:3] == '250':
            return 1
        else:
            print 'hitk returned: ' + result
            return 0


    def osd_message(self, msg):
        """
        """
        result = self.write_cmd('%s %s\n' % (SVDRP_CMD_MESG, msg))
        if result[0:3] == '250':
            return 1
        else:
            print '%s returned: %s' % (SVDRP_CMD_MESG, result)
            return 0
    

    def chan(self, chan, vdr = None):
        """Switch the current channel.
        
        The channel argument can be a Channel object or a string
        containing a channel name or index or being '+' or '-' for
        switching to the next or previous channel.
        
        The vdr argument is a VDR object from which fully qualified
        Channel object can be retrieved.
        
        The return value is a Channel object representing the
        current channel if a VDR object was supplied, else it is the
        string returned by VDR or None if the command failed.
        """
        if isinstance(chan, channel.Channel):
            result = self.write_cmd('chan ' + channel.name + '\n')
        # elif isinstance(chan, StringType) or isinstance(chan, IntType):
        else:
            result = self.write_cmd('chan %s\n' % chan)

        if result[0:3] == '250':
            if vdr:
                return vdr.getchannel(result.split(None, 2)[1])
            else:
                return result[3:]
        else:
            print 'chan returned: ' + result
            return None
    

    def current_chan(self):
        """
        Return the currently tuned channel.
        """
        result=self.write_cmd('chan\n')
        channel=""
        if result[0:3] == '250':
            try:
                channel=result.split(None, 2)[1]
            except:
                channel=""
            print "Current_chan="+channel
        else:
            print "result='"+result+"'"
        return channel


    def lstc(self, id = None):
        """List channel details.
        
        If the id argument is an integer the channel with that
        index is listed. If the argument is a string all channels
        containing that string as part of their name are listed.
        If the argument is None, all channels are listed.
        
        The return value is a list of Channel objects representing
        the listed channels. If the command failed, None is returned.
        """
        if id is None:
            result = self.write_cmd('lstc\n')
        else:
            result = self.write_cmd('lstc ' + str(id) + '\n')
        
        # check first line of output
        if result[0:3] != '250':
            print 'lstc returned: ' + result
            return None
        
        # create Channel objects from output
        channels = []
        counter = 1
        for line in result.split('\n'):
            if len(line) > 5:
                tokens = line.strip()[4:].split(None, 1)
                if len(tokens) > 1:
                    try:
                        c = channel.Channel(tokens[-1], counter)
                        c.in_conf = True
                        channels.append(c)
                        counter = counter + 1
                    except:
                        print "Error parsing channel "+line

        return channels


    def pute(self, channels):
        """Put data into the EPG list.
        
        The channels argument is a list of Channel objects containing
        the Event objects to be the EPG list.
        
        The return value is true if all EPG events were transmitted
        successfully, false else.
        """
        result = self.write_cmd('pute\n', close = 0)
        if result[0:3] != '354':
            print 'pute returned: ' + result
            return 0

        for ch in channels:
            self.write(ch.getepgstr())
        self.write('.\n')

        result = self.read_reply()
           
        if self.close_connection:
            self.close()

        if result[0:3] != '250':
            print 'pute returned: ' + result
            return 0
        
        return 1


    def lstr(self, index = None):
        """List VDR recordings.
        
        The optional index argument is expected to be an integer
        containing an index into the global list of recordings.
        
        If no index argument is given, the return value is a list of
        Recording objects. If an index is given, a string containing
        the summary for that recording is returned.
        If an error occurs, None is returned.
        """
        result = ''
        if index is None:
            result = self.write_cmd('lstr\n')
        else:
            result = self.write_cmd('lstr ' + str(index) + '\n')
            if result[0:3] == '550':
                return ''
            elif result[0:3] == '250':
                return result.strip()[4:]

        # check first line of output
        if result[0:3] != '250':
            print 'lstr returned: ' + result
            return None
        
        # create Recording objects from output
        recs = []
        for line in result.split('\n'):
            if len(line) > 5 and line[:3] == '250':
                r = recording.Recording(line)
                r.setsource(self)
                recs.append(r)
        
        return recs


    def lstt(self, index = None):
        """List VDR timers.
        
        The optional index argument is expected to be an integer
        containing an index into the global list of timers.
        
        If no index argument is given, the return value is a list of
        Timer objects. If an index is given, a Timer object
        representing the timer with the specified index is
        returned. If an error occurs, None is returned.
        """
        result = ''
        if index is None:
            result = self.write_cmd('lstt\n')
        else:
            result = self.write_cmd('lstt ' + str(index) + '\n')

        # check first line of output
        if result[0:3] != '250':
            print 'lstt returned: ' + result
            return None
        
        # create Recording objects from output
        timers = []
        for line in result.split('\n'):
            if len(line) > 5 and line[:3] == '250':
                t = timer.Timer(line)
                timers.append(t)
        
        return timers


        


