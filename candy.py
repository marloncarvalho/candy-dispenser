from twython import Twython
import Adafruit_CharLCD as LCD
import socket
import os
import sqlite3 as lite
import time
import threading
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

con = lite.connect('tweets.db')
cur = con.cursor()
cur.executescript("""
            DROP TABLE IF EXISTS tweets;
            CREATE TABLE tweets(Id INT, text TEXT, user TEXT, sent INT);
            """)
con.close()

class Twitter(threading.Thread):
    """
    Alimenta o banco de dados de tweets com as mensagens com uma determinada hashtag.
    """
    
    def __init__(self):
        threading.Thread.__init__(self)
        self.app_key = 'BLqRs3ajA0A621p1Yojo1gVFj'
        self.app_secret = 'A7Xa43LiJTaLvFVUVRRsm8yqF48sJd6RJ0kCUDOh8yJXTxyIjL'

        self.twitter = Twython(self.app_key, self.app_secret, oauth_version=2)
        self.twitter = Twython(self.app_secret, access_token=self.twitter.obtain_access_token())

    def run(self):
        self.get_tweets()

    def get_tweets(self):
        con = lite.connect('tweets.db')
        cur = con.cursor()

        while True:
            result = self.twitter.search(q='#ecbahia', count=10)
            for tweet in result['statuses']:
                cur.execute('SELECT count(*) as total FROM tweets WHERE id=' + str(tweet['id']))
                data = cur.fetchone()

                if data[0] <= 0:
                    print("Gravando tweet de " + tweet["user"]["name"])
                    cur.execute(
                        "INSERT INTO tweets (id, text, user, sent) values (" + str(tweet['id']) + ",'" + tweet['text'] + "','" +
                        tweet['user']['name'] + "', 0)")
                    
            con.commit()
            time.sleep(10)

        con.close()


class Servo:

    def __init__(self):
        GPIO.setup(14, GPIO.OUT)

    def rotate(self):
        pwm = GPIO.PWM(14, 50)
        pwm.start(12)
        time.sleep(0.5)
        pwm.stop()

class LCDPower:
    lcd = None

    def __init__(self):
        lcd_rs        = 21
        lcd_en        = 20
        lcd_d4        = 26
        lcd_d5        = 19
        lcd_d6        = 13
        lcd_d7        = 6
        lcd_backlight = 4
        lcd_colunas = 16
        lcd_linhas  = 2
        self.lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5,
                           lcd_d6, lcd_d7, lcd_colunas, lcd_linhas,
                           lcd_backlight)
        self.lcd.clear()
        self.lcd.message('GDG Salvador\n')
        self.lcd.message('Use #TechTour\n')

    def message(self, message):
        self.lcd.message(message)

    def clear(self):
        self.lcd.clear()


class Ultrassonico:

    def __init__(self):
        self.GPIO_TRIGGER = 3
        self.GPIO_ECHO = 2
        GPIO.setup(self.GPIO_TRIGGER, GPIO.OUT)
        GPIO.setup(self.GPIO_ECHO, GPIO.IN)    
        
    def get_distance(self):
        try:
            distance = 100000.0
            while distance > 6:
                GPIO.output(self.GPIO_TRIGGER, False)
                time.sleep(1)
                GPIO.output(self.GPIO_TRIGGER,True) 
                time.sleep(0.00001)
                GPIO.output(self.GPIO_TRIGGER, False)
                start = time.time()            
                while GPIO.input(self.GPIO_ECHO)==0:
                    start = time.time()        
                while GPIO.input(self.GPIO_ECHO)==1:
                    stop = time.time()         
                elapsed = stop-start           
                distance = elapsed / 0.000058
                print("Distancia: " + str(distance))
                time.sleep(1)

            return distance
        except KeyboardInterrupt:             
            GPIO.cleanup()                    
        

        
class Dispenser(threading.Thread):
    servo = Servo()
    lcd = LCDPower()
    ultrassonico = Ultrassonico()
    
    def run(self):            
        con = lite.connect('tweets.db')
        cur = con.cursor()
        try:
            while True:
                print("Procurando Tweets no BD")
                cur.execute('SELECT user FROM tweets WHERE sent=0')
                rows = cur.fetchall()
                    
                if(len(rows) > 0):
                    for row in rows:
                        print("Achou um Tweet!")
                        self.lcd.clear()
                        self.lcd.message("Aproxime o copo:\n")
                        self.lcd.message(row[0])
                        self.ultrassonico.get_distance()
                        time.sleep(2)
                        self.servo.rotate()
                        time.sleep(5)
                        
                        # Falta colocar o update do banco de dados.
                        con.commit()
                self.lcd.message('GDG Salvador\n')
                self.lcd.message('Use #TechTour\n')
                time.sleep(10)
                                    
        except lite.Error, e:
            print "Error %s:" % e.args[0]
        finally:
            con.close()

twitter = Twitter()
dispenser = Dispenser()

twitter.start()
dispenser.start()
