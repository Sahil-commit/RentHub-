import pymysql

try:
    connection = pymysql.connect(host='localhost', user='root', password='')
    cursor = connection.cursor()
    cursor.execute("CREATE DATABASE IF NOT EXISTS renthub")
    print("Database 'renthub' created or already exists.")
    connection.close()
except pymysql.err.OperationalError as e:
    print(f"Could not connect to MySQL: {e}")
    print("WARNING: Using SQLite fallback since MySQL is not running on localhost:3306")
