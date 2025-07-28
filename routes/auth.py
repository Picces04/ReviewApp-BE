from fastapi import APIRouter, HTTPException, Response, Depends, Cookie, status, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models.schemas import LoginModel, RegisterModel
from database import user
from auth import verify_password, get_password_hash, create_access_token
from jose import jwt, JWTError
from bson import ObjectId
from config import SECRET_KEY, ALGORITHM

# Khởi tạo APIRouter
auth_router = APIRouter()

# Hàm lấy user_id từ cookie
def get_current_user_from_cookie(token: str = Cookie(None)):
    if not token:
        print("Debug: Token missing in cookie") 
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            print("Debug: Invalid token - user_id not found")  
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError as e:
        print(f"Debug: JWTError - {str(e)}")  
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or invalid token")

# Endpoint đăng ký
@auth_router.post("/register")
async def register(data: RegisterModel):
    if await user.find_one({"email": data.email}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã tồn tại")
    hashed_pw = get_password_hash(data.password)
    result = await user.insert_one({
        "email": data.email,
        "password": hashed_pw,
        "username": data.username or "",
        "zone": "user"
    })
    print(f"Debug: Registered user with email {data.email}")  
    return {"message": "Đăng ký thành công!"}

# Endpoint đăng nhập
@auth_router.post("/login")
async def login(data: LoginModel, response: Response):
    u = await user.find_one({"email": data.email})
    if not u or not verify_password(data.password, u["password"]):
        print(f"Debug: Login failed for email {data.email}")  
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sai tài khoản hoặc mật khẩu")
    token = create_access_token({
        "email": u["email"],
        "user_id": str(u["_id"]),
        "username": u.get("username", ""),
        "zone": u.get("zone", "user")
    })
    response.set_cookie(
        "token",
        token,
        httponly=True,
        secure=False,  # Đặt secure=False nếu test trên localhost, đổi thành True trong production
        samesite="lax",  # Sử dụng lax để giảm hạn chế khi test
        max_age=86400
    )
    print(f"Debug: Set cookie for user {u['email']} with token {token[:10]}...")  
    return {"message": "Đăng nhập thành công", "token_type": "bearer"}

# Endpoint đăng xuất
@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        "token",
        httponly=True,
        secure=False,  # Đặt secure=False nếu test trên localhost, đổi thành True trong production
        samesite="lax"
    )
    print("Debug: Cookie token deleted") 
    return {"message": "Đăng xuất thành công"}

# Endpoint lấy thông tin người dùng
@auth_router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_from_cookie)):
    try:
        user_data = await user.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            print(f"Debug: User not found for user_id {user_id}")  
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy người dùng")
        print(f"Debug: Fetched user data for user_id {user_id}") 
        return {
            "username": user_data.get("username", ""),
            "zone": user_data.get("zone", "user")
        }
    except Exception as e:
        print(f"Debug: Error fetching user data - {str(e)}") 
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Lỗi server khi lấy thông tin người dùng")

