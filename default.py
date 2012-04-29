# -*- coding: utf-8 -*-
"""
Control VDR with xbmc
"""
#Modules xbmc
import xbmc, xbmcgui
import xbmcaddon
#python modules
import os
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
CHAINE_EPG      = 101
DESC_BODY       = 102
EPG_LIST     = 120
CHANNELS_LIST   = 1200
QUIT            = 1004
TIMERS          = 1006
#ID des champs dans timersWIN.xml
ACTIF       = 201
CHAINE      = 202
JOUR        = 203
DEBUT       = 204
FIN         = 205

ch = False

def decoupe(seconde):
    """
    Découpe les secondes en H,M,S
    """
    heure = seconde /3600
    seconde %= 3600
    minute = seconde/60
    seconde %= 60
    return (heure, minute, seconde)

class EPGWindow(xbmcgui.WindowXML):
    """
    Window for VDR commands
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: 
            print "__INIT__"
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
        """
        Init Class EPGWIndow
        """
        if DEBUG == True: 
            print "Branch Master"
        for ch in self.channels:
            listChannel = xbmcgui.ListItem(label=ch.name_tok)
            listChannel.setProperty( "description", 'desc' )
            listChannel.setProperty( "img" , 'img' )
            listChannel.setProperty( "date" , 'date')
            listChannel.setProperty( "video" , 'video' )
 
            listChannel.setProperty("serveur", ch.name_tok )
            self.getControl( CHANNELS_LIST ).addItem( listChannel )

    def getEPG(self, ch):
        """
        Recupere l'EPG sur VDR
        """
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
                #print "No = %s, c_name.name_tok = %s" % (c_name.no, c_name.name_tok)
                c_no = c_name.no
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lste %s' % c_no)
        Titre, SousTitre, Description = ('', '', '')
        ev = event.Event()
        #nbEPG = len(self.vdrpclient.read_response())
        NbEPG = 500
        for num, flag, message in self.vdrpclient.read_response():
            #print "MESSAGE = %s " % message
            if message[0] == 'T':
                ev.title = message[2:]
            elif message[0] == 'S':
                ev.subtitle = message[2:]
            elif message[0] == 'D':
                Description  = message[2:]
                ev.desc = Description.replace('|','\n')
            elif message[0] == 'E' and message != 'End of EPG data':
                # event start
                ev.parseheader(message[2:])
                ev.source = 'vdr'
                #print "Start = %s, durée = %s, id = %s" % (ev.start, ev.dur, ev.id)
                #START = Wed Apr 11 01:10:00 2012
                #time.struct_time(tm_year=2012, tm_mon=4, tm_mday=10, tm_hour=23, tm_min=10, tm_sec=0, tm_wday=1, tm_yday=101, tm_isdst=0) 
                #print 'getitme = %s ' % time.gmtime(int(ev.start))
            #print "Mxx[0] = %s " % message[0]
            if message[0] == 'e':
                #print 'Messge = %s' % message
                try:
                #if 1:
                    #(year,mois, mday, heure, min, sec) = time.gmtime(int(ev.start))
                    #Tient compte du fuseau horaire
                    if time.daylight != 0:
                        time_start = int(ev.start) - time.altzone
                    else:
                        time_start = int(ev.start)
                    stop = time_start + ev.dur
                    time_start = time.gmtime(int(time_start))
                    #stop = ev.start + ev.dur
                    time_stop = time.gmtime(int(stop))
                    #print "Start = %s, durée = %s, id = %s" % (ev.start, ev.dur, ev.id)
                    #print ('%02d:%02d - %02d:%02d => %s' %
                    #    (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                    #    ev.title))

                    epg_data = ('%02d:%02d - %02d:%02d : %s' %
                        (time_start.tm_hour,time_start.tm_min,time_stop.tm_hour,time_stop.tm_min,
                        ev.title))
    
                    listEPGItem = xbmcgui.ListItem( label=epg_data)
                    description = '%s\n====\n%s\n====\n%s' % (ev.title, ev.subtitle, ev.desc )
                    listEPGItem.setProperty( "description", description )
                    listEPGItem.setProperty( "date", time.strftime('%A, %d/%m/%Y', time_start))
                    #Properties pour les timers
                    #  status:channel:day    :start:stop:priority:lifetime:filename:
                    #1 0     :      3:MT-TF--: 0644:0902:      50:      30:    Ludo:
                    listEPGItem.setProperty( "channel", ch)
                    listEPGItem.setProperty( "no_ch", c_no)
                    listEPGItem.setProperty( "day", time.strftime('%Y-%m-%d', time_start))
                    listEPGItem.setProperty( "start", '%02d%02d' %
                                            (time_start.tm_hour,time_start.tm_min))
                    listEPGItem.setProperty( "stop", '%02d%02d' %
                                            (time_stop.tm_hour,time_stop.tm_min))
                    listEPGItem.setProperty( "priority", '50')
                    listEPGItem.setProperty( "lifetime", '30')
                    listEPGItem.setProperty( "filename", ev.title)

                    self.getControl( 120 ).addItem( listEPGItem )
                    (ev.title, ev.subtitle, ev.desc ) = ('', '', '')
                except:
                    print "Unexpected error:", sys.exc_info()[0] 
                    #pass
            up2 = int((up*100)/NbEPG)
            #print "UP = %d " % up
            up += 1
            locstr = __addon__.getLocalizedString(id=601) #Please wait
            Dialog.update(up2, locstr)
        Dialog.close()       

        self.vdrpclient.close()
        self.getControl( CHAINE_EPG ).setLabel( '%s' % ch )

    def selectTimer(self):
        """
        Ecrit un nouveau timer
        """
        epg_channel = self.getControl( EPG_LIST
                                   ).getSelectedItem().getProperty('channel')
        epg_no_ch = self.getControl( EPG_LIST
                                    ).getSelectedItem().getProperty('no_ch')
        epg_day = self.getControl( EPG_LIST
                                  ).getSelectedItem().getProperty('day')
        epg_start = self.getControl( EPG_LIST 
                                     ).getSelectedItem().getProperty('start')
        epg_stop = self.getControl( EPG_LIST 
                                     ).getSelectedItem().getProperty('stop')
        epg_priority = self.getControl( EPG_LIST 
                                     ).getSelectedItem().getProperty('priority')
        epg_lifetime = self.getControl( EPG_LIST 
                                     ).getSelectedItem().getProperty('lifetime')
        epg_filename = self.getControl( EPG_LIST 
                                     ).getSelectedItem().getProperty('filename')

        print """
        EPG ch = %s, day = %s, start = %s , stop = %s, prio = %s , lt =
        %s, filename = %s
        """ % (epg_channel, epg_day, epg_start, epg_stop, epg_priority,
               epg_lifetime, epg_filename)
        #Stocke les infos dans la classe Timer
        ti = timer.Timer()
        ti.index = 0
        ti.name = epg_filename
        ti.summary = ''
        ti.channel = epg_no_ch
        ti.start = epg_start
        ti.stop = epg_stop
        ti.recurrence = ''
        ti.prio = epg_priority
        ti.lifetime = epg_lifetime
        ti.active = ''
        ti.day = epg_day
        #On passe les valeurs du timer
        write_timerWIN = EDITimerWindow( "timersWIN.xml" , __cwd__,
                                      "Default",writetimer=True, timer=ti)
        write_timerWIN.doModal()

    def onClick( self, controlId ):
        """
        Action lorsque on clique sur un bouton
        """
        print "onClick controId = %d " % controlId
        if (controlId == CHANNELS_LIST):
            label = self.getControl( controlId
                                   ).getSelectedItem().getProperty('serveur')
            self.getEPG(label)
        elif (controlId == EPG_LIST):
            self.selectTimer()
        elif (controlId == TIMERS):
            label = self.getControl( FEEDS_LIST
                                   ).getSelectedItem().getProperty('description')
            print 'LABEL = %s ' % label

        elif (controlId == QUIT):
            self.close()

class EDITimerWindow(xbmcgui.WindowXML):
    """
    Window for EDITimer window
    """
 
    def __init__(self, *args, **kwargs):
        if DEBUG == True: 
            print "__INIT__ TIMERSWindow"
            #writetimer = True si on ecrit un timer
            self.write = kwargs.get('writetimer')
            self.myTimer = kwargs.get('timer')
            print "ARGS = " + repr(args) + " - " + repr(kwargs)
            print "WriteTimer = %s " % self.write
  
    def onInit( self ):
        """
        Initialisation de la classe EDITIMERWindow
        """
        if DEBUG == True:
            print 'INIT EDITimerWindow'
        if self.write:
            self.writeTimer()
 
    def writeTimer(self):
        """
        Ecrit le timer
        """
        print "TIMER = %s " % self.myTimer.channel
        #Properties pour les timers
        #  status:channel:day    :start:stop:priority:lifetime:filename:
        #1 0     :      3:MT-TF--: 0644:0902:      50:      30:    Ludo:
        cmd_svdrp = "1:%s:%s:%s:%s:%s:%s:%s:" % (self.myTimer.channel,
                                           self.myTimer.day,
                                           self.myTimer.start,
                                           self.myTimer.stop,
                                           self.myTimer.prio,
                                           self.myTimer.lifetime,
                                           self.myTimer.name)
        print "cmd_svdrp = %s " % cmd_svdrp
        #svdrp write timer command (newt)
        vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        vdrpclient.send_command('newt %s' % cmd_svdrp)
        vdrpclient.close()
        #On ajoute les timers dans la listbox
        listTimers = xbmcgui.ListItem(label='%s : %s | %s - %s' %
                                      (self.myTimer.channel, self.myTimer.day,
                                       self.myTimer.start, self.myTimer.stop),
                                      label2=self.myTimer.name)
        #On rempli les différents champs du skin
        listTimers.setProperty( "channel", str(self.myTimer.channel) )
        listTimers.setProperty( "start", self.myTimer.start )
        listTimers.setProperty( "stop", self.myTimer.stop )
        listTimers.setProperty( "day", self.myTimer.day )
        listTimers.setProperty( "active", '1')
 
        self.getControl( EPG_LIST ).addItem( listTimers )

class TIMERSWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: 
            print "__INIT__ TIMERSWindow"
            #writetimer = True si on ecrit un timer
            self.write = kwargs.get('writetimer')
            self.myTimer = kwargs.get('timer')
            print "ARGS = " + repr(args) + " - " + repr(kwargs)
            print "WriteTimer = %s " % self.write

    def onInit( self ):
        """
        Initialisation de la classe TIMERSWindow
        """
        actions = ['Programmes', 'Programmation', 'Enregistrements']
        if DEBUG == True: 
            print "Init TIMERSWindow"
        #writetimer = True on écrit un timer sinon on liste ceux qui existent
        if self.write:
            self.writeTimer()
        else:
            self.listTimers()
    
    def writeTimer(self):
        """
        Ecrit le timer
        """
        print "TIMER = %s " % self.myTimer.channel
        #Properties pour les timers
        #  status:channel:day    :start:stop:priority:lifetime:filename:
        #1 0     :      3:MT-TF--: 0644:0902:      50:      30:    Ludo:
        cmd_svdrp = "1:%s:%s:%s:%s:%s:%s:%s:" % (self.myTimer.channel,
                                           self.myTimer.day,
                                           self.myTimer.start,
                                           self.myTimer.stop,
                                           self.myTimer.prio,
                                           self.myTimer.lifetime,
                                           self.myTimer.name)
        print "cmd_svdrp = %s " % cmd_svdrp
        #svdrp write timer command (newt)
        vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        vdrpclient.send_command('newt %s' % cmd_svdrp)
        vdrpclient.close()
        #On ajoute les timers dans la listbox
        listTimers = xbmcgui.ListItem(label='%s : %s | %s - %s' %
                                      (self.myTimer.channel, self.myTimer.day,
                                       self.myTimer.start, self.myTimer.stop),
                                      label2=self.myTimer.name)
        #On rempli les différents champs du skin
        listTimers.setProperty( "channel", str(self.myTimer.channel) )
        listTimers.setProperty( "start", self.myTimer.start )
        listTimers.setProperty( "stop", self.myTimer.stop )
        listTimers.setProperty( "day", self.myTimer.day )
        listTimers.setProperty( "active", '1')
 
        self.getControl( EPG_LIST ).addItem( listTimers )

    def listTimers(self):
        """
        Liste les timers de VDR et les affiche
        """
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lstc')
        self.channels = []
        for num, flag, message in self.vdrpclient.read_response(): 
            ch = channel.Channel(message)
            self.channels.append(ch)
        self.vdrpclient.close()
        
        #Tableau qui va contenir tout les timers
        timers = []
        client = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        #Envoi le cmd pour lister les timers
        client.send_command('lstt')
        for num, flag, message in client.read_response():
            print message
            #Stocke les infos dans la classe Timer
            ti = timer.Timer(message)
            print "index = %s, name = %s " % (ti.index, ti.name)
            print 'summary = %s, channel = %s ' % (ti.summary, ti.channel)
            print 'start = %s, stop = %s'  % (ti.start, ti.stop)
            print 'recu = %s, prio = %s' % (ti.recurrence, ti.prio)
            print 'lt = %s, act= %s ' % (ti.lifetime, ti.active)
            print 'day = %s' % ti.day
            print ti.vdr
            timers.append(ti)
        client.close()

        self.getControl( EPG_LIST ).reset()
        #On parcours les timers
        #pour les mettre dans la listbox
        for prog in timers:
            print "TIMERS => %s " % str(prog.name)
            (heure, minute, sec) = decoupe(prog.start)
            h_start = '%02d:%02d' % (heure, minute)
            (heure, minute, sec) = decoupe(prog.stop)
            h_stop = '%02d:%02d' % (heure, minute)
            #On recupere le nom de la chaine en fct de son numéro
            for c_name in self.channels:
                print "NO = -%d-, CH = -%d- " %  (int(c_name.no), int(prog.channel))
                if int(c_name.no) == int(prog.channel):
                    print "No = %s, c_name=>.name_tok = %s" % (c_name.no, c_name.name_tok)
                    prog.channel = c_name.name_tok
                    break
            #Dans VDR il y a deux manière de stocker le jour
            #2012-04-24
            #MTWFSS pour les programmations récurrentes
            days = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
            if not prog.day:
                i = 0
                prog.day = ''
                for x in prog.recurrence:
                    if x:
                        prog.day = str(prog.day) + days[i]
                    else:
                        prog.day = prog.day + '-'
                    i += 1
            #On ajoute les timers dans la listbox
            #listTimers = xbmcgui.ListItem(label='%2s| %10s | %10s | %5s - %5s' %
            #                              (str(prog.active),prog.channel, 
            #                               prog.day, h_start,h_stop),
            #                              label2=prog.name)
            listTimers = xbmcgui.ListItem(label='%10s' %
                                          prog.channel, 
                                          label2=prog.name)
           #On rempli les différents champs du skin
            listTimers.setProperty( "channel", str(prog.channel) )
            listTimers.setProperty( "start", h_start )
            listTimers.setProperty( "stop", h_stop )
            listTimers.setProperty( "day", str(prog.day) )
            listTimers.setProperty( "active", str(prog.active))
 
            self.getControl( EPG_LIST ).addItem( listTimers )

    #def onFocus( self, controlId ):
    #    """
    #    actions lorsque on clique sur un bouton du skin
    #    """
    #    print "onFocus controId = %d " % controlId

    #def onAction(self, action):
    #    print "ID Action %d" % action.getId()
    #    print "Code Action %d" % action.getButtonCode()
            
    def onClick( self, controlId ):
        """
        actions lorsque on clique sur un bouton du skin
        """
        print "onClick controId = %d " % controlId
        if (controlId == ACTIF):
            print "ControID = ACTIF"
        elif (controlId == CHAINE):
            print "ControID = CHAINE"
            text = self.getControl( CHAINE ).getLabel()
            print '==> text = %s ' % text
            kb = xbmc.Keyboard('default', 'heading', True)
            kb.setHeading('Entrer le nom de la chaîne') # optional
            kb.setDefault(text) # optional
            kb.setHiddenInput(False)
            kb.doModal()
            if (kb.isConfirmed()):
                text = kb.getText()
                self.getControl( CHAINE ).setLabel(text)
        elif (controlId == JOUR):
            print "ControID = JOUR"
        elif (controlId == DEBUT):
            print "ControID = DEBUT"
        elif (controlId == FIN):
            print "ControID = FIN"
        elif (controlId == QUIT):
            print "ControID = QUIT"
            self.close()




class VDRWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def __init__(self, *args, **kwargs):
        if DEBUG == True: 
            print "__INIT__"

    def onInit( self ):
        actions = ['Programmes','Programmation','Enregistrements']
        if DEBUG == True: 
            print "Init VDRWindow"
        #self.getControl( 1200 ).reset()
        #for action in actions:
        #    listAction = xbmcgui.ListItem(label=action)
        #    listAction.setProperty( "action", action )
        #    self.getControl( 1200 ).addItem( listAction )

    def onClick( self, controlId ):
        """
        Actions when mouse click on control
        """
        print "onClick controId = %d " % controlId
        if (controlId == 1001):
            epgWIN = EPGWindow( "epgWIN.xml" , __cwd__, "Default")
            epgWIN.doModal()
        elif (controlId == 1002):
            timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
            timersWIN.doModal()
            del timersWIN
        #elif (controlId == 1003):
        #    timersWIN = xbmcgui.WindowXML( "fixed.xml" , __cwd__, "Default")
            #timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
        #    timersWIN.doModal()
        #    del timersWIN

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

mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__, "Default")
mydisplay.doModal()
del mydisplay
