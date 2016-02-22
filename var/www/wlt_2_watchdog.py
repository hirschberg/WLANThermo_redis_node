#!/usr/bin/python
import os
import pyinotify
import subprocess
import ConfigParser
import thread
import time
import sys
import threading
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

#GPIO START
HALT_IO   = 3 # Halt 
#GPIO END

#GPIO Setup
GPIO.setup(HALT_IO, GPIO.IN)


# Timing Konstanten
E_PULSE = 0.00005
E_DELAY = 0.00005


HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel

def wait_input():
    var=1
    counter = 0
    while var == 1:
        if GPIO.input(HALT_IO):
            counter += 1
            time.sleep(0.5)
        else:
            counter = 0
            time.sleep(1)
        if counter >= 3:
            print "halt"
            #halt_pi()
        time.sleep(2)

def reboot_pi():
        print "reboot PI"
        cfgfile = open(cf,'w')
        Config.set('ToDo', 'raspi_reboot', 'False')
        Config.write(cfgfile)
        cfgfile.close()
        #Stoppe die Dienste
        handle_service('/etc/init.d/WLANThermo', 'stop')
        handle_service('/etc/init.d/WLANThermoPIT', 'stop')
        #Schreibe aufs LCD
        fw1 = open('/var/www/tmp/zeile1.txt','w')
        fw1.write('------ACHTUNG!-------')
        fw1.close()
        fw2 = open('/var/www/tmp/zeile2.txt','w')
        fw2.write('WLAN-Thermometer')
        fw2.close()
        fw3 = open('/var/www/tmp/zeile3.txt','w')
        fw3.write('startet neu!')
        fw3.close()
        fw4 = open('/var/www/tmp/zeile4.txt','w')
        fw4.write('bis gleich...')
        fw4.close()
        
        bashCommand = 'sudo reboot'
        retcode = subprocess.Popen(bashCommand.split())
        retcode.wait()
        if retcode < 0:
            print "Termin by signal"
        else:
            print "Child returned", retcode

def halt_pi():
        print "shutdown PI"
        cfgfile = open(cf,'w')
        Config.set('ToDo', 'raspi_shutdown', 'False')
        Config.write(cfgfile)
        cfgfile.close()
        #Stoppe die Dienste
        handle_service('/etc/init.d/WLANThermo', 'stop')
        handle_service('/etc/init.d/WLANThermoPIT', 'stop')
        #Schreibe aufs LCD
        fw1 = open('/var/www/tmp/zeile1.txt','w')
        fw1.write('------ACHTUNG!-------')
        fw1.close()
        fw2 = open('/var/www/tmp/zeile2.txt','w')
        fw2.write('WLAN-Thermometer')
        fw2.close()
        fw3 = open('/var/www/tmp/zeile3.txt','w')
        fw3.write('- heruntergefahren -')
        fw3.close()
        fw4 = open('/var/www/tmp/zeile4.txt','w')
        fw4.write('und Tschuess...')
        fw4.close()
        
        bashCommand = 'sudo halt'
        retcode = subprocess.Popen(bashCommand.split())
        retcode.wait()
        if retcode < 0:
            print "Termin by signal"
        else:
            print "Child returned", retcode
 

wm = pyinotify.WatchManager()
#mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
mask = pyinotify.IN_CLOSE_WRITE

cf = '/var/www/conf/WLANThermo.conf'

Config = ConfigParser.ConfigParser()

class PTmp(pyinotify.ProcessEvent):

    def process_IN_CLOSE_WRITE(self, event):
        if (os.path.join(event.path, event.name) == "/var/www/conf/WLANThermo.conf"):
            print "IN_CLOSE_WRITE: %s " % os.path.join(event.path, event.name)
            read_config()

def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        print "Termin by signal"
    else:
        print "Child returned", retcode

def read_config():
    global cf
    try:
        # Konfigurationsdatei einlesen
        #Config = ConfigParser.ConfigParser()
        Config.read(cf)
        if (Config.getboolean('ToDo', 'restart_thermo')):
            print "Restart Thermo Process..."
            handle_service('/etc/init.d/WLANThermo', 'restart')
            time.sleep(3)
            print "Aendere config wieder auf False"
            cfgfile = open(cf,'w')
            Config.set('ToDo', 'restart_thermo', 'False')
            Config.write(cfgfile)
            cfgfile.close()
            # Config.save()

        if (Config.getboolean('ToDo', 'restart_pitmaster')):
            print "Restart Pitmaster"
            handle_service('/etc/init.d/WLANThermoPIT', 'restart')
            time.sleep(3)
            print "Aendere config wieder auf False"
            cfgfile = open(cf,'w')
            Config.set('ToDo', 'restart_pitmaster', 'False')
            Config.write(cfgfile)
            cfgfile.close()

        if (Config.getboolean('ToDo', 'raspi_shutdown')):
            halt_pi()
        
        if (Config.getboolean('ToDo', 'restart_display')):
            check_display()

        if (Config.getboolean('ToDo', 'raspi_reboot')):
            reboot_pi()
        if (Config.getboolean('ToDo', 'create_new_log')):
            print "create new log"
            cfgfile = open(cf,'w')
            Config.set('ToDo', 'create_new_log', 'False')
            Config.set('Logging', 'write_new_log_on_restart', 'True')
            Config.write(cfgfile)
            cfgfile.close()
            time.sleep(2)
            handle_service('/etc/init.d/WLANThermo', 'restart')
            time.sleep(2)
            cfgfile = open(cf,'w')
            Config.set('Logging', 'write_new_log_on_restart', 'False')
            Config.write(cfgfile)
            cfgfile.close()
            print "finished create new log"

        if (Config.getboolean('ToDo', 'pit_on')):
            check_pitmaster() 

    except:
        print "Unexpected error:", sys.exc_info()[0]
        raise

def check_file(f):
    if ( not os.path.isfile(f)):
        fw1 = open(f,'w')
        fw1.write('-')
        fw1.close()

def check_display():
    if (Config.get('Display', 'lcd_present')):
        fn = Config.get('Display', 'lcd_type')
        if(len(fn)>0):
            lcdPID = os.popen("ps aux|grep " + fn +"|grep -v grep|awk '{print $2}'").read()
            if (len(lcdPID) < 1):
                print "start display"
                bashCommandLCD = 'python /usr/sbin/' + fn
                retcodeO = subprocess.Popen(bashCommandLCD.split())
                retcodeO.wait()
                if retcodeO < 0:
                    print "Termin by signal"
                else:
                    print "Child returned", retcodeO
            else:
                print "display already running"
            

def check_pitmaster():
    pitmasterPID = os.popen("ps aux|grep wlt_2_pitmaster.py|grep -v grep|awk '{print $2}'").read()
    bashCommandPit = ''
    if (Config.getboolean('ToDo', 'pit_on')):
        if (len(pitmasterPID) < 1):
            print "start pitmaster"
            bashCommandPit = 'sudo service WLANThermoPIT start'
        else:
            print "pitmaster already running"
    else:
        if (len(pitmasterPID) > 0):
            print "stop pitmaster"
            #obsolet
        else:
            print "pitmaster already stopped"
    if (len(bashCommandPit) > 0):
        retcodeO = subprocess.Popen(bashCommandPit.split())
        retcodeO.wait()
        if retcodeO < 0:
            print "Termin by signal"
        else:
            print "Child returned", retcodeO

notifier = pyinotify.Notifier(wm, PTmp())

wdd = wm.add_watch('/var/www/conf', mask) #, rec=True)

#Start thread for shutdown pin
# deaktiviert bis die Schaltung Funktioniert!
#input_thread = threading.Thread(target = wait_input)
#input_thread.start()

Config.read(cf)
check_display()
check_pitmaster()

while True:
    try:
        Config.read(cf)
        #time.sleep(5) 
        notifier.process_events()
        if notifier.check_events():
            notifier.read_events()
    except KeyboardInterrupt:
        notifier.stop()
        break
input_thread.join()
print "\nWatchdog stopped!"
