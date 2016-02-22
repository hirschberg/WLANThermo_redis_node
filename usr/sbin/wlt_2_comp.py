#!/usr/bin/python
import os
import psutil
import time
import math
import string
import logging
import RPi.GPIO as GPIO
import urllib
import wlt_alarm
import subprocess

#edit Felix
from time import strftime
import json
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)
# muster insert fuer verschachtelte Hashes
#r.hmset("config:sensortyp:ACURITE", {"a":"0.003344", "b":"0.000251911", "c":"0.00000351094", "Rn":"47"})

rPubSub = redis.StrictRedis(host='localhost', port=6379, db=0)
pubsub  = rPubSub.pubsub() #ignore_subscribe_messages=True
pubsub.subscribe('temperatures', 'todo', 'pit', 'lcd', 'clientdata', 'clienttemps', 'clientsettings')

#sollte das script neu gestartet werden, fliegt halt hier bloederweise das log um die ohren
r.delete("log:temp")

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel

LOGFILE = r.hget('config:daemon_logging', 'file')

logger = logging.getLogger('WLANthermoCOMP')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL

#edit Felix
level = logging.getLevelName(str(r.hget('config:daemon_logging', 'level_compy')))
logger.setLevel(level)

# end edit Felix
handler = logging.FileHandler(str(LOGFILE))
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info('WLANThermo started')

logger.info('REDIS connected wlt_2_comp')



# Funktionsdefinition
#edit Felix
# def alarm_email(SERVER,USER,PASSWORT,FROM,TO,SUBJECT,MESSAGE):
# jetzt in wlt_alarm.py zu finden
# end edit Felix

def readAnalogData(adcChannel, SCLKPin, MOSIPin, MISOPin, CSPin):
    # Pegel vorbereiten
    GPIO.output(CSPin,   HIGH)  
    GPIO.output(CSPin,   LOW)
    GPIO.output(SCLKPin, LOW)
        
    sendcmd = adcChannel
    sendcmd |= 0b00011000 # Entspricht 0x18 (1:Startbit, 1:Single/ended)
    
    # Senden der Bitkombination (Es finden nur 5 Bits Beruecksichtigung)
    for i in range(5):
        if (sendcmd & 0x10): # (Bit an Position 4 pruefen. Zaehlung beginnt bei 0)
            GPIO.output(MOSIPin, HIGH)
        else:
            GPIO.output(MOSIPin, LOW)
        # Negative Flanke des Clocksignals generieren    
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)
        sendcmd <<= 1 # Bitfolge eine Position nach links schieben
            
    # Empfangen der Daten des ADC
    adcvalue = 0 # Ruecksetzen des gelesenen Wertes
    for i in range(13):
        GPIO.output(SCLKPin, HIGH)
        GPIO.output(SCLKPin, LOW)
        # print GPIO.input(MISOPin)
        adcvalue <<= 1 # 1 Postition nach links schieben
        if(GPIO.input(MISOPin)):
            adcvalue |= 0x01
    return adcvalue

def temperatur_sensor (Rt, sensortyp): #Ermittelt die Temperatur

    #Messungen beschleunigen durch pipelining der redis commands
    #pipe = r.pipeline()
    
    a = float(r.hget('config:sensortyp:'+sensortyp, 'a'))
    b = float(r.hget('config:sensortyp:'+sensortyp, 'b'))
    c = float(r.hget('config:sensortyp:'+sensortyp, 'c'))
    Rn = float(r.hget('config:sensortyp:'+sensortyp, 'Rn'))

    try: 
       v = math.log(Rt/Rn)
       T = (1/(a + b*v + c*v*v)) - 273
    except: #bei unsinnigen Werten (z.B. ein- ausstecken des Sensors im Betrieb) Wert 999.9
       T = 999.9
    return T

def dateiname(): #Zeitstring fuer eindeutige Dateinamen erzeugen

    zeit = time.localtime()
    # fn = string.zfill(zeit[2],2)+string.zfill(zeit[1],2)+str(zeit[0])+string.zfill(zeit[3],2)+string.zfill(zeit[4],2)+string.zfill(zeit[5],2)
    fn = str(zeit[0]) + string.zfill(zeit[1],2) + string.zfill(zeit[2],2) + "_" + string.zfill(zeit[3],2)+string.zfill(zeit[4],2)+string.zfill(zeit[5],2)
    return fn

def handle_service(sService, sWhat):
    bashCommand = 'sudo ' + sService + ' ' + sWhat #/etc/init.d/WLANThermo restart'
    logger.debug('handle_service: ' + bashCommand)
    retcode = subprocess.Popen(bashCommand.split())
    retcode.wait()
    if retcode < 0:
        logger.info('Termin by signal')
    else:
        logger.info('Child returned' + str(retcode))


# Variablendefinition und GPIO Pin-Definition
ADC_Channel = 0  # Analog/Digital-Channel
#GPIO START
SCLK        = 18 # Serial-Clock
MOSI        = 24 # Master-Out-Slave-In
MISO        = 23 # Master-In-Slave-Out
CS          = 25 # Chip-Select
BEEPER      = 17 # Piepser
#GPIO END


# Kanalvariablen-Initialisierung
Sensornummer_typ = ['ACURITE','ACURITE','ACURITE','ACURITE','ACURITE','ACURITE','ACURITE','ACURITE']
Logkanalnummer = [True,True,True,True,True,True,True,True]

# Sensortypen und Logging aus der DB abfragen und in Arrays speichern
for x in range(0, 8):
    Sensornummer_typ[x] =  r.hget('sensors:'+str(x), 'sensortyp')
    Logkanalnummer[x]   =  r.hget('sensors:'+str(x), 'log')


#Einlesen Email-Parameter fuer Alarmmeldung
#Email_alert = Config.getboolean('Email','email_alert')
#Email_server  = Config.get('Email','server')
#Email_auth = Config.getboolean('Email','auth')
#Email_user = Config.get('Email','username')
#Email_password = Config.get('Email','password')
#Email_from = Config.get('Email','email_from')
#Email_to = Config.get('Email','email_to')
#Email_subject = Config.get('Email','email_subject')

#Einlesen der Software-Version
build = r.hget('config:version', 'software')

#Einlesen der Push Nachrichten Einstellungen
#PUSH = Config.getboolean('Push', 'push_on')
#PUSH_URL = Config.get('Push', 'push_url')

#Einlesen der Logging-Option
#newfile = Config.getboolean('Logging','write_new_log_on_restart')
# end edit Felix

# Pin-Programmierung
GPIO.setup(SCLK, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CS,   GPIO.OUT)
GPIO.setup(BEEPER,  GPIO.OUT)

sound_on = r.hget('config:sound', 'beeper')
if sound_on == "true":
    sound_on = 1
else:
    sound_on = 0
GPIO.output(BEEPER, sound_on)

time.sleep(0.2)

GPIO.output(BEEPER, LOW)

#Alarmstatusspeicher loeschen
Alarm_state_high_previous = 0
Alarm_state_low_previous = 0

while True: #Messchleife

    CPU_usage = psutil.cpu_percent(interval=1, percpu=True)
    ram = psutil.phymem_usage()
    ram_free = ram.free / 2**20
    logger.debug('CPU: ' + str(CPU_usage) + ' RAM free: ' + str(ram_free))

    Alarm_irgendwo = False
    Alarm_message = 'Achtung!\n'
    Alarm_state_high_bin = 0
    Alarm_state_low_bin = 0
    Alarm_high = [999,999,999,999,999,999,999,999]
    Alarm_low = [0,0,0,0,0,0,0,0]
    Temperatur = [0.10,0.10,0.10,0.10,0.10,0.10,0.10,0.10]
    Temperatur_string = ['999.9','999.9','999.9','999.9','999.9','999.9','999.9','999.9']
    Temperatur_alarm = ['er','er','er','er','er','er','er','er']
    Displaytemp = ['999.9','999.9','999.9','999.9','999.9','999.9','999.9','999.9']


    for kanal in range (8): #Maximal 8 Kanaele abfragen
        #print "ANFANG__________________KANAL:" + str(kanal)
        sensortyp           =  r.hget('sensors:' + str(kanal), 'sensortyp')
        Alarm_high[kanal]   =  int(r.hget('sensors:' + str(kanal), 'temp_max'))
        Alarm_low[kanal]    =  int(r.hget('sensors:' + str(kanal), 'temp_min'))
        #sensortyp = Sensornummer_typ[kanal]
        
        Temp = 0
	gute = 0
        for i in range (int(r.hget('config:measure', 'iterations'))): #Anzahl iterations Werte messen und Durchschnitt bilden

            ADC_Channel = kanal
            Wert = 4096 - readAnalogData(ADC_Channel, SCLK, MOSI, MISO, CS)
	    # print kanal , Wert        
            if (Wert > 30) and (sensortyp!='KTYPE'): #sinvoller Wertebereich
                Rtheta = int(r.hget('config:measure', 'resistance'))*((4096.0/Wert) - 1)
                #print "Sensortyp" + sensortyp
                #print "Rheta: "+ str(Rtheta)
                #Tempvar = temperatur_sensor(Rtheta,sensortyp)
                Tempvar = temperatur_sensor(Rtheta,sensortyp)
                #print str(Tempvar) +" Grad"
                if Tempvar <> 999.9: #normale Messung, keine Sensorprobleme
		    gute = gute + 1
                    Temp = Temp + Tempvar
                    Temperatur[kanal] = round(Temp/gute,2)
                    r.hset('sensors:'+str(kanal),str('current'),Temperatur[kanal])
                else:
                    if gute==0:
		            Temperatur[kanal]  = 999.9 # Problem waehrend des Messzyklus aufgetreten, Errorwert setzen
                    r.hset('sensors:'+str(kanal),str('current'),Temperatur[kanal])
            else:
                if Sensornummer_typ[kanal]=='KTYPE':
                    Temperatur[kanal] = Wert*330/4096
                    r.hset('sensors:'+str(kanal),str('current'),Temperatur[kanal])
                else:
                    Temperatur[kanal] = 999.9 # kein sinnvoller Messwert, Errorwert setzen
                    r.hset('sensors:'+str(kanal),str('current'),Temperatur[kanal])

        #print "ENDE__________________KANAL:" + str(kanal)
	if gute <> int(r.hget('config:measure', 'iterations')) :
	    logger.warning('Kanal: ' + str(kanal))  
        logger.warning('Kanal: ' + str(kanal) + ' konnte nur ' + str(gute) + ' von ' + str(r.hget('config:measure', 'iterations')) + ' messen!!')  
        if Temperatur[kanal] <> 999.9:    
            Temperatur_string[kanal] = "%.1f" % Temperatur[kanal]
            Temperatur_alarm[kanal] = 'ok'
            if Temperatur[kanal] >= Alarm_high[kanal]:
                #Alarmstatus high aufdatieren
                Alarm_irgendwo = True
                Alarm_state_high_bin = Alarm_state_high_bin + pow(2, kanal)
                Alarm_message = Alarm_message + 'Kanal ' + str(kanal) + ' hat Uebertemperatur!\n'
                if int(r.hget('config:sound', 'beeper') == 'true') :
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)
                    time.sleep(0.2)
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)
                    time.sleep(0.2)
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)

                Temperatur_alarm[kanal] = 'hi'
                #Temperatur_string[kanal] = chr(1) + "%.1f" % Temperatur[kanal]
            if Temperatur[kanal] <= Alarm_low[kanal]:
                #Alarmstatus low aufdatieren
                Alarm_irgendwo = True
                Alarm_state_low_bin = Alarm_state_low_bin + pow(2, kanal) 
                Alarm_message = Alarm_message + 'Kanal ' + str(kanal) + ' hat Untertemperatur!\n'
                if int(r.hget('config:sound', 'beeper') == 'true') :
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)
                    time.sleep(0.2)
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)
                    time.sleep(0.2)
                    GPIO.output (BEEPER,sound_on)
                    time.sleep(0.2)
                    GPIO.output (BEEPER, LOW)
                Temperatur_alarm[kanal] = 'lo'
                #Temperatur_string[kanal] = chr(0) + "%.1f" % Temperatur[kanal]
                
                
    #Pruefen, ob mehr Alarmzustaende gegenueber dem letzten Lauf vorliegen. Wenn ja, email schicken, wenn gewuenscht.
    
    if ((Alarm_state_high_bin > Alarm_state_high_previous) or (Alarm_state_low_bin > Alarm_state_low_previous)):
        
        if r.hget('config:email', 'alert') == 'true': #wenn konfiguriert, email schicken
            #alarm_email(Email_server,Email_user,Email_password, Email_from, Email_to, Email_subject, Alarm_message)
            logger.debug('Alarmmail gesendet!')
        if r.hget('config:push', 'alert') == 'true':
            Alarm_message2 = urllib.quote(Alarm_message)
            #push_cmd =  PUSH_URL.replace('messagetext', Alarm_message2.replace('\n', '<br/>'))
            #push_cmd = 'wget -q -O - ' + push_cmd
            #logger.debug(push_cmd)
            #os.popen(push_cmd)
    
    Alarm_state_high_previous = Alarm_state_high_bin #aktuellen Alarm-Status sichern
    Alarm_state_low_previous = Alarm_state_low_bin   
    
    #Temperaturen fuer Display anzeige aufbereiten
    if int(r.hget('config:display', 'present') == 1):
        for kanal in range(8):
            Displaytemp[kanal] = Temperatur_string[kanal]
    
    # Log datei erzeugen
    lt = time.localtime()#  Uhrzeit des Messzyklus
    jahr, monat, tag, stunde, minute, sekunde = lt[0:6]
    Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
    Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit

    Temperatur_string.append(Uhrzeit_lang)
    json_temp = json.dumps(Temperatur_string)

    logstring = "{\"templog\":[{\"time\":\""+strftime("%Y-%m-%d %H:%M:%S") + "\"}"
    for kanal in range(8):# eine Zeile mit allen Temperaturen
        sensor = 'sensors:' + str(kanal)
        sensorname =  "\"" + r.hget(sensor, 'name') + "\""
        logstring = logstring + ", {\"name\":" + sensorname
        logstring = logstring + ", \"temp\":" + str(Temperatur_string[kanal]) + "}"
    logstring = logstring + "]}"
    #r.rpush("log:temp", {strftime("%Y-%m-%d %H:%M:%S"):str(logstring)})
    r.rpush("log:temp", str(logstring))


    #Generating a JSON-String for the Clients with all Data
    clientdata = "{\"time\":\""+strftime("%Y-%m-%d %H:%M:%S") + "\","
    clientdata = clientdata + "\"sensors\": {"
    for kanal in range(8):# eine Zeile mit allen Temperaturen
        clientdata = clientdata + "\"sensor" + str(kanal) + "\": {"
        sensor = 'sensors:' + str(kanal)
        sensorname =  "\"" + r.hget(sensor, 'name') + "\""
        clientdata = clientdata + "\"name\":" + sensorname + ","
        clientdata = clientdata + "\"current\":" + Temperatur_string[kanal] +","
        clientdata = clientdata + "\"sensortyp\": \"" + r.hget(sensor, 'sensortyp') + "\", "
        clientdata = clientdata + "\"temp_min\": \"" + r.hget(sensor, 'temp_min') + "\", "
        clientdata = clientdata + "\"temp_max\": \"" + r.hget(sensor, 'temp_max') + "\", "
        clientdata = clientdata + "\"web_alert\": \"" + r.hget(sensor, 'web_alert') + "\", "
        clientdata = clientdata + "\"color\": \"" + r.hget(sensor, 'color') + "\""
        clientdata = clientdata + "}"
        if (kanal < 7):
            clientdata = clientdata + ","
    clientdata = clientdata + "}}"
    #and publish it via Redis
    r.publish('clientdata', clientdata)
    print "clientdata "+str(clientdata)
    #End JSON-Generate

    #Generating a JSON-String for the Temperatures
    clienttemps = "{\"time\":\""+strftime("%Y-%m-%d %H:%M:%S") + "\","
    clienttemps = clienttemps + "\"sensors\": {"
    for kanal in range(8):# eine Zeile mit allen Temperaturen
        clienttemps = clienttemps + "\"sensor" + str(kanal) + "\": {"
        clienttemps = clienttemps + "\"current\":" + Temperatur_string[kanal]
        clienttemps = clienttemps + "}"
        if (kanal < 7):
            clienttemps = clienttemps + ","
    clienttemps = clienttemps + "}}"
    #and publish it via Redis
    r.publish('clienttemps', clienttemps)
    print "clienttemps "+str(clienttemps)
    #End JSON-Generate

   #Generating a JSON-String for the Clients with all Data
    clientsettings = "{\"time\":\""+strftime("%Y-%m-%d %H:%M:%S") + "\","
    clientsettings = clientsettings + "\"sensors\": {"
    for kanal in range(8):# eine Zeile mit allen Temperaturen
        clientsettings = clientsettings + "\"sensor" + str(kanal) + "\": {"
        sensor = 'sensors:' + str(kanal)
        sensorname =  "\"" + r.hget(sensor, 'name') + "\""
        clientsettings = clientsettings + "\"name\":" + sensorname + ","
        clientsettings = clientsettings + "\"sensortyp\": \"" + r.hget(sensor, 'sensortyp') + "\", "
        clientsettings = clientsettings + "\"temp_min\": \"" + r.hget(sensor, 'temp_min') + "\", "
        clientsettings = clientsettings + "\"temp_max\": \"" + r.hget(sensor, 'temp_max') + "\", "
        clientsettings = clientsettings + "\"web_alert\": \"" + r.hget(sensor, 'web_alert') + "\", "
        clientsettings = clientsettings + "\"color\": \"" + r.hget(sensor, 'color') + "\""
        clientsettings = clientsettings + "}"
        if (kanal < 7):
            clientsettings = clientsettings + ","
    clientsettings = clientsettings + "}"
    clientsettings = clientsettings + "\"config\":\"" + r.hget('config:measure', 'delay') + "\","
    clientsettings = clientsettings + "}"
    #and publish it via Redis
    r.publish('clientsettings', clientsettings)
    print "clientsettings "+str(clientsettings)
    #End JSON-Generate



    redisplay = str(Uhrzeit_lang)
    for kanal in range(8):# eine Zeile mit allen Temperaturen fuers display ueber redis
        redisplay = redisplay + ";" + str(Temperatur_string[kanal])

    r.publish('temperatures', redisplay)
    print "published temps "+str(redisplay)

    #Log fuer den Alarm, falls die min Temp nicht erreicht (Versuch, die hoechste Temperatur zu loggen)
    # for kanal in range(8):


    #     if (r.get('log:tempmin_alarm:'+str(kanal)) > int(Temperatur_string[kanal])):
    #         r.set('log:tempmin_alarm:'+str(kanal), Temperatur_string[kanal])


    #------------------------------------------------------------------------------------#
    #   Pitmaster Watchdog
    #------------------------------------------------------------------------------------#
    pitmasterPID = os.popen("ps aux|grep wlt_2_pitmaster.py|grep -v grep|awk '{print $2}'").read()
    bashCommandPit = ''
    if r.hget('config:pitmaster', 'active'):
        if (len(pitmasterPID) < 1):
            logger.info('start pitmaster')
            bashCommandPit = 'sudo service WLANThermoPIT start'
        else:
            logger.info('pitmaster already running')
        r.publish('pit', redisplay)
        print "published pit "+str(redisplay)
    else:
        if (len(pitmasterPID) > 0):
            logger.info('stop pitmaster')
            bashCommandPit = 'sudo service WLANThermoPIT stop'
        else:
            logger.info('pitmaster already stopped')
    if (len(bashCommandPit) > 0):
        retcodeO = subprocess.Popen(bashCommandPit.split())
        retcodeO.wait()
        if retcodeO < 0:
            logger.info('Termin by signal')
        else:
            logger.info('Child returned' + str(retcodeO))
        


    #------------------------------------------------------------------------------------#
    #   LCD Watchdog
    #------------------------------------------------------------------------------------#
    lcdPID = os.popen("ps aux|grep wlt_2_lcd_204.py|grep -v grep|awk '{print $2}'").read()
    if r.hget('config:display', 'active'):
        if (len(lcdPID) < 1):
            logger.info('start lcd')
            handle_service('sudo service WLANThermoDIS', 'start')
        else:
            logger.info('lcd already running')
        r.publish('lcd', redisplay)
        logger.info("published lcd "+str(redisplay))
    else:
        if (len(lcdPID) > 0):
            logger.info('stop lcd')
            handle_service('sudo service WLANThermoDIS', 'stop')
        else:
            logger.info('display already stopped')
    
    #------------------------------------------------------------------------------------#
    #   LCD restart >> send command
    #------------------------------------------------------------------------------------#

    #------------------------------------------------------------------------------------#
    #   LCD shutdown >> send command
    #------------------------------------------------------------------------------------#

    time.sleep(float(r.hget('config:measure', 'delay'))) 

logger.info('WLANThermo stopped!')
