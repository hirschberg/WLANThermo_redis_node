#!/usr/bin/python
import time
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
lcd_string("V1",2)    

time.sleep(3) # 3 second delay 

lcd_byte(LCD_LINE_1, LCD_CMD)
lcd_string("Grillsportverein",2)
lcd_byte(LCD_LINE_2, LCD_CMD)
lcd_string("WLAN-Thermometer",2)  
lcd_byte(LCD_LINE_3, LCD_CMD)
lcd_string("Die Referenz zum",1) 
lcd_byte(LCD_LINE_4, LCD_CMD)
lcd_string("Grillen und Messen!",1)   

time.sleep(3) # 3 second delay
        
