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
import time

__author__     = "Senufo"
__scriptid__   = "script.svdrpclient"
__scriptname__ = "svdrpclient"

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
#Label SKIN XML

CHAINE = 101

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
##        for ch in self.channels:
#            print "CHinit = %s " % ch
        
    def onInit( self ):
        if DEBUG == True: print "Branch Master"
        for ch in self.channels:
            listChannel = xbmcgui.ListItem(label=ch.name_tok)
            listChannel.setProperty( "description", 'desc' )
            listChannel.setProperty( "img" , 'img' )
            listChannel.setProperty( "date" , 'date')
            listChannel.setProperty( "video" , 'video' )
 
            listChannel.setProperty("serveur", ch.name_tok )
            self.getControl( 1200 ).addItem( listChannel )

    def getEPG(self, ch):
        #print 'CH EPG = %s ' % ch
        Dialog = xbmcgui.DialogProgress()
        #    locstr = __addon__.getLocalizedString(id=600) #Get News
        Dialog.create('Please Wait')
        #locstr = __addon__.getLocalizedString(id=601) #Please wait
        Dialog.update(0, 'update')
        #Variable pour la progression dans la boite de dialogue²
        up = 1

        for c_name in self.channels:
            #print "CHinit = %s " % ch
            if c_name.name_tok == ch:
                print "No = %s, c_name.name_tok = %s" % (c_name.no,c_name.name_tok)
                c_no = c_name.no
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lste %s' % c_no)
        Titre, SousTitre, Description = ('','','')
        ev = event.Event()
        #nbEPG = len(self.vdrpclient.read_response())
        NbEPG = 100
        for num, flag, message in self.vdrpclient.read_response():
            print "MESSAGE = %s " % message
            if message[0] == 'T':
                ev.title = message[2:]
            elif message[0] == 'S':
                ev.subtitle= message[2:]
            elif message[0] == 'D':
                Description  = message[2:]
                ev.desc = Description.replace('|','\n')
            elif message[0] == 'E' and message != 'End of EPG data':
                # event start
                ev.parseheader(message[2:])
                ev.source = 'vdr'
                print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)
                #START = Wed Apr 11 01:10:00 2012
                #time.struct_time(tm_year=2012, tm_mon=4, tm_mday=10, tm_hour=23, tm_min=10, tm_sec=0, tm_wday=1, tm_yday=101, tm_isdst=0) 
                print 'getitme = %s ' % time.gmtime(int(ev.start))

            if message[0] == 'e':
                #(year,mois, mday, heure, min, sec) = time.gmtime(int(ev.start))
                time_start = time.gmtime(int(ev.start))
                stop = ev.start + ev.dur
                time_stop = time.gmtime(int(stop))
                #print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)a
                print ('%02d:%02d - %02d:%02di => %s' %
                    (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                    ev.title))
                epg_data = ('%02d:%02d - %02d:%02d : %s' %
                    (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                    ev.title))

                listEPGItem = xbmcgui.ListItem( label=epg_data)
                listEPGItem.setProperty( "description", ev.desc )
                listEPGItem.setProperty( "date", time.strftime('%A, %d/%m/%Y',time_start))
                self.getControl( 120 ).addItem( listEPGItem )
                Titre, SousTitre, Description = ('','','')
            up2 = int((up*100)/NbEPG)
            #print "UP = %d " % up
            up += 1
            Dialog.update(up2, 'Get EPG', 'Please wait')
        Dialog.close()       

        self.vdrpclient.close()

 
    def onClick( self, controlId ):
        #print "onClick controId = %d " % controlId
        if (controlId == 1200):
            label = self.getControl( controlId
                                   ).getSelectedItem().getProperty('serveur')
            self.getEPG(label)
        elif (controlId == VIDEO):
            label = self.getControl( FEEDS_LIST
                                   ).getSelectedItem().getProperty('video')

        elif (controlId == QUIT):
            self.close()

  
mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__, "Default")
mydisplay.doModal()
del mydisplay
