import sqlite3
conn = sqlite3.connect('Database.db')
cursor = conn.cursor()


cursor.execute("DROP TABLE IF EXISTS messages")

conn.commit()
conn.close()



