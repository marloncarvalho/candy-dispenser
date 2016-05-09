from twython import Twython
import sqlite3 as lite
import time
import threading


class Database:
    INSTANCE = None

    def __init__(self):
        self.con = lite.connect('tweets.db')
        self.cur = self.con.cursor()
        self.cur.executescript("""
            DROP TABLE IF EXISTS tweets;
            CREATE TABLE tweets(Id INT, text TEXT, user TEXT, sent INT);
            """)

    @classmethod
    def get_instance(cls):
        if cls.INSTANCE is None:
            cls.INSTANCE = Database()
        return cls.INSTANCE

    def get_cursor(self):
        return self.cur

    def close(self):
        self.con.close()


class Twitter(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.app_key = 'BLqRs3ajA0A621p1Yojo1gVFj'
        self.app_secret = 'A7Xa43LiJTaLvFVUVRRsm8yqF48sJd6RJ0kCUDOh8yJXTxyIjL'

        self.twitter = Twython(self.app_key, self.app_secret, oauth_version=2)
        self.twitter = Twython(self.app_secret, access_token=self.twitter.obtain_access_token())

    def run(self):
        self.get_tweets()

    def get_tweets(self):
        while True:
            result = self.twitter.search(q='#gdgssa', count=10)
            cur = Database.get_instance().get_cursor()
            for tweet in result['statuses']:
                cur.execute('SELECT count(*) as total FROM tweets WHERE id=' + str(tweet['id']))
                data = cur.fetchone()

                if data[0] <= 0:
                    cur.execute(
                        "INSERT INTO tweets (id, text, user, sent) values (" + str(tweet['id']) + ",'" + tweet['text'] + "','" +
                        tweet['user']['name'] + "', 0)")
            time.sleep(10)


class Servo(threading.Thread):

    def read_tweets(self):
        cur = Database.get_instance().get_cursor()
        cur.execute('SELECT * FROM tweets WHERE sent=0')
        return cur.fetchall()

    def feed(self):
        try:
            cur = Database.get_instance().get_cursor()
            while True:
                for row in self.read_tweets():
                    #open_candy_dispenser(row)
                    cur.execute("UPDATE tweets SET sent=1 WHERE id=" + str(row['id']))

                time.sleep(5)
        except lite.Error, e:
            print "Error %s:" % e.args[0]
        finally:
            Database.get_instance().close()


twitter = Twitter()
servo = Servo()

twitter.start()
servo.start()