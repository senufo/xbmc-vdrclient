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

DEBUG_LOG = __addon__.getSetting( 'debug' )
if 'true' in DEBUG_LOG : DEBUG_LOG = True
else: DEBUG_LOG = False
#DEBUG_LOG = True

#Function Debug
def debug(msg):
    """
    print message if DEBUG_LOG == True
    """
    if DEBUG_LOG == True: print " [%s] : %s " % (__scriptname__, msg)

#vdr modules
import svdrp
import event
import channel
import timer

# VDR server
VDR_HOST = __addon__.getSetting('host1')
#VDR_HOST = '127.0.0.1'
#VDR_PORT = 6419
#VDR_PORT = 2001
VDR_PORT = __addon__.getSetting('port1')
#Label SKIN XML

#ID des boutons dans .xml
STATUS_LABEL    = 100
CHAINE_EPG      = 101
DESC_BODY       = 102
EPG_LIST        = 120
CHANNELS_LIST   = 1200
QUIT            = 1004
TIMERS          = 1006
#ID des champs dans timersWIN.xml
ACTIF       = 201
CHAINE      = 202
JOUR        = 203
DEBUT       = 204
FIN         = 205
#Boutons de timersWIN.xml
ON          = 2001
NEW         = 2002
DEL         = 2003
INFO        = 2004
EDIT        = 2005

#ID des champs dans EditimerWIN.xml
PRIORITY    = 206
LIFETIME    = 207
CHILDLOCK   = 208
TITLE       = 209
#Boutons de editimerWIN.xml
CANCEL      = 2001
ECRIRE      = 2002

#ch = False


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
        debug( "__INIT__")
        #Recupere la liste des chaines
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lstc')
        self.channels = []
        for num, flag, message in self.vdrpclient.read_response(): 
            ch = channel.Channel(message)
            self.channels.append(ch)
        self.vdrpclient.close() 
        
    def onInit( self ):
        """
        Init Class EPGWIndow
        """
        debug ( "Branch Master")
        for ch in self.channels:
            #Affiche le numero et le nom de la chaine
            listChannel = xbmcgui.ListItem(label=ch.no, label2=ch.name_tok)
            listChannel.setProperty('channel_name', ch.name_tok )
            listChannel.setProperty('channel_no', ch.no )
            self.getControl( CHANNELS_LIST ).addItem( listChannel )

    def getEPG(self, ch_name, ch_no):
        """
        Get EPG in  VDR server
        ch_name = channel name
        ch_no = channel's number in VDR
        """
        Dialog = xbmcgui.DialogProgress()
        locstr = __addon__.getLocalizedString(id=600) #Get EPG data
        Dialog.create(locstr)
        locstr = __addon__.getLocalizedString(id=601) #Please wait
        Dialog.update(0, locstr)
        #Variable pour la progression dans la boite de dialogue
        up = 1
        #On remet à zéro la liste des epg
        self.getControl( EPG_LIST ).reset()

        #for c_name in self.channels:
            #Cherche le numéro de la chaine en fct du nom
        #    if c_name.name_tok == ch:
        #        c_no = c_name.no
        #Liste les prog de la chaine c_no
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('lste %s' % ch_no)
        Titre, SousTitre, Description = ('', '', '')
        ev = event.Event()
        #nbEPG = len(self.vdrpclient.read_response())
        NbEPG = 500
        for num, flag, message in self.vdrpclient.read_response():
            #print "MESSAGE = %s " % message
            #Parse l'EPG renvoyé par VDR
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
            if message[0] == 'e':
                #debug ( 'Messge = %s' % message)
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
                    #Debut, Fin et Nom de l'EPG
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
                    listEPGItem.setProperty( "channel", ch_name)
                    listEPGItem.setProperty( "no_ch", ch_no)
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
        self.getControl( CHAINE_EPG ).setLabel( '%s' % ch_name )

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
        #On passe les valeurs du timer a la classe editimer
        try:
            write_timerWIN = EDITimerWindow( "editimersWIN.xml" , __cwd__,
                                      'aeon.nox.svn',writetimer=True, timer=ti,
                                        channel_name=epg_channel)
        except:
            write_timerWIN = EDITimerWindow( "editimersWIN.xml" , __cwd__,
                                      "Default",writetimer=True, timer=ti,
                                        channel_name=epg_channel)
        write_timerWIN.doModal()
        del write_timerWIN

    def onClick( self, controlId ):
        """
        Action lorsque on clique sur un bouton window timer
        """
        debug ( "onClick controId = %d " % controlId)
        #Clic sur un nom de chaine
        if (controlId == CHANNELS_LIST):
            channel_name = self.getControl( controlId
                                   ).getSelectedItem().getProperty('channel_name')
            channel_no = self.getControl( controlId
                                   ).getSelectedItem().getProperty('channel_no')
            self.getEPG(channel_name, channel_no)
        #Clic sur un event epg
        elif (controlId == EPG_LIST):
            self.selectTimer()
#        elif (controlId == TIMERS):
#            label = self.getControl( FEEDS_LIST
#                                   ).getSelectedItem().getProperty('description')
#            print 'LABEL = %s ' % label
        #Clic pour quitter
        elif (controlId == QUIT):
            self.close()

class EDITimerWindow(xbmcgui.WindowXML):
    """
    Window for EDITimer window
    """
 
    def __init__(self, *args, **kwargs):
        debug ( "__INIT__ EDITIMERWindow")
        #writetimer = True si on ecrit un timer
        self.write = kwargs.get('writetimer')
        self.myTimer = kwargs.get('timer')
        self.channel_name = kwargs.get('channel_name')
        debug ( "ARGS = " + repr(args) + " - " + repr(kwargs))
        debug ( "WriteTimer = %s " % self.write)
  
    def onInit( self ):
        """
        Initialisation de la classe EDITIMERWindow
        """
        debug ( 'INIT EDITimerWindow')
        if self.write:
            self.displayTimer()

    def displayTimer(self): 
        """
        Display timer info before write in VDR
        """
        #On ajoute le timer dans la listbox
        listTimers = xbmcgui.ListItem(label='%s' %
                                      self.channel_name,   #Utilise le nom de la chaine plutot que son numéro
                                      label2=self.myTimer.name)
        #On rempli les différents champs du skin
        listTimers.setProperty( "channel", str(self.myTimer.channel) )
        listTimers.setProperty( "start", self.myTimer.start )
        listTimers.setProperty( "stop", self.myTimer.stop )
        listTimers.setProperty( "day", self.myTimer.day )
        listTimers.setProperty( "active", '1')
        listTimers.setProperty( "priority", self.myTimer.prio)
        listTimers.setProperty( "lifetime", self.myTimer.lifetime)
        listTimers.setProperty( "childlock", 'no used')
        listTimers.setProperty( "title", self.myTimer.name)
 
        self.getControl( EPG_LIST ).addItem( listTimers )

    def writeTimer(self):
        """
        Ecrit le timer
        """
        debug ( "TIMER = %s " % self.myTimer.channel)
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
        debug ( "cmd_svdrp = %s " % cmd_svdrp)
        #svdrp write timer command (newt)
        vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        vdrpclient.send_command('newt %s' % cmd_svdrp)
        vdrpclient.close()

    def onClick( self, controlId ):
        """
        actions lorsque on clique sur un bouton du skin EditimerWin
        """
        debug ( "onClick Editimer = %d " % controlId)
        if (controlId == CANCEL):
            self.close()
        elif (controlId == ECRIRE):
            self.writeTimer()
            self.close()
        elif (controlId == ACTIF):
            debug ( "ControID = ACTIF")
        elif (controlId == CHAINE):
            debug ( "ControID = CHAINE")
            text = self.getControl( CHAINE ).getLabel()
            debug ( '==> text = %s ' % text)
            kb = xbmc.Keyboard('default', 'heading', True)
            kb.setHeading('Entrer le nom de la chaîne') # optional
            kb.setDefault(text) # optional
            kb.setHiddenInput(False)
            kb.doModal()
            if (kb.isConfirmed()):
                text = kb.getText()
                self.getControl( CHAINE ).setLabel(text)
        elif (controlId == JOUR):
            debug ( "ControID = JOUR")
        elif (controlId == DEBUT):
            debug ( "ControID = DEBUT")
        elif (controlId == FIN):
            debug ( "ControID = FIN")
        elif (controlId == QUIT):
            debug ( "ControID = QUIT")
            self.close()

class TIMERSWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def __init__(self, *args, **kwargs):
        debug ( "__INIT__ TIMERSWindow")
        #writetimer = True si on ecrit un timer
        self.write = kwargs.get('writetimer')
        self.myTimer = kwargs.get('timer')
        debug ( "ARGS = " + repr(args) + " - " + repr(kwargs))
        debug ( "WriteTimer = %s " % self.write)

    def onInit( self ):
        """
        Initialisation de la classe TIMERSWindow
        """
        #actions = ['Programmes', 'Programmation', 'Enregistrements']
        debug ( "Init TIMERSWindow")
        #writetimer = True on écrit un timer sinon on liste ceux qui existent
        if self.write:
            self.writeTimer()
        else:
            self.listTimers()
    
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
            debug ( message)
            #Stocke les infos dans la classe Timer
            ti = timer.Timer(message)
            debug ( "num = %s, index = %s, name = %s " % (num, ti.index,
                                                          ti.name))
            debug ( 'summary = %s, channel = %s ' % (ti.summary, ti.channel))
            debug ( 'start = %s, stop = %s'  % (ti.start, ti.stop))
            debug ( 'recu = %s, prio = %s' % (ti.recurrence, ti.prio))
            debug ( 'lt = %s, act= %s ' % (ti.lifetime, ti.active))
            debug ( 'day = %s' % ti.day)
            debug ( ti.vdr)
            timers.append(ti)
        client.close()

        self.getControl( EPG_LIST ).reset()
        #On parcours les timers
        #pour les mettre dans la listbox
        for prog in timers:
            debug ( "TIMERS => %s " % str(prog.name))
            (heure, minute, sec) = decoupe(prog.start)
            h_start = '%02d:%02d' % (heure, minute)
            (heure, minute, sec) = decoupe(prog.stop)
            h_stop = '%02d:%02d' % (heure, minute)
            #On recupere le nom de la chaine en fct de son numéro
            for c_name in self.channels:
                debug ( "NO = -%d-, CH = -%d- " %  (int(c_name.no),
                                                    int(prog.channel)))
                if int(c_name.no) == int(prog.channel):
                    debug ( "No = %s, c_name=>.name_tok = %s" % (c_name.no,
                                                                 c_name.name_tok))
                    prog.channel = c_name.name_tok
                    prog.no_ch = c_name.no
                    break
            #Dans VDR il y a deux manières de stocker le jour
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
            if prog.active == 1:
                on = '*'
            else:
                on = ' '
            listTimers = xbmcgui.ListItem(label='%2s %10s' %
                                          (on, prog.channel), 
                                          label2=prog.name)
           #On rempli les différents champs du skin
            listTimers.setProperty( "channel", str(prog.channel) )
            listTimers.setProperty( "no_ch", str(prog.no_ch) )
            listTimers.setProperty( "start", h_start )
            listTimers.setProperty( "stop", h_stop )
            listTimers.setProperty( "day", str(prog.day) )
            listTimers.setProperty( "active", str(prog.active))
            listTimers.setProperty( "index", str(prog.index))
            listTimers.setProperty( "filename", str(prog.name))
            listTimers.setProperty( "priority", str(prog.prio))
            listTimers.setProperty( "lifetime", str(prog.lifetime))
 
            self.getControl( EPG_LIST ).addItem( listTimers )

    def delTimer(self, index):
        """
        Delete timer in VDR
        """
        debug ( "Delete TIMER")
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('delt %s' % index)
        self.vdrpclient.close() 

    def activateTimer(self, activate):
        """
        ON/OFF timer in VDR
        """
        debug ( "ACTIVATE TIMER")
        #Properties pour les timers
        #  status:channel:day    :start:stop:priority:lifetime:filename:
        #1 0     :      3:MT-TF--: 0644:0902:      50:      30:    Ludo:
        channel = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('channel')
        no_channel = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('no_ch')
        start = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('start')
        start = start.replace(':','')
        stop = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('stop')
        stop = stop.replace(':','')
        day = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('day')
        filename = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('filename')
        priority = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('priority')
        lifetime = self.getControl( EPG_LIST
                                 ).getSelectedItem().getProperty('lifetime')
 
        cmd_svdrp = "%s:%s:%s:%s:%s:%s:%s:%s:" % (activate, no_channel,
                                           day,
                                           start,
                                           stop,
                                           priority,
                                           lifetime,
                                           filename)
        self.vdrpclient = svdrp.SVDRPClient(VDR_HOST, VDR_PORT)
        self.vdrpclient.send_command('updt %s' % cmd_svdrp)
        self.vdrpclient.close() 

    def onClick( self, controlId ):
        """
        actions lorsque on clique sur un bouton du skin
        """
        debug ( "onClick TIMERWIN = %d " % controlId)
        #delete timer
        if ( controlId == DEL):
            dialog = xbmcgui.Dialog()
            timer_index = self.getControl( EPG_LIST
                                   ).getSelectedItem().getProperty('index')
            timer_name = self.getControl( EPG_LIST
                                   ).getSelectedItem().getProperty('filename')
            locstr = __addon__.getLocalizedString(id=603) #Delete
            locstr2 = __addon__.getLocalizedString(id=604) #Do you want del timer No
            #Fix temporary unicode error
            try:
                ret = dialog.yesno(locstr, locstr2 %
                               (timer_index, timer_name))
            except:
                ret = dialog.yesno(locstr, 
                                   'Effacer timer : %s[CR]Erreur unicode dans le titre' % timer_index)

            debug ( "ret = %s " % ret)
            if ret == 1:
                self.delTimer(timer_index)
                self.listTimers()
        #Toggle ON/OFF timer
        elif (controlId == ON):
            timer_actif = self.getControl( EPG_LIST
                                         ).getSelectedItem().getProperty('active')
            timer_name = self.getControl( EPG_LIST
                                   ).getSelectedItem().getProperty('filename')
            if timer_actif == '0':
                cmd_activate = __addon__.getLocalizedString(id=607) #'activate'
                timer_actif = 1
            else:
                cmd_activate = __addon__.getLocalizedString(id=608) #'de-activate'
                timer_actif = 0
            dialog = xbmcgui.Dialog()
            locstr = __addon__.getLocalizedString(id=605) #Activate
            locstr2 = __addon__.getLocalizedString(id=606) #Do you want %s this timer : %s ?
            ret = dialog.yesno(locstr, locstr2 %
                               (cmd_activate, timer_name))
            if ret == 1:
                self.activateTimer(timer_actif)
                self.listTimers()
 
        elif (controlId == ACTIF):
            debug ( "ControID = ACTIF")
        elif (controlId == CHAINE):
            debug ( "ControID = CHAINE")
            text = self.getControl( CHAINE ).getLabel()
            debug ( '==> text = %s ' % text)
            kb = xbmc.Keyboard('default', 'heading', True)
            kb.setHeading('Entrer le nom de la chaîne') # optional
            kb.setDefault(text) # optional
            kb.setHiddenInput(False)
            kb.doModal()
            if (kb.isConfirmed()):
                text = kb.getText()
                self.getControl( CHAINE ).setLabel(text)
        elif (controlId == JOUR):
            debug ( "ControID = JOUR")
        elif (controlId == DEBUT):
            debug ( "ControID = DEBUT")
        elif (controlId == FIN):
            debug ( "ControID = FIN")
        elif (controlId == QUIT):
            debug ( "ControID = QUIT")
            self.close()




class VDRWindow(xbmcgui.WindowXML):
    """
    Window for Timer window
    """
   
    def onInit( self ):
        actions = ['Programmes','Programmation','Enregistrements']
        debug ( "Init VDRWindow")

    def onClick( self, controlId ):
        """
        Actions when mouse click on control
        """
        debug ( "onClick controId = %d " % controlId)
        if (controlId == 1001):
            #epgWIN = EPGWindow( "epgWIN.xml" , __cwd__, "Default")
            try:
                epgWIN = EPGWindow( "epgWIN.xml" , __cwd__,'aeon.nox.svn')
            except:
                epgWIN = EPGWindow( "epgWIN.xml" , __cwd__)
            epgWIN.doModal()
        elif (controlId == 1002):
            try:
                timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, 'aeon.nox.svn')
            except:
                timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
            timersWIN.doModal()
            del timersWIN
        #elif (controlId == 1003):
        #    timersWIN = xbmcgui.WindowXML( "fixed.xml" , __cwd__, "Default")
            #timersWIN = TIMERSWindow( "timersWIN.xml" , __cwd__, "Default")
        #    timersWIN.doModal()
        #    del timersWIN

        elif (controlId == QUIT):
            self.close()

try:
    mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__,'aeon.nox.svn' )
except:
    mydisplay = VDRWindow( "script-svdrp-main.xml" , __cwd__, "Default")

mydisplay.doModal()
del mydisplay
