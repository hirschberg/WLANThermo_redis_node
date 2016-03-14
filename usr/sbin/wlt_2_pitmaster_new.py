#!/usr/bin/python
# coding=utf-8

# WLANThermo
# wlt_2_pitmaster.py - Sets pit temperature by controlling a fan, servo, heater or likely devices.
#
# Copyright (c) 2013, Joe16
# Copyright (c) 2015, Björn Schrader
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import ConfigParser
import os
import time
import math
import logging
import string
import pigpio
import threading
import signal
import redis

#redis connect
r = redis.StrictRedis(host='localhost', port=6379, db=0)

#GPIO START
PIT_PWM  = 4 # Pitmaster PWM

# Wir laufen als root, auch andere müssen die Config schreiben!
os.umask (0)

# Funktionsdefinition
class BBQpit:
    def __init__(self, logger):
        self.logger = logger
        self.pi = pigpio.pi()
        # self.Pit-Config
        self.pit_type = None
        self.pit_gpio = None
        
        # public
        self.pit_min = 50
        self.pit_max = 200
        self.pit_inverted = False
        
        self.pit_startup_min = 25
        self.pit_startup_threshold = 0
        self.pit_startup_time = 0.5
        
        # Steuergröße
        self.pit_out = None
        
        # Wave-ID
        self.fan_pwm = None
        
        self.pit_io_pwm_thread = None
        self.pit_io_pwm_on = 0
        self.pit_io_pwm_off = 0
        self.pit_io_pwm_lock = threading.Lock()
        self.pit_io_pwm_end = threading.Event()
        
        
    # Beendet eine Ausgabe
    def stop_pit(self):
        if self.pit_type == 'fan_pwm':
            # 25kHz PC-Lüfter
            self.pi.wave_tx_stop()
            # self.pi.wave_delete(self.fan_pwm) # Gives an Error
            self.pi.write(self.pit_gpio, 0)
        elif self.pit_type == 'fan':
            # Lüftersteuerung v3
            self.pi.set_PWM_dutycycle(self.pit_gpio, 0)
        elif self.pit_type == 'servo':
            # Servosteuerung (oder Lüfter über Fahrtenregler)
            self.pi.set_servo_pulsewidth(self.pit_gpio, 0)
        elif self.pit_type == 'io_pwm':
            # PWM-modulierter Schaltausgang (Schwingungspaketsteuerung)
            self.pit_io_pwm_end.set()
            self.pit_io_pwm_thread.join()
            self.pi.write(self.pit_gpio, 0)
        elif self.pit_type == 'io':
            # Schaltausgang
            self.pi.write(self.pit_gpio, 0)
        self.pit_type = None
    
    
    # Startet eine Ausgabe
    def start_pit(self, pit_type, gpio):
        self.logger.debug('Starte Pit ' + pit_type + ' auf GPIO' + str(gpio))
        if pit_type == 'fan_pwm':
            # 25kHz PC-Lüfter
            self.pi.set_mode(gpio, pigpio.OUTPUT)
            fan_pwm_pulses = []
            fan_pwm_pulses.append(pigpio.pulse(1<<gpio,0,1))
            fan_pwm_pulses.append(pigpio.pulse(0,1<<gpio,46))
            self.pi.wave_clear()
            self.pi.wave_add_generic(fan_pwm_pulses)
            self.fan_pwm = self.pi.wave_create()
            self.pi.wave_send_repeat(self.fan_pwm)
            self.pit_gpio = gpio
            self.pit_type = pit_type
        elif pit_type == 'fan':
            # Lüftersteuerung v3
            self.pi.set_mode(gpio, pigpio.OUTPUT)
            self.pi.set_PWM_frequency(gpio, 500)
            if not self.pit_inverted:
                self.pi.set_PWM_dutycycle(gpio, self.pit_min * 2.55)
            else:
                self.pi.set_PWM_dutycycle(gpio, self.pit_max * 2.55)
            self.pit_gpio = gpio
            self.pit_type = pit_type
        elif pit_type == 'servo':
            # Servosteuerung (oder Lüfter über Fahrtenregler)
            self.pi.set_mode(gpio, pigpio.OUTPUT)
            if not self.pit_inverted:
                self.pi.set_servo_pulsewidth(gpio, self.pit_min)
            else:
                self.pi.set_servo_pulsewidth(gpio, self.pit_max)
            self.pit_gpio = gpio
            self.pit_type = pit_type
        elif pit_type == 'io_pwm':
            # PWM-modulierter Schaltausgang (Schwingungspaketsteuerung)
            self.pi.set_mode(gpio, pigpio.OUTPUT)
            self.pit_io_pwm_end.clear()
            self.pit_io_pwm_thread = threading.Thread(target=self.io_pwm, args=(gpio,))
            self.pit_io_pwm_thread.daemon = True
            # Startwerte mitgeben (nicht 0/0 wg. CPU-Last)
            if not self.pit_inverted:
                self.pit_io_pwm_on = 1
                self.pit_io_pwm_off = 1
            else:
                self.pit_io_pwm_on = 1
                self.pit_io_pwm_off = 1
            self.pit_io_pwm_thread.start()
            self.pit_gpio = gpio
            self.pit_type = pit_type
        elif pit_type == 'io':
            self.pi.set_mode(gpio, pigpio.OUTPUT)
            # Schaltausgang
            if not self.pit_inverted:
                self.pi.write(gpio, 0)
            else:
                self.pi.write(gpio, 1)
            self.pit_gpio = gpio
            self.pit_type = pit_type
    
    
    def set_pit(self, control_out):
        self.logger.debug('Setze Pit auf ' + str(control_out) + '%')
        if control_out > 100:
            self.logger.info('Steuergröße über Maximum, begrenze auf 100%')
            control_out = 100
        elif control_out < 0:
            self.logger.info('Steuergröße unter Minimum, begrenze auf 0%')
            control_out = 0
            
        # Startup-Funktion für Lüfteranlauf, startet für 0,5s mit 25%
        if self.pit_type in ['fan_pwm', 'fan', 'servo'] and control_out > 0:
            # Auch bei Servo, falls noch jemand Lüfter an Fahrtenregler betreibt.
            if self.pit_out <= self.pit_startup_threshold and control_out < self.pit_startup_min:
                self.logger.info('Lüfteranlauf, 0,5s 25%')
                self.set_pit(self.pit_startup_min)
                time.sleep(self.pit_startup_time)
                self.pit_out = self.pit_startup_min
        
        if self.pit_type == 'fan_pwm':
            # 25kHz PC-Lüfter
            # Puls/ Pause berechnen
            pulselength = 47.0
            if not self.pit_inverted:
                if control_out < 0.1:
                # Zerocut
                    width = 0
                else:
                    width = int(round(self.pit_min + ((self.pit_max - self.pit_min) * (control_out / 100.0))) / (100 / (pulselength - 1)))
            else:
                width = int(round(self.pit_max - ((self.pit_max - self.pit_min) * (control_out / 100.0))) / (100 / (pulselength - 1)))
            # Ohne Impuls = 100%, daher minimum 1!
            width = width + 1
            pause = pulselength - width
            self.logger.debug('fan_pwm Pulsweite ' + str(width))
            # Wellenform generieren
            fan_pwm_pulses = []
            fan_pwm_pulses.append(pigpio.pulse(1<<self.pit_gpio,0,width))
            fan_pwm_pulses.append(pigpio.pulse(0,1<<self.pit_gpio,pause))
            self.pi.wave_clear()
            self.pi.wave_add_generic(fan_pwm_pulses)
            wave = self.pi.wave_create()
            # Neue Wellenform aktivieren, alte Löschen
            self.pi.wave_send_repeat(wave)
            self.pi.wave_delete(self.fan_pwm)
            self.fan_pwm = wave
        elif self.pit_type == 'fan':
            # Lüftersteuerung v3
            if not self.pit_inverted:
                if control_out < 0.1:
                # Zerocut
                    width = 0
                else:
                    width = int(round(self.pit_min + ((self.pit_max - self.pit_min) * (control_out / 100.0))) * 2.55)
            else:
                width = int(round(self.pit_max - ((self.pit_max - self.pit_min) * (control_out / 100.0))) * 2.55)
            self.pi.set_PWM_dutycycle(self.pit_gpio, width)
            self.logger.debug('fan PWM ' + str(width) + ' von 255')
        elif self.pit_type == 'servo':
            # Servosteuerung (oder Lüfter über Fahrtenregler)
            if not self.pit_inverted:
                width = self.pit_min + ((self.pit_max - self.pit_min) * (control_out / 100.0))
            else:
                width = self.pit_max - ((self.pit_max - self.pit_min) * (control_out / 100.0))
            self.pi.set_servo_pulsewidth(self.pit_gpio, width)
            self.logger.debug('servo Impulsbreite ' + str(width) + 'µs')
        elif self.pit_type == 'io_pwm':
            # PWM-modulierter Schaltausgang (Schwingungspaketsteuerung)
            # Zyklusdauer in s
            cycletime = 2
            width = (self.pit_min / 100.0 + ((self.pit_max - self.pit_min) / 100.0 * (control_out / 100.0))) * cycletime
            if not self.pit_inverted:
                on = width
                off = cycletime - width
            else:
                on = cycletime - width
                off = width
            with self.pit_io_pwm_lock:
                self.pit_io_pwm_on = on
                self.pit_io_pwm_off = off
            self.logger.debug('io_pwm Impulsbreite ' + str(on) + 's von ' + str(cycletime) + 's')
        elif self.pit_type == 'io':
            # Schaltausgang
            if control_out >= 50.0:
                # Einschalten
                self.logger.debug('io Schalte ein!')
                if not self.pit_inverted:
                    self.pi.write(self.pit_gpio, 1)
                else:
                    self.pi.write(self.pit_gpio, 0)
            else:
                # Ausschalten
                self.logger.debug('io Schalte aus')
                if not self.pit_inverted:
                    self.pi.write(self.pit_gpio, 0)
                else:
                    self.pi.write(self.pit_gpio, 1)
        self.pit_out = control_out
    
    
    def io_pwm(self, gpio):
        self.logger.debug('io_pwm - Starte Thread')
        while not self.pit_io_pwm_end.is_set():
            with self.pit_io_pwm_lock:
                on = self.pit_io_pwm_on
                off = self.pit_io_pwm_off
            if on > 0:
                self.pi.write(gpio, 1)
                time.sleep(on)
            if off > 0:
                self.pi.write(gpio, 0)
                time.sleep(off)
        self.logger.debug('io_pwm - Beende Thread')


def checkTemp(temp):
    r = 0
    try:
        r = float(temp)
    except ValueError:
        temp = temp[2:]
        r = float(temp)
    return r


def get_steps(steps_str):
    # Generiert aus einem durch Verkettungszeichen ("|") getrennten String
    # von durch Ausrufezeichen getrennten Wertepaaren eine Liste aus Tupeln
    
    steps = steps_str.split("|")
    
    retval = []
    for step in steps:
        step_fields = step.split("!")
        retval.append((step_fields[0], step_fields[1]))
    return retval


def main():
    
    last_pit = 0
    
    # Konfigurationsdatei einlesen
    defaults = {'pit_startup_min': '25', 'pit_startup_threshold': '0', 'pit_startup_time':'0.5', 'pit_io_gpio':'2'}
    #Config = ConfigParser.SafeConfigParser(defaults)
    #for i in range(0,5):
    #    while True:
    #        try:
    #            Config.read('/var/www/conf/WLANThermo.conf')
    #        except IndexError:
    #            time.sleep(1)
    #            continue
    #        break
    
    LOGFILE = r.hget('config:daemon_logging', 'file')
    HW = r.hget('config:version', 'hardware')


    logger = logging.getLogger('WLANthermoPIT')
    #Define Logging Level by changing >logger.setLevel(logging.LEVEL_YOU_WANT)< available: DEBUG, INFO, WARNING, ERROR, CRITICAL

    log_level = logging.getLevelName(str(r.hget('config:daemon_logging', 'level_pit')))
    logger.setLevel(level)

    handler = logging.FileHandler(LOGFILE)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
   
    logger.info('WLANThermoPID started')
   
    #GPIO END
    logger.info('Pitmaster Start')
   
    #Log Dateinamen aus der config lesen
    current_temp = Config.get('filepath','current_temp')
    pitmaster_log = Config.get('filepath','pitmaster')

    #Pfad aufsplitten
    pitPath,pitFile = os.path.split(pitmaster_log)

    pit_new = 0
    pit_val = 0
    #Wenn das display Verzeichniss im Ram Drive nicht exisitiert erstelle es

    if not os.path.exists(pitPath):
        os.makedirs(pitPath)

    count = 0

    #PID Begin Variablen fuer PID Regelung
    Iterm = 0
    pit_temp_last = 0
    pit_pid_max = 100
    pit_pid_min = 0
    pit_open_lid_detected = False
    pit_open_lid_ref_temp = [0.0,0.0,0.0,0.0,0.0]
    pit_open_lid_temp = 0
    pit_open_lid_count = 0
    #PID End Variablen fuer PID Regelung
    
    restart_pit = False
    pit_type = None
    pit_io_gpio = None
    pit_inverted = False
    
    bbqpit = BBQpit(logger)
    
    try:
        while True: #Regelschleife
            msg = ""
            #Aktuellen ist wert auslesen
            while True:
                try:
                    tl = open(current_temp, 'r')
                except IOError:
                    time.sleep(1)
                    continue
                break
            tline = tl.readline()
            if len(tline) > 5:
                logger.debug('Loading Configuration...')
                
                while True:
                    try:
                        Config.read('/var/www/conf/WLANThermo.conf')
                    except IndexError:
                        time.sleep(1)
                        continue
                    break
                
                pit_type_new = r.hget('config:pitmaster', 'type')
                pit_io_gpio_new = r.hget('config:pitmaster', 'io_gpio')
                
                if pit_type != pit_type_new:
                    logger.debug('Setting Pit type to: ' + pit_type_new)
                    if pit_type_new in ['io', 'io_pwm']:
                        # GPIO für IO aus der Config
                        logger.debug('Setting Pit IO GPIO to: ' + str(pit_io_gpio_new))
                        gpio = pit_io_gpio_new
                        pit_io_gpio = pit_io_gpio_new
                    else:
                        gpio = PIT_PWM
                    restart_pit = True
                
                if pit_io_gpio != pit_io_gpio_new:
                    # GPIO für IO geändert
                    logger.debug('Setting Pit IO GPIO to: ' + str(pit_io_gpio_new))
                    gpio = pit_io_gpio_new
                    restart_pit = True
                
                if pit_type_new in ['fan_pwm', 'fan', 'io_pwm']:
                    bbqpit.pit_min = r.hget('config:pitmaster', 'pwm_min')
                    bbqpit.pit_max = r.hget('config:pitmaster', 'pwm_max')
                else:
                    bbqpit.pit_min = r.hget('config:pitmaster', 'servo_min')
                    bbqpit.pit_max = r.hget('config:pitmaster', 'servo_max')
                    
                bbqpit.pit_startup_min = r.hget('config:pitmaster', 'startup_min')
                bbqpit.pit_startup_threshold = r.hget('config:pitmaster', 'startup_treshold')
                bbqpit.pit_startup_time = r.hget('config:pitmaster', 'startup_time')
                
                pit_inverted_new = r.hget('config:pitmaster', 'inverted')
                
                if bbqpit.pit_inverted != pit_inverted_new:
                    bbqpit.pit_inverted = pit_inverted_new
                
                if restart_pit:
                    logger.debug('Restarting Pit...')
                    pit_type = pit_type_new
                    pit_io_gpio = pit_io_gpio_new
                    bbqpit.stop_pit()
                    bbqpit.start_pit(pit_type, gpio)
                    restart_pit = False
                
                pit_steps = get_steps(r.hget('config:pitmaster', 'curve'))
                
                pit_set = r.hget('config:pitmaster', 'set')
                pit_ch = r.hget('config:pitmaster', 'ch')
                pit_pause = r.hget('config:pitmaster', 'pause')
                
                pit_man = r.hget('config:pitmaster', 'man')
                
                #PID Begin Parameter fuer PID einlesen
                pit_Kp = r.hget('config:pitmaster', 'kp')
                pit_Kd = r.hget('config:pitmaster', 'pwm_kd')
                pit_Ki = r.hget('config:pitmaster', 'ki')
                pit_Kp_a = r.hget('config:pitmaster', 'kp_a')
                pit_Kd_a = r.hget('config:pitmaster', 'kd_a')
                pit_Ki_a = r.hget('config:pitmaster', 'ki_a')
                pit_switch_a = r.hget('config:pitmaster', 'switch_a')
                controller_type = r.hget('config:pitmaster', 'controller_type')
                pit_iterm_min = r.hget('config:pitmaster', 'iterm_min')
                pit_iterm_max = r.hget('config:pitmaster', 'iterm_max')
                pit_open_lid_detection = r.hget('config:pitmaster', 'open_lid_detection')
                pit_open_lid_pause = r.hget('config:pitmaster', 'open_lid_pause')
                pit_open_lid_falling_border = r.hget('config:pitmaster', 'open_lid_falling_border')
                pit_open_lid_rising_border = r.hget('config:pitmaster', 'open_lid_rising_border')
                #PID End Paramter fuer PID einlesen
                
                if pit_man == 0:
                    temps = tline.split(";")
                    if temps[(pit_ch + 1)] == "Error":
                        logger.info('Kein Messwert auf Kanal ' + pit_ch)
                        msg = msg + '|Kein Temperaturfuehler an Kanal ' + pit_ch + ' angeschlossen!'
                    else:
                        pit_now = float(checkTemp(temps[(pit_ch + 1)]))
                        #start open lid detection
                        if pit_open_lid_detection:
                            pit_open_lid_ref_temp[0] = pit_open_lid_ref_temp[1]
                            pit_open_lid_ref_temp[1] = pit_open_lid_ref_temp[2]
                            pit_open_lid_ref_temp[2] = pit_open_lid_ref_temp[3]
                            pit_open_lid_ref_temp[3] = pit_open_lid_ref_temp[4]
                            pit_open_lid_ref_temp[4] = pit_now
                            temp_ref = (pit_open_lid_ref_temp[0]+pit_open_lid_ref_temp[1]+pit_open_lid_ref_temp[2]) / 3
                            
                            #erkennen ob Temperatur wieder eingependelt oder Timeout
                            if pit_open_lid_detected:
                                logger.info('Offener Deckel erkannt!')
                                pit_open_lid_count = pit_open_lid_count - 1  
                                if pit_open_lid_count <= 0:
                                    logger.info('Deckelöffnung: Timeout!')
                                    pit_open_lid_detected = False 
                                    msg = msg + '|Timeout open Lid detection '
                                elif pit_now > (pit_open_lid_temp * (pit_open_lid_rising_border / 100)):
                                    logger.info('Deckelöffnung: Deckel wieder geschlossen!')
                                    pit_open_lid_detected = False
                                    msg = msg + '|Lid closed '
                            elif pit_now < (temp_ref * (pit_open_lid_falling_border / 100)):
                                #Wenn Temp innerhalb der letzten beiden Messzyklen den falling Wert unterschreitet
                                logger.info('Deckelöffnung erkannt!')
                                pit_open_lid_detected = True
                                pit_new = 0
                                pit_open_lid_temp = pit_open_lid_ref_temp[0] #war bsiher pit_now, das ist aber schon zu niedrig
                                msg = msg + '|open Lid detected '
                                pit_open_lid_count = pit_open_lid_pause / pit_pause
                        else:
                            # Deckelerkennung nicht aktiv, Status zurücksetzen
                            pit_open_lid_detected = False
                        #end open lid detection
                        msg = msg + "|Ist: " + str(pit_now) + " Soll: " + str(pit_set)
                        calc = 0
                        s = 0
                        #Suchen und setzen des neuen Reglerwerts Wertekurve
                        if (controller_type == "False") and (not pit_open_lid_detected): #Bedingung fuer Wertekurve
                            for step, val in pit_steps:
                                if calc == 0:
                                    dif = pit_now - pit_set
                                    msg = msg + "|Dif: " + str(dif)
                                    if (dif <= float(step)):
                                        calc = 1
                                        msg = msg + "|Step: " + step
                                        pit_new = float(val)
                                        msg = msg + "|New: " + val
                                    if (pit_now >= pit_set):
                                        calc = 1
                                        pit_new = 0
                                        msg = msg +  "|New-overshoot: " + str(pit_new)
                                s = s + 1
                            if calc == 0:
                                msg = msg + "|Keine Regel zutreffend, Ausschalten!"
                                pit_new = 0
                        #PID Begin Block PID Regler Ausgang kann Werte zwischen 0 und 100% annehmen
                        elif (controller_type == "PID") and (not pit_open_lid_detected): #Bedingung fuer PID
                            dif = pit_set - pit_now
                            #Parameter in Abhaengigkeit der Temp setzen
                            if pit_now > (pit_switch_a / 100 * pit_set):
                                kp = pit_Kp
                                ki = pit_Ki
                                kd = pit_Kd
                            else:
                                kp = pit_Kp_a
                                ki = pit_Ki_a
                                kd = pit_Kd_a
                            #I-Anteil berechnen
                            Iterm = Iterm + (ki * float(dif))
                            #Anti-Windup I-Anteil
                            if Iterm > pit_iterm_max:
                                Iterm = pit_iterm_max
                            elif Iterm < pit_iterm_min:
                                Iterm = pit_iterm_min
                            #D-Anteil berechnen
                            dInput = pit_now - pit_temp_last
                            #PID Berechnung durchfuehren
                            pit_new  = kp * dif + Iterm - kd * dInput
                            msg = msg + "|PID Values P" + str(kp*dif) + " Iterm " + str(Iterm) + " dInput " + str(dInput)
                            #Stellwert begrenzen
                            if pit_new  > pit_pid_max:
                                pit_new  = pit_pid_max
                            elif pit_new  < pit_pid_min:
                                pit_new  = pit_pid_min
                            #Messwert Temperatur merken
                            pit_temp_last = pit_now
                            #PID End Block PID Regler
                            
                    
                    bbqpit.set_pit(pit_new)
                    msg += 'Neuer Wert: ' + str(pit_new)
                    
                    # Export das aktuellen Werte in eine Text datei
                    lt = time.localtime()#  Uhrzeit des Messzyklus
                    jahr, monat, tag, stunde, minute, sekunde = lt[0:6]
                    Uhrzeit = string.zfill(stunde,2) + ':' + string.zfill(minute,2)+ ':' + string.zfill(sekunde,2)
                    Uhrzeit_lang = string.zfill(tag,2) + '.' + string.zfill(monat,2) + '.' + string.zfill((jahr-2000),2) + ' ' + Uhrzeit
                    
                    while True:
                        try:          
                            fp = open(pitPath + '/' + pitFile + '_tmp', 'w')
                            # Schreibe mit Trennzeichen ; 
                            # Zeit;Soll;Ist;%;msg + pitFile,
                            fp.write(str(Uhrzeit_lang) + ';'+ str(pit_set) + ';' + str(pit_now) + ';' + str(pit_new) + '%;' + msg)
                            fp.flush()
                            os.fsync(fp.fileno())
                            fp.close()
                            os.rename(pitPath + '/' + pitFile + '_tmp', pitPath + '/' + pitFile)
                        except IndexError:
                            time.sleep(1)
                            continue
                        break
                    
                    if (Config.getboolean('ToDo', 'pit_on') == False):
                        if (count > 0):
                            break
                        count = 1
                else:
                    setPWM(pit_man)
            if len(msg) > 0:
                logger.debug(msg)
            time.sleep(pit_pause)
        
    except KeyboardInterrupt:
        pass
    bbqpit.stop_pit()
    try:
        os.unlink(pitPath + '/' + pitFile)
    except OSError:
        logger.debug('Fehler beim löschen der Pitmasterwerte')        
    logger.info('Shutting down WLANThermoPID')


def check_pid(pid):
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True


if __name__ == "__main__":
    pid = str(os.getpid())
    pidfilename = '/var/run/'+os.path.basename(__file__).split('.')[0]+'.pid'
    
    if os.access(pidfilename, os.F_OK):
        pidfile = open(pidfilename, "r")
        pidfile.seek(0)
        old_pid = int(pidfile.readline())
        if check_pid(old_pid):
            print("%s existiert, Prozess läuft bereits, beende Skript" % pidfilename)
            sys.exit()
        else:
            pidfile.seek(0)
            open(pidfilename, 'w').write(pid)
        
    else:
        open(pidfilename, 'w').write(pid)
    
    main()
    
    os.unlink(pidfilename)