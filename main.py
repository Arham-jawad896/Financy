import pymysql
import cryptography

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="defaultdb",
    host="mysql-2893971a-jawadarham896-a2c4.i.aivencloud.com",
    password="************************",
    read_timeout=timeout,
    port=19023,
    user="avnadmin",
    write_timeout=timeout,
)

try:
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE mytest (id INTEGER PRIMARY KEY)")
    cursor.execute("INSERT INTO mytest (id) VALUES (1), (2)")
    cursor.execute("SELECT * FROM mytest")
    print(cursor.fetchall())
finally:
    connection.close()