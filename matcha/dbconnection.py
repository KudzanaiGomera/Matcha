import mysql.connector as mysql

db = mysql.connect(
    host = '127.0.0.1',
    user = 'root',
    passwd = ''
    )

if(db):
    print('Connected successful....')

else:
    print('Connection unsuccessful')

cursor = db.cursor()

# creating a databse called 'matcha'
cursor.execute("CREATE DATABASE IF NOT EXISTS matcha")