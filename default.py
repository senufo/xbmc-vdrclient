# -*- coding: utf-8 -*-
"""
iControl VDR with xbmc
"""
#Modules xbmc
import xbmc, xbmcgui
import xbmcaddon
#vdr modules
import svdrp
import event
import channel

#python modules
import os, re
import pickle
import sys

__author__     = "Senufo"
__scriptid__   = "script.svdrpclient"
__scriptname__ = "isvdrpclient"

__addon__      = xbmcaddon.Addon(id=__scriptid__)

__cwd__        = __addon__.getAddonInfo('path')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') )
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources',
                                                  'lib' ) )
sys.path.append (__resource__)

DEBUG = False
# VDR server
VDR_HOST = '127.0.0.1'
VDR_PORT = 6419
VDR_PORT = 2001


class VDRWindow(xbmcgui.WindowXML):
    """
    Window for VDR commands
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: print "__INIT__"
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lstc')
        self.channels = []
        for num, flag, message in self.vdrpclient.read_response(): 
            ch = channel.Channel(message)
            self.channels.append(ch)
        self.vdrpclient.close() 
        for ch in self.channels:
            print "CHinit = %s " % ch
        
    def onInit( self ):
        if DEBUG == True: print "Branch Master"
        for ch in self.channels:
            print "CH = %s " % ch
            listChannel = xbmcgui.ListItem(label=ch.name_tok)
            listChannel.setProperty( "description", 'desc' )
            listChannel.setProperty( "img" , 'img' )
            listChannel.setProperty( "date" , 'date')
            listChannel.setProperty( "video" , 'video' )
 
            listChannel.setProperty("serveur", ch.name_tok )
            self.getControl( 1200 ).addItem( listChannel )
   
mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__, "Default")
mydisplay.doModal()
del mydisplay
