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
#python modules
import os, re
import pickle

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
        self.vdrpclient = SVDRPClient(VDR_HOST, VDR_PORT)
        client.send_command('lste 1')
  
    def onInit( self ):
        if DEBUG == True: print "Branch Master"

   
mydisplay = VDRWindow( "script-svdrpclient-main.xml" , __cwd__, "Default")
mydisplay.doModal()
del mydisplay
