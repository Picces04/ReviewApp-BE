from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.server_api import ServerApi
import logging
import certifi
from config import MONGODB_URI, MONGODB_DB_NAME

logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("motor").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING)

# Tạo client bất đồng bộ với cấu hình TLS
client = AsyncIOMotorClient(
    MONGODB_URI,
    server_api=ServerApi('1'),
    tls=True,  # Bật TLS/SSL
    tlsCAFile=certifi.where()  # Sử dụng chứng chỉ CA từ certifi
)

# Kết nối đến database
db = client.get_database(MONGODB_DB_NAME)

# Các collection
items = db.get_collection('items')
user = db.get_collection('user')
likes = db.get_collection('likes')
comments = db.get_collection('comments')

# Ping để kiểm tra kết nối
async def check_connection():
    try:
        await client.admin.command('ping')
        print("✅ Đã kết nối MongoDB Atlas thành công.")
    except Exception as e:
        print("❌ Kết nối thất bại:", e)

if __name__ == "__main__":
    import asyncio
    asyncio.run(check_connection())