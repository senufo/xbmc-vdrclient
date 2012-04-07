# -*- coding: utf-8 -*-
"""
Control VDR with xbmc
"""
#Modules xbmc
import xbmc, xbmcgui
import xbmcaddon
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


#vdr modules
import svdrp
import event
import channel
import timer

DEBUG = True
# VDR server
VDR_HOST = '127.0.0.1'
VDR_PORT = 6419
VDR_PORT = 2001
#Label SKIN XML

#ID des boutons dans .xml
STATUS_LABEL    = 100
CHAINE          = 101
DESC_BODY       = 102
TIMERS_LIST      = 120
QUIT            = 1004
TIMERS          = 1006

def decoupe(seconde):
    """
    Découpe les secondes en H,M,S
    """
    heure = seconde /3600
    seconde %= 3600
    minute = seconde/60
    seconde%=60
    return (heure,minute,seconde)

class EPGWindow(xbmcgui.WindowXML):
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
        locstr = __addon__.getLocalizedString(id=600) #Get EPG data
        Dialog.create(locstr)
        locstr = __addon__.getLocalizedString(id=601) #Please wait
        Dialog.update(0, locstr)
        #Variable pour la progression dans la boite de dialogue²
        up = 1
        self.getControl( 120 ).reset()

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
        NbEPG = 500
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
                try:
                    #(year,mois, mday, heure, min, sec) = time.gmtime(int(ev.start))
                    #Tient compte du fuseau horaire
                    if time.daylight != 0:
                        time_start = int(ev.start) - time.altzone
                    else:
                        time_start = int(ev.start)
                    time_start = time.gmtime(int(time_start))
                    stop = ev.start + ev.dur
                    time_stop = time.gmtime(int(stop))
                    #print "Start = %s, durée = %s, id = %s" % (ev.start,ev.dur,ev.id)a
                    print ('%02d:%02d - %02d:%02d => %s' %
                        (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                        ev.title))

                    epg_data = ('%02d:%02d - %02d:%02d : %s' %
                        (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                        ev.title))
    
                    listEPGItem = xbmcgui.ListItem( label=epg_data)
                    description = '%s\n====\n%s\n====\n%s' % (ev.title, ev.subtitle, ev.desc )
                    listEPGItem.setProperty( "description", description )
                    listEPGItem.setProperty( "date", time.strftime('%A, %d/%m/%Y',time_start))
                    self.getControl( 120 ).addItem( listEPGItem )
                    (ev.title, ev.subtitle, ev.desc ) = ('','','')
                except:
                    pass
            up2 = int((up*100)/NbEPG)
            #print "UP = %d " % up
            up += 1
            locstr = __addon__.getLocalizedString(id=601) #Please wait
            Dialog.update(up2, locstr)
        Dialog.close()       

        self.vdrpclient.close()
        self.getControl( CHAINE ).setLabel( '%s' % ch )
 
    def onClick( self, controlId ):
        #print "onClick controId = %d " % controlId
        if (controlId == 1200):
            label = self.getControl( controlId
                                   ).getSelectedItem().getProperty('serveur')
            self.getEPG(label)
        elif (controlId == TIMERS):
            label = self.getControl( FEEDS_LIST
                                   ).getSelectedItem().getProperty('description')
            print 'LABEL = %s ' % label

        elif (controlId == QUIT):
            self.close()

class TIMERSWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: print "__INIT__"

    def onInit( self ):
        actions = ['Programmes','Programmation','Enregistrements']
        if DEBUG == True: print "Init TIMERSWindow"
        timers = []
        client = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        client.send_command('lstt')
        for num, flag, message in client.read_response():
            print message
            ti = timer.Timer(message)
            print "index = %s, name = %s " % (ti.index, ti.name)
            print 'summary = %s, channel = %s ' % (ti.summary, ti.channel)
            print 'start = %s, stop = %s'  % (ti.start, ti.stop)
            print 'recu = %s, prio = %s' % (ti.recurrence, ti.prio)
            print 'lt = %s, act= %s ' % (ti.lifetime, ti.active)
            print ti.vdr
            timers.append(ti)
        client.close()

        self.getControl( TIMERS_LIST ).reset()

        for prog in timers:
            print "TIMERS => %s " % str(prog.name)
            (heure,minute,sec) = decoupe(prog.start)
            h_start = '%02d:%02d' % (heure,minute)
            (heure,minute,sec) = decoupe(prog.stop)
            h_stop = '%02d:%02d' % (heure,minute)

            listTimers = xbmcgui.ListItem(label=prog.name,
                                          label2='%s - %s' % (h_start,h_stop))
            listTimers.setProperty( "action", prog.name )
 
            self.getControl( TIMERS_LIST ).addItem( listTimers )


class VDRWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: print "__INIT__"

    def onInit( self ):
        actions = ['Programmes','Programmation','Enregistrements']
        if DEBUG == True: print "Init VDRWindow"
        #self.getControl( 1200 ).reset()
        #for action in actions:
        #    listAction = xbmcgui.ListItem(label=action)
        #    listAction.setProperty( "action", action )
        #    self.getControl( 1200 ).addItem( listAction )

    def onClick( self, controlId ):
        print "onClick controId = %d " % controlId
        if (controlId == 1001):
            epgWIN = EPGWindow( "epgWIN.xml" , __cwd__, "Default")
            epgWIN.doModal()
        elif (controlId == 1002):
            timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
            timersWIN.doModal()
            del timersWIN

#        if (controlId == 1200):
 #           print "onClick controId = %d " % controlId
 #           label = self.getControl( controlId
 #                                  ).getSelectedItem().getProperty('action')
 #           print 'LABEL = %s ' % label
 #           if label == 'Programmes':
 #               epgWIN = EPGWindow( "epgWIN.xml" , __cwd__, "Default")
 #               epgWIN.doModal()
 #               del epgWIN
 #           elif label == 'Programmation':
 #               timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
 #               timersWIN.doModal()
 #              del timersWIN

        elif (controlId == QUIT):
            self.close()

#mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__, "Default")
mydisplay = VDRWindow( "script-Actors-ContextMenu.xml" , __cwd__, "Default")
mydisplay.doModal()
del mydisplay
