import pymysql
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
new_hash = pwd.hash("admin123")

conn = pymysql.connect(
    host="118.190.78.149",
    port=3306,
    user="bili_hot",
    password="rWW3WZTLYDM5886M",
    database="bili_hot",
    charset="utf8mb4",
)
cursor = conn.cursor()
cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (new_hash,))
conn.commit()
print("Admin password updated to: admin123")
cursor.close()
conn.close()