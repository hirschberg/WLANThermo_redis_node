#!/usr/bin/python
import sys
#import ConfigParser
import os
import time
import math
import logging
import string
import RPi.GPIO as GPIO
import math
import subprocess

import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

rPubSub = redis.StrictRedis(host='localhost', port=6379, db=0)
pubsub  = rPubSub.pubsub(ignore_subscribe_messages=True) #ignore_subscribe_messages=True
pubsub.subscribe('pit')

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel
last_pit = 0

LOGFILE = r.hget('config:daemon_logging', 'file')                                                                                                     

logger = logging.getLogger('WLANthermoPIT')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL

#edit Felix
level = logging.getLevelName(str(r.hget('config:daemon_logging', 'level_pit')))
logger.setLevel(level)

# end edit Felix
handler = logging.FileHandler(str(LOGFILE))
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info('WLANThermoPID started')

# Variablendefinition und GPIO Pin-Definition
ADC_Channel = 0  # Analog/Digital-Channel
#GPIO START
PIT_IO   = 2 # Pitmaster Relais 
PID_PWM  = 4 # Pitmaster PWM
#GPIO END


    
# Funktionsdefinition
def setPWM(val):
    subprocess.call (["echo 0=" + str(val) + " > /dev/servoblaster"], shell=True)
    print "pwm set"

def setIO(val):
    GPIO.output(PIT_IO, int(val))
    
def checkTemp(temp):
    r = 0
    try:
        r = float(temp)
    except ValueError:
        temp = temp[2:]
        r = float(temp)
    return r
    
def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    logger.debug('handle_service: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))

logger.info('Pitmaster Start')



#Log Dateinamen aus der config lesen
#current_temp = Config.get('filepath','current_temp')
#pitmaster_log = Config.get('filepath','pitmaster')

#Pfad aufsplitten
#pitPath,pitFile = os.path.split(pitmaster_log)

# Pin-Programmierung
GPIO.setup(PIT_IO, GPIO.OUT)


#Wenn das display Verzeichniss im Ram Drive nicht exisitiert erstelle es

#if not os.path.exists(pitPath):
#    os.makedirs(pitPath)

count = 0
chanel_name = [ "temp_0", "temp_1", "temp_2", "temp_3", "temp_4", "temp_5", "temp_6", "temp_7" ]
pit_new = 0
pit_val = 0



#Regelschleife

    
    #Aktuellen ist wert auslesen
    #tl = open(current_temp, 'r')

logger.debug('monitoring channel temperatures')
for m in pubsub.listen():
    redisData = str(m['data'])
    rd = redisData.split(';')
    print rd

    msg = ""


    pit_type = str(r.hget('config:pitmaster', 'type'))
    pit_pwm_min = r.hget('config:pitmaster','pwm_min')
    pit_curve = r.hget('config:pitmaster','curve')

    if pit_type == 'SERVO':
        logger.info('initialize servod')
        handle_service('service WLANThermoSERVO', 'restart')

    #Variablen
    if pit_type == 'IO':
        pit_val = 0 
    if pit_type == 'SERVO':
        pit_val = pit_pwm_min
    #print pit_curve
    steps = pit_curve.split("|")

    step = []
    for val in steps:
        step.append(val)

    step_temp = []
    step_val = []
    for val in step:
        v = val.split("!")
    #    print v[0]
    #    print v[1]
        step_temp.append(v[0]) 
        step_val.append(v[1])



    pit_type = str(r.hget('config:pitmaster', 'type'))
    pit_pwm_min = r.hget('config:pitmaster','pwm_min')
    pit_curve = r.hget('config:pitmaster','curve')

    #rd = ['19.12.14 00:30:41', '90.0', '21.7', '18.8', '999.9', '999.9', '999.9', '999.9', '999.9', 'ok', 'ok', 'ok', 'er', 'er', 'er', 'er', 'er']

    logger.debug('check temps and control...')
#    Config.read('/var/www/conf/WLANThermo.conf')
    pit_curve = r.hget('config:pitmaster','curve')
    pit_set = float(r.hget('config:pitmaster','set'))
    pit_ch = int(r.hget('config:pitmaster','ch'))
    pit_pause = float(r.hget('config:pitmaster','pause'))
    pit_pwm_min = int(r.hget('config:pitmaster','pwm_min'))
    pit_pwm_max = int(r.hget('config:pitmaster','pwm_max'))
    pit_man = int(r.hget('config:pitmaster','man'))
    if pit_man == 0:
        temps = rd
        if temps[(pit_ch + 9)] == "er":
            msg = msg + '|Kein Temperaturfuehler an Kanal ' + str(pit_ch) + ' angeschlossen!'
        else:
            print str(temps[(pit_ch + 1)])
            pit_now = float(checkTemp(temps[(pit_ch + 1)]))
            msg = msg + "|Ist: " + str(pit_now) + " Soll: " + str(pit_set)
            print msg
            calc = 0
            s = 0
            for step in step_temp:
                if calc == 0:
                    dif = pit_now - pit_set
                    msg = msg + "|Dif: " + str(dif)
                    if (dif <= float(step)):
                        calc = 1
                        msg = msg + "|Step: " + step
                        pit_new = step_val[s]
                        msg = msg + "|New: " + pit_new
                    if (pit_now >= pit_set):
                        calc = 1
                        pit_new = 0
                        msg = msg +  "|New-overshoot: " + str(pit_new)
                s = s + 1
            if calc == 0:
                msg = msg + "|Keine Regel zutreffend, Ausschalten!"
                pit_new = 0
        if pit_type == "SERVO":
            #Berechne die Position mit den min und max Werten...
            msg = msg + "|Min: " + str(pit_pwm_min) + " Max: " + str(pit_pwm_max)
            x = (pit_pwm_max - pit_pwm_min) * (float(pit_new) / 100) + pit_pwm_min
            if x != pit_val:
                msg = msg + "|Drive Servo to: " + str(x) + " = " + str(pit_new) + "%"
                print msg
                pit_val = x
                if last_pit == 0 and pit_new < (pit_pwm_min + 10): #Wenn vorher 0% war zuerst auf 25% und dann nach einer Sekunde auf den berechneten Wert stellen.
                    setPWM((pit_pwm_max - pit_pwm_min) * (25 / 100) + pit_pwm_min)
                    #print "pwm1"
                    time.sleep(1.0)
                setPWM(int(pit_val))
                print pit_val
            else:
                msg = msg + "|Servo pos: " + str(pit_new) + "% = " + str(pit_val)
                last_pit = pit_val
        if pit_type == "IO":
            if pit_val != pit_new:
                setIO(pit_new)
            logger.info('IO: ' + str(pit_new))
        # Export das aktuellen Werte in eine Text datei
        lt = time.localtime()#  Uhrzeit des Messzyklus
        jahr, monat, tag, stunde, minute, sekunde = lt[0:6]
        Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
        Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
        
        Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
        Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
        
        #fp = open(pitPath + '/' + pitFile, 'w')
        # Schreibe mit Trennzeichen ; 
        # Zeit;Soll;Ist;%;msg
        #fp.write(str(Uhrzeit_lang) + ';'+ str(pit_set) + ';' + str(pit_now) + ';' + str(pit_new) + '%;' + msg)
        #fp.close()



        ###muss wieder aktiviert werden
        # if (Config.getboolean('ToDo', 'pit_on') == False):
        #     if (count > 0):
        #         if pit_type == "SERVO":
        #             setPWM(int(pit_pwm_min))
        #         if pit_type == "IO":
        #             setIO(0)
        #         logger.info('WLANThermoPID stopped')
        #         break
        #     count = 1
    else:
        setPWM(pit_man)
        print "pwm3"
    if len(msg) > 0:
        logger.debug(msg)
    #time.sleep(pit_pause)

print "WLANThermoPID stopped"
