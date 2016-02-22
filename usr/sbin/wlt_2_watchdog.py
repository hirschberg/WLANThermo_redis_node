#!/usr/bin/python
import os
import pyinotify
import subprocess
import ConfigParser
import thread
import time
import sys
import logging
import threading
import RPi.GPIO as GPIO
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)

rPubSub = redis.StrictRedis(host='localhost', port=6379, db=0)
pubsub  = rPubSub.pubsub(ignore_subscribe_messages=True)
pubsub.subscribe('todo')

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

wm = pyinotify.WatchManager()
#mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_CLOSE_WRITE
mask = pyinotify.IN_CLOSE_WRITE

# cf = '/var/www/conf/WLANThermo.conf'

# Config = ConfigParser.ConfigParser()
# Config.read(cf)

LOGFILE = r.hget('config:daemon_logging', 'file')

logger = logging.getLogger('WLANthermoWD')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL

#edit Felix
level = logging.getLevelName(str(r.hget('config:daemon_logging', 'level_compy')))
logger.setLevel(level)

# end edit Felix
handler = logging.FileHandler(str(LOGFILE))
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info('WLANThermoWD started')


# class fs_wd(pyinotify.ProcessEvent):

#     def process_IN_CLOSE_WRITE(self, event):
#         if (os.path.join(event.path, event.name) == "/var/www/conf/WLANThermo.conf"):
#             #print "IN_CLOSE_WRITE: %s " % os.path.join(event.path, event.name)
#             read_config()

def reboot_pi():
    logger.info('reboot PI')
    #cfgfile = open(cf,'w')
    #Config.set('ToDo', 'raspi_reboot', 'False')
    #Config.write(cfgfile)
    #cfgfile.close()
    #Stoppe die Dienste
    handle_service('/etc/init.d/WLANThermo', 'stop')
    handle_service('/etc/init.d/WLANThermoPIT', 'stop')
    #Schreibe aufs LCD
    fw = open('/var/www/tmp/display/wd','w')
    fw.write('------ACHTUNG!-------;WLAN-Thermometer;- startet neu -;bis gleich...')
    fw.close()
    
    bashCommand = 'sudo reboot'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

def halt_pi():
    logger.info('shutdown PI')
    #cfgfile = open(cf,'w')
    #Config.set('ToDo', 'raspi_shutdown', 'False')
    #Config.write(cfgfile)
    #cfgfile.close()
    #Stoppe die Dienste
    handle_service('/etc/init.d/WLANThermo', 'stop')
    handle_service('/etc/init.d/WLANThermoPIT', 'stop')
    #Schreibe aufs LCD
    fw = open('/var/www/tmp/display/wd','w')
    fw.write('------ACHTUNG!-------;WLAN-Thermometer;- heruntergefahren -;und Tschuess...')
    fw.close()
    
    bashCommand = 'sudo halt'
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))
 

# def read_config():
#     global cf
#     logger.debug('Read Config..')
#     try:
#         # Konfigurationsdatei einlesen
#         Config = ConfigParser.ConfigParser()
#         Config.read(cf)
#         if (Config.getboolean('ToDo', 'restart_thermo')):
#             logger.info('Restart Thermo Process...')
#             handle_service('service WLANThermo', 'restart')
#             time.sleep(3)
#             logger.info('Aendere config wieder auf False')
#             cfgfile = open(cf,'w')
#             Config.set('ToDo', 'restart_thermo', 'False')
#             Config.write(cfgfile)
#             cfgfile.close()
#             # Config.save()

#         if (Config.getboolean('ToDo', 'restart_pitmaster')):
#             logger.info('Restart Pitmaster')
#             handle_service('service WLANThermoPIT', 'restart')
#             time.sleep(3)
#             logger.info('Aendere config wieder auf False')
#             cfgfile = open(cf,'w')
#             Config.set('ToDo', 'restart_pitmaster', 'False')
#             Config.write(cfgfile)
#             cfgfile.close()

#         if (Config.getboolean('ToDo', 'raspi_shutdown')):
#             halt_pi()
        
#         if (Config.getboolean('ToDo', 'restart_display')):
#             check_display()

#         if (Config.getboolean('ToDo', 'raspi_reboot')):
#             reboot_pi()
#         if (Config.getboolean('ToDo', 'backup')):
#             logger.info('create backup!')
#             cfgfile = open(cf,'w')
#             Config.set('ToDo', 'backup', 'False')
#             Config.write(cfgfile)
#             cfgfile.close()
#             ret = os.popen("/usr/sbin/wlt_2_backup.sh").read()
#             logger.debug(ret)
#         if (Config.getboolean('ToDo', 'update_gui')):
#             logger.info('create backup!')
#             cfgfile = open(cf,'w')
#             Config.set('ToDo', 'update_gui', 'False')
#             Config.write(cfgfile)
#             cfgfile.close()
#             ret = os.popen("/usr/sbin/wlt_2_update_gui.sh").read()
#             logger.debug(ret)
            
#         if (Config.getboolean('ToDo', 'create_new_log')):
#             logger.info('create new log')
#             #cfgfile = open(cf,'w')
#             #Config.set('ToDo', 'create_new_log', 'False')
#             #Config.set('Logging', 'write_new_log_on_restart', 'True')
#             #Config.write(cfgfile)
#             #cfgfile.close()
#             time.sleep(2)
#             handle_service('service WLANThermo', 'restart')
#             time.sleep(10)
#             #cfgfile = open(cf,'w')
#             #Config.set('Logging', 'write_new_log_on_restart', 'False')
#             #Config.write(cfgfile)
#             #cfgfile.close()
#             logger.info('finished create new log')

#         if (Config.getboolean('ToDo', 'pit_on')):
#             check_pitmaster() 

#     except:
#         logger.info('Unexpected error: ' +str(sys.exc_info()[0]))
#         raise

def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    logger.debug('handle_service: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

def check_file(f):
    if ( not os.path.isfile(f)):
        fw1 = open(f,'w')
        fw1.write('-')
        fw1.close()

def check_display():
    #logger.debug('Check Display')
    #logger.info('Aendere config wieder auf False')
    #cfgfile = open(cf,'w')
    #Config.set('ToDo', 'restart_display', 'False')
    #Config.write(cfgfile)
    #cfgfile.close()
    if r.hget('config:display', 'active'):
        logger.debug('Display enabled, run it')
        handle_service('service WLANThermoDIS', 'restart')
    else:
        handle_service('service WLANThermoDIS', 'stop')
            

def check_pitmaster():
    logger.debug('Check Pitmaster')
    pitmasterPID = os.popen("ps aux|grep wlt_2_pitmaster.py|grep -v grep|awk '{print $2}'").read()
    bashCommandPit = ''
    if r.hget('config:pitmaster', 'active'):
        if (len(pitmasterPID) < 1):
            logger.info('start pitmaster')
            bashCommandPit = 'sudo service WLANThermoPIT start'
        else:
            logger.info('pitmaster already running')
    else:
        if (len(pitmasterPID) > 0):
            logger.info('stop pitmaster')
            #obsolet
        else:
            logger.info('pitmaster already stopped')
    if (len(bashCommandPit) > 0):
        retcodeO = subprocess.Popen(bashCommandPit.split())
        retcodeO.wait()
        if retcodeO < 0:
            logger.info('Termin by signal')
        else:
            logger.info('Child returned' + str(retcodeO))

#notifier = pyinotify.Notifier(wm, fs_wd())

wdd = wm.add_watch('/var/www/conf', mask) #, rec=True)

#Config.read(cf)
check_display()
check_pitmaster()

print 'monitoring channel todo'
for m in pubsub.listen():
    redisData = str(m['data'])
    rd = redisData.split(';')
    print rd

    if str(m['channel']) == 'todo':
        print redisData
        print "todo"

#while True:
#    try:
#        Config.read(cf)
        #time.sleep(5) 
#        notifier.process_events()
#        if notifier.check_events():
#            notifier.read_events()
#    except KeyboardInterrupt:
#        notifier.stop()
#        logging.shutdown()
#        break
logging.shutdown()
logger.info('WLANThermoWD stopped')
