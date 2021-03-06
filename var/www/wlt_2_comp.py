#!/usr/bin/python
import sys
import ConfigParser
import os
import time
import math
import string
import logging
import RPi.GPIO as GPIO
import math
import urllib
import psutil

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel

# Konfigurationsdatei einlesen
Config = ConfigParser.ConfigParser()
Config.read('/var/www/conf/WLANThermo.conf')

LOGFILE = Config.get('daemon_logging', 'log_file')
logger = logging.getLogger('WLANthermo')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL
#logger.setLevel(logging.DEBUG)
log_level = Config.get('daemon_logging', 'level_COMPY')
if log_level == 'DEBUG':
    logger.setLevel(logging.DEBUG)
if log_level == 'INFO':
    logger.setLevel(logging.INFO)
if log_level == 'ERROR':
    logger.setLevel(logging.ERROR)
if log_level == 'WARNING':
    logger.setLevel(logging.WARNING)
if log_level == 'CRITICAL':
    logger.setLevel(logging.CRITICAL)
handler = logging.FileHandler(LOGFILE)
handler.setLevel(logging.DEBUG)
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)

logger.info('WLANThermo started')

# Funktionsdefinition
def alarm_email(SERVER,USER,PASSWORT,FROM,TO,SUBJECT,MESSAGE):
    logger.info('Send mail!')
    from smtplib import SMTP as smtp
    from email.mime.text import MIMEText as text

    s = smtp(SERVER)

    s.login(USER,PASSWORT)

    m = text(MESSAGE)

    m['Subject'] = SUBJECT
    m['From'] = FROM
    m['To'] = TO


    s.sendmail(FROM,TO, m.as_string())
    s.quit()

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
    #time.sleep(0.1)
    return adcvalue

def temperatur_sensor (Rt, typ): #Ermittelt die Temperatur
    if typ=='ACURITE':
      # Kennlinienkonstanten Sensor ACURITE/Ventus
      a = 0.003344
      b = 0.000251911
      c = 0.00000351094
      Rn = 47

    if typ=='FANTAST':
      # Kennlinienkonstanten Sensor IKEA FANTAST
       a = 0.003339
       b = 0.000251911
       c = 0.00000351094
       Rn = 47
    
    if (typ=='MAVERICK') or (typ=='ET-732'):
      # Kennlinienkonstanten Sensor MAVERICK ET-732
       a = 0.0033354016
       b = 0.000225
       c = 0.00000251094
       Rn = 925

    if (typ=='ET-73'):
      # Kennlinienkonstanten Sensor MAVERICK ET-73!!
       a = 0.0033032
       b = 0.000332196
       c = 0.0000023677
       Rn = 160

    
    if typ=='ROSENSTEIN':
      # Kennlinienkonstanten Rosenstein und Soehne RF-T0601
       a = 0.003362
       b = 0.000251911
       c = 0.00000351094
       Rn = 100 

    
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


#Log Dateinamen aus der config lesen
current_temp = Config.get('filepath','current_temp')

#Sensortypen einlesen pro Kanal
Sensornummer_typ[0] =  Config.get('Sensoren','CH0')
Sensornummer_typ[1] =  Config.get('Sensoren','CH1')
Sensornummer_typ[2] =  Config.get('Sensoren','CH2')
Sensornummer_typ[3] =  Config.get('Sensoren','CH3')
Sensornummer_typ[4] =  Config.get('Sensoren','CH4')
Sensornummer_typ[5] =  Config.get('Sensoren','CH5')
Sensornummer_typ[6] =  Config.get('Sensoren','CH6')
Sensornummer_typ[7] =  Config.get('Sensoren','CH7')

#Loggingoptionen einlesen
Logkanalnummer[0] =  Config.getboolean('Logging','CH0')
Logkanalnummer[1] =  Config.getboolean('Logging','CH1')
Logkanalnummer[2] =  Config.getboolean('Logging','CH2')
Logkanalnummer[3] =  Config.getboolean('Logging','CH3')
Logkanalnummer[4] =  Config.getboolean('Logging','CH4')
Logkanalnummer[5] =  Config.getboolean('Logging','CH5')
Logkanalnummer[6] =  Config.getboolean('Logging','CH6')
Logkanalnummer[7] =  Config.getboolean('Logging','CH7')


separator = Config.get('Logging','Separator')


#Soundoption einlesen
sound_on = Config.getboolean('Sound','Beeper_enabled')

#Einlesen, ueber wieviele Messungen integriert wird 
iterations = Config.getint('Messen','Iterations')

#delay zwischen jeweils 8 Messungen einlesen 
delay = Config.getfloat('Messen','Delay')

#Einlesen des Reihenwiderstandes zum Fuehler (Hardwareabhaengig!!) 
messwiderstand = Config.getint('Messen','Messwiderstand')

#Einlesen Email-Parameter fuer Alarmmeldung
Email_alert = Config.getboolean('Email','email_alert')
Email_server  = Config.get('Email','server')
Email_auth = Config.getboolean('Email','auth')
Email_user = Config.get('Email','username')
Email_password = Config.get('Email','password')
Email_from = Config.get('Email','email_from')
Email_to = Config.get('Email','email_to')
Email_subject = Config.get('Email','email_subject')


#Einlesen der Software-Version
build = Config.get('Version','build')

#Einlesen Displayeinstellungen
LCD = Config.getboolean('Display','lcd_present')

#Einlesen der Push Nachrichten Einstellungen
PUSH = Config.getboolean('Push', 'push_on')
PUSH_URL = Config.get('Push', 'push_url')
#

#Einlesen der Logging-Option
newfile = Config.getboolean('Logging','write_new_log_on_restart')


# Pin-Programmierung
GPIO.setup(SCLK, GPIO.OUT)
GPIO.setup(MOSI, GPIO.OUT)
GPIO.setup(MISO, GPIO.IN)
GPIO.setup(CS,   GPIO.OUT)
#GPIO.setup(LED_ROT, GPIO.OUT)
#GPIO.setup(LED_GELB, GPIO.OUT)
#GPIO.setup(LED_GRUEN, GPIO.OUT)
GPIO.setup(BEEPER,  GPIO.OUT)

GPIO.output(BEEPER, sound_on)

time.sleep(1)

#GPIO.output(LED_ROT, LOW)
#GPIO.output(LED_GELB, LOW)
#GPIO.output(LED_GRUEN, LOW)
GPIO.output(BEEPER, LOW)

# Pfad fuer die uebergabedateien auslesen und auftrennen in Pfad und Dateinamen
curPath,curFile = os.path.split(current_temp)

#Wenn das display Verzeichniss im Ram Drive nicht exisitiert erstelle es
if not os.path.exists(curPath):
    os.makedirs(curPath)

#Temperatur-LOG-Verzeichnis anlegen, wenn noch nicht vorhanden und aktuelle Log-Datei generieren
try:
 os.mkdir('/var/log/WLAN_Thermo')
except: 
 nix=0

name = "/var/log/WLAN_Thermo/"  + dateiname() +'_TEMPLOG.csv' #eindeutigen Namen generieren 
if (newfile):# neues File beim Start anlegen
    fw = open(name,'w') #Datei anlegen

    # Falls der Symlink noch da ist, loeschen
    try:
        os.remove('/var/log/WLAN_Thermo/TEMPLOG.csv')
    except:
        nix=0

    os.symlink(name, '/var/log/WLAN_Thermo/TEMPLOG.csv') #Symlink TEMPLOG.csv auf die gerade zu benutzte eindeutige Log-Datei legen.
    kopfzeile='Datum_Uhrzeit' 
    for kanal in range(8):
        if (Logkanalnummer[kanal]):
            kopfzeile = kopfzeile + separator +  'Kanal ' + str(kanal)
    kopfzeile = kopfzeile +'\n'
     

    fw.write(kopfzeile) # Kopfzeile der CSV-Datei schreiben
    fw.close()

else:
    #Kein neues File anlegen
    if os.path.exists('/var/log/WLAN_Thermo/TEMPLOG.csv'): # pruefen, ob die Datei schon da ist zum anhaengen
         name = '/var/log/WLAN_Thermo/TEMPLOG.csv'
    else:
        # Datei noch nicht vorhanden, doch neu anlegen!
        fw = open(name,'w')
        os.symlink(name, '/var/log/WLAN_Thermo/TEMPLOG.csv')
        kopfzeile='Datum_Uhrzeit' 
        for kanal in range(8):
            if (Logkanalnummer[kanal]):
                kopfzeile = kopfzeile + separator +  'Kanal ' + str(kanal)
        kopfzeile = kopfzeile +'\n'
        fw.write(kopfzeile) # Kopfzeile der CSV-Datei schreiben
        fw.close()



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

    af = open("/var/www/temperaturen.csv") #Datei mit den Alarmwerten einlesen
    for i in range (8):
        Alarm_high[i] = int(af.readline())
    for i in range (8):
        Alarm_low[i] = int(af.readline())
    af.close() 

    for kanal in range (8): #Maximal 8 Kanaele abfragen, Kanal binaer mit den LED anzeigen gruen=1 gelb=2 rot=4.
        sensortyp = Sensornummer_typ[kanal] 
        Temp = 0
	gute = 0
        for i in range (iterations): #Anzahl iterations Werte messen und Durchschnitt bilden
            ADC_Channel = kanal
            Wert = 4096 - readAnalogData(ADC_Channel, SCLK, MOSI, MISO, CS)
	    # print kanal , Wert        
            if (Wert > 30) and (Sensornummer_typ[kanal]!='KTYPE'): #sinvoller Wertebereich
                Rtheta = messwiderstand*((4096.0/Wert) - 1)
                Tempvar = temperatur_sensor(Rtheta,sensortyp)
                if Tempvar <> 999.9: #normale Messung, keine Sensorprobleme
		    gute = gute + 1
                    Temp = Temp + Tempvar
                    Temperatur[kanal] = round(Temp/gute,2)
                else:
                    if gute==0:
		       Temperatur[kanal]  = 999.9 # Problem waehrend des Messzyklus aufgetreten, Errorwert setzen
            else:
                if Sensornummer_typ[kanal]=='KTYPE':
                    Temperatur[kanal] = Wert*330/4096
                else:
                    Temperatur[kanal] = 999.9 # kein sinnvoller Messwert, Errorwert setzen
	if gute <> iterations :
	   logger.warning('Kanal: ', str(kanal), ' konnte nur ', str(gute), ' von ', str(iterations), ' messen!!')  
        if Temperatur[kanal] <> 999.9:    
            Temperatur_string[kanal] = "%.1f" % Temperatur[kanal]
            Temperatur_alarm[kanal] = 'ok'
            if Temperatur[kanal] >= Alarm_high[kanal]:
                #Alarmstatus high aufdatieren
                Alarm_irgendwo = True
                Alarm_state_high_bin = Alarm_state_high_bin + pow(2, kanal)
                Alarm_message = Alarm_message + 'Kanal ' + str(kanal) + ' hat Uebertemperatur!\n'
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
        
        if Email_alert: #wenn konfiguriert, email schicken
            alarm_email(Email_server,Email_user,Email_password, Email_from, Email_to, Email_subject, Alarm_message)
            logger.debug('Alarmmail gesendet!')
        if PUSH:
            Alarm_message2 = urllib.quote(Alarm_message)
            push_cmd =  PUSH_URL.replace('messagetext', Alarm_message2.replace('\n', '<br/>'))
            push_cmd = 'wget -q -O - ' + push_cmd
            logger.debug(push_cmd)
            os.popen(push_cmd)
    
    Alarm_state_high_previous = Alarm_state_high_bin #aktuellen Alarm-Status sichern
    Alarm_state_low_previous = Alarm_state_low_bin   
    
    #Temperaturen fuer Display anzeige aufbereiten
    if LCD:
        for kanal in range(8):
            Displaytemp[kanal] = Temperatur_string[kanal]
    
    # Log datei erzeugen
    lt = time.localtime()#  Uhrzeit des Messzyklus
    jahr, monat, tag, stunde, minute, sekunde = lt[0:6]
    Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
    Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
    logdatei = os.readlink('/var/log/WLAN_Thermo/TEMPLOG.csv')
    logdatei = logdatei[21:-4]
    fcsv = open(current_temp,'w')
    lcsv = Uhrzeit_lang 
    t = ""
    for kanal in range(8):# eine Zeile mit allen Temperaturen
        lcsv = lcsv + ";" + str(Temperatur_string[kanal])
    for kanal in range(8):# eine Zeile mit allen alarm Temperaturen
        lcsv = lcsv + ";" + Temperatur_alarm[kanal]
    lcsv = lcsv + ";" + build + ";" + logdatei
    fcsv.write(lcsv)
    fcsv.close()
    
    # Generierung des Logfiles
    logfile = open(name,'a')#logfile oeffnen
    
    #Messzyklus protokollieren und nur die Kanaele loggen, die in der Konfigurationsdatei angegeben sind
    schreiben = Uhrzeit_lang
    for i in range(8):
       if (Logkanalnummer[i]):
          schreiben=schreiben + separator + str(Temperatur[i])
    logfile.write(schreiben + '\n')
    logfile.close()
    logger.debug(schreiben) # nur relevant wenn nicht als Dienst gestartet. Man sieht die aktuelle Logzeile
    
    time.sleep(delay) 

logger.info('WLANThermo stopped!')
