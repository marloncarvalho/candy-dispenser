from twython import Twython
import sqlite3 as lite
import time
import threading
import RPi.GPIO as GPIO

con = lite.connect('tweets.db')
cur = con.cursor()
cur.executescript("""
            DROP TABLE IF EXISTS tweets;
            CREATE TABLE tweets(Id INT, text TEXT, user TEXT, sent INT);
            """)
con.close()

class TwitterFeeder(threading.Thread):
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
            result = self.twitter.search(q='#gdgssa', count=10)
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


class CandyDispenser(threading.Thread):
    """
    It's gonna open the dispenser when it finds a tweet.
    """
    
    def run(self):
        con = lite.connect('tweets.db')
        cur = con.cursor()
        try:
            while True:
                cur.execute('SELECT * FROM tweets WHERE sent=0')
                rows = cur.fetchall()
                    
                print("Buscando tweets")
                if(len(rows) > 0):
                    GPIO.setmode(GPIO.BOARD)
                    GPIO.setwarnings(False)
                    GPIO.setup(8, GPIO.OUT)
                    pwm = GPIO.PWM(8, 50)
                    pwm.start(12)                    
                    for row in rows:
                        print("Achou! Atualizando!")
                        self.open_candy_dispenser(row, pwm)
                        con.commit()
                    pwm.stop()
                time.sleep(10)
                                    
        except lite.Error, e:
            print "Error %s:" % e.args[0]
        finally:
            con.close()

    def open_candy_dispenser(self, row, pwm):
        print("Abrindo Dispenser - Mudando Ciclo")
        pwm.ChangeDutyCycle(2)
        time.sleep(5)
        pwm.ChangeDutyCycle(12)
        time.sleep(1)

twitter = TwitterFeeder()
dispenser = CandyDispenser()

twitter.start()
dispenser.start()
