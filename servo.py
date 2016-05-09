import sqlite3 as lite
import time

def open_candy_dispenser(row):
    return row

try:
    con = lite.connect('tweets.db')

    cur = con.cursor()
    while True:
        cur.execute('SELECT * FROM tweets WHERE sent=0')
        rows = cur.fetchall()
        for row in rows:
            open_candy_dispenser(row)
            cur.execute("UPDATE tweets SET sent=1 WHERE id=" + str(row['id']))

        time.sleep(5)

except lite.Error, e:
    print "Error %s:" % e.args[0]
finally:
    if con:
        con.close()
