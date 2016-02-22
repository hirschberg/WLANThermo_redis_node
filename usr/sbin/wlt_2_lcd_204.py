#!/usr/bin/python
import sys
import os
import time
import math
import string
import logging
import RPi.GPIO as GPIO




GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

HIGH = True  # HIGH-Pegel
LOW  = False # LOW-Pegel
# Variablendefinition und GPIO Pin-Definition
#GPIO START
LCD_RS      = 7  # RS-Leitung Display
LCD_E       = 8  # Enable-Leitung Display
LCD_D4      = 22 # Data-4 Display
LCD_D5      = 10 # Data-5 Display
LCD_D6      = 9  # Data-6 Display
LCD_D7      = 11 # Data-7 Display
#GPIO END

LCD_WIDTH = 20  # Maximum Zeichen pro Zeile
LCD_CHR = True  # Charakter/DATA an das Display
LCD_CMD = False # Kommando an das Display

LCD_LINE_1 = 0x80 # LCD RAM Adresse fuer die erste Zeile
LCD_LINE_2 = 0xC0 # LCD RAM Adresse fuer die zweite Zeile
LCD_LINE_3 = 0x94 # LCD RAM Adresse fuer die dritte Zeile
LCD_LINE_4 = 0xD4 # LCD RAM Adresse fuer die vierte Zeile 

# Timing Konstanten
E_PULSE = 0.0005
E_DELAY = 0.0005

counter = 0
#String Length
sLen = 6

#edit Felix
import redis
r = redis.StrictRedis(host='localhost', port=6379, db=0)

#end edit Felix

LOGFILE = r.hget('config:daemon_logging', 'file')
logger = logging.getLogger('WLANthermoDIS')
#Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL
level = logging.getLevelName(str(r.hget('config:daemon_logging', 'level_display')))
logger.setLevel(level)
handler = logging.FileHandler(LOGFILE)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

logger.info('Display Started!')
logger.info('REDIS started on display')


def lcd_init():  # Initialisierung Display und Definition Sonderzeichen Pfeil runter ASCII 0 und Pfeil hoch ASCII 1
  lcd_byte(0x33,LCD_CMD) # Noch im 8 Bit Modus also 30 30 
  lcd_byte(0x32,LCD_CMD) # 30 20 (30 = 8 Bit, 20 =4-Bit Modus)
  lcd_byte(0x28,LCD_CMD) # 4-Bit, 2-Zeilig, 5x8 Font
  lcd_byte(0x0C,LCD_CMD) # Display ein 
  
  lcd_byte(0x40,LCD_CMD) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x15,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x0E,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 0 definieren
  lcd_byte(0x00,LCD_CHR) # Sonderzeichen 0 definieren

  lcd_byte(0x48,LCD_CMD) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x0E,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x15,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x04,LCD_CHR) # Sonderzeichen 1 definieren
  lcd_byte(0x00,LCD_CHR) # Sonderzeichen 1 definieren


  lcd_byte(0x06,LCD_CMD) # Cursor nach rechts wandernd, kein Displayshift
  lcd_byte(0x01,LCD_CMD) # Display loeschen 
 
  

def lcd_string(message,style):
  # Sende String zum  Display
  # style=1 Linksbuendig
  # style=2 Zentriert
  # style=3 Rechtsbuendig

  if style==1:
    message = message.ljust(LCD_WIDTH," ")  
  elif style==2:
    message = message.center(LCD_WIDTH," ")
  elif style==3:
    message = message.rjust(LCD_WIDTH," ")

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

def lcd_byte(bits, mode):
  # Sende Byte an die Daten-Leitungen des Displays
  # bits = data
  # mode = True  fuer Zeichen
  #        False fuer Kommando

  GPIO.output(LCD_RS, mode) # RS

  # High Nibble uebertragen
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  time.sleep(E_DELAY)    
  GPIO.output(LCD_E, True)  
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)  
  time.sleep(E_DELAY)      

  # Low Nibble uebertragen
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  time.sleep(E_DELAY)    
  GPIO.output(LCD_E, True)  
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)  
  time.sleep(E_DELAY)   

def str_len(v,l,s):
    global error_val, sLen
    r = ''
    if (v == '999.9'):
        v = error_val.replace('"','')
    if (len(v) > l):
        r = v[:sLen]
    else:
        for char in range(l - len(v)):
            r = r + s
        r = r + v
    return r

#Tests whether wter is present.
# returns 0 for dry
# returns 1 for wet
# tested to work on pin 18 
def RCtime (RCpin):
    reading = 0
    GPIO.setup(RCpin, GPIO.OUT)
    GPIO.output(RCpin, GPIO.LOW)
    time.sleep(0.3) 
    GPIO.setup(RCpin, GPIO.IN)
    # This takes about 1 millisecond per loop cycle
    while True:
        if (GPIO.input(RCpin) == GPIO.LOW):
            reading += 1
        if reading >= 1000:
            return 0
        if (GPIO.input(RCpin) != GPIO.LOW):
            return 1



def show_values():
    global counter, sLen, curPath, curFile, pitFile, redisData


    rPubSub = redis.StrictRedis(host='localhost', port=6379, db=0)
    pubsub  = rPubSub.pubsub()
    pubsub.subscribe('temperatures')

    print 'monitoring channel temperatures'
    for m in pubsub.listen():
      redisData = str(m['data'])
      rd = redisData.split(';')
      print rd   
      if counter == 10:
        lcd_init()
        counter=0

         

      if len(rd) > 1:

        alarm = ['']
        for al in range (8):
          if al == 0:
            continue
          if float(rd[al]) == 999.9:
            alarm.append('')
          elif float(rd[al]) < float(r.hget('sensors:'+str(al), 'temp_min')):
            alarm.append(chr(0))
          elif float(rd[al]) > float(r.hget('sensors:'+str(al), 'temp_max')):
            alarm.append(chr(1))
          else:
            alarm.append('')

        lcd_byte(LCD_LINE_1, LCD_CMD)
        #print rd[1]
        #lcd_string('sag hallo'+str(rd[1]),2)
        lcd_string('C0:' +  str_len(alarm[0] + rd[1],sLen,' ') + chr(178) + 'C1:' + str_len(alarm[1] + rd[2],sLen,' ') + chr(178),2)
        print 'C0:' +  str_len(alarm[0] + rd[1],sLen,' ') + chr(178) + 'C1:' + str_len(alarm[1] + rd[2],sLen,' ') + chr(178)
        lcd_byte(LCD_LINE_2, LCD_CMD)
        #lcd_string('sag hallo'+str(counter+2),2)
        lcd_string('C2:' +  str_len(alarm[2] + rd[3],sLen,' ') + chr(178) + 'C3:' + str_len(alarm[3] + rd[4],sLen,' ') + chr(178),2)  
        lcd_byte(LCD_LINE_3, LCD_CMD)
        #lcd_string('sag hallo'+str(counter+3),2)
        lcd_string('C4:' +  str_len(alarm[4] + rd[5],sLen,' ') + chr(178) + 'C5:' + str_len(alarm[5] + rd[6],sLen,' ') + chr(178),2) 
        
        lcd_byte(LCD_LINE_4, LCD_CMD)
        # if (Config.getboolean('ToDo', 'pit_on')):
        #     if os.path.isfile(curPath + '/' + pitFile):
        #         logger.debug("Pitmaster laeuft, zeige die Daten in der 3. Zeile an")
        #         fp = open(curPath + '/' + pitFile).read()
        #         pits = fp.split(';')
        #         lcd_string('Pit: S:' + str("%.0f" % float(pits[1])) + ' I:' + str("%.0f" % float(pits[2])) + ' ' + pits[3],2)
        # else:
        #lcd_string('sag hallo'+str(counter+4),2)
        lcd_string('C6:' +  str_len(alarm[6] + rd[7],sLen,' ') + chr(178) + 'C7:' + str_len(alarm[7] + rd[8],sLen,' ') + chr(178),2)
      counter = counter + 1

      
      if RCtime(14) == 1:
        print "Sensor is wet"
      else:
        print 'Waiting for wetness...'
        print "Sensor is dry"

  



#Einlesen Displayeinstellungen
#edit Felix
#LCD = Config.getboolean('Display','lcd_present')
LCD = r.hget('config:display', 'active')


#Einlesen des gewuenschten Error value --> wenn ein unplausibler Messwert festgestellt wird wird statt dem Wert dieser String angezeigt
error_val = r.hget('config:display', 'error_val')

#Einlesen der Software-Version
build = r.hget('config:version', 'software')

if LCD:
    print "LCD init"
    GPIO.setup(LCD_E, GPIO.OUT)  # E
    GPIO.setup(LCD_RS, GPIO.OUT) # RS
    GPIO.setup(LCD_D4, GPIO.OUT) # DB4
    GPIO.setup(LCD_D5, GPIO.OUT) # DB5
    GPIO.setup(LCD_D6, GPIO.OUT) # DB6
    GPIO.setup(LCD_D7, GPIO.OUT) # DB7

    #Display initialisieren und Begruessungstext ausgeben
    lcd_init()
    lcd_byte(LCD_LINE_1, LCD_CMD)
    lcd_string("------8-Kanal-------",2) 
    lcd_byte(LCD_LINE_2, LCD_CMD)
    lcd_string("WLAN-Thermometer",2)
    lcd_byte(LCD_LINE_3, LCD_CMD)
    lcd_string("Armin Thinnes",2)
    lcd_byte(LCD_LINE_4, LCD_CMD)
    lcd_string(build,2)    

    time.sleep(3) # 3 second delay 

    lcd_init()
    lcd_byte(LCD_LINE_1, LCD_CMD)
    lcd_string("Grillsportverein",2)
    lcd_byte(LCD_LINE_2, LCD_CMD)
    lcd_string("WLAN-Thermometer",2)  
    lcd_byte(LCD_LINE_3, LCD_CMD)
    lcd_string("Die Referenz zum",2) 
    lcd_byte(LCD_LINE_4, LCD_CMD)
    lcd_string("Grillen und Messen!",2)   

    #time.sleep(3) # 3 second delay

    show_values()

logger.info('Display stopped!')
        
