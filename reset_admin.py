import pymysql
import bcrypt

new_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="root123456",
    database="mydb",
    charset="utf8mb4",
)
cursor = conn.cursor()
cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
print("Admin password updated to: admin123")
cursor.close()
conn.close()