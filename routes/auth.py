from fastapi import APIRouter, HTTPException, Response, Depends, Cookie, status
from models.schemas import LoginModel, RegisterModel
from database import user
from auth import verify_password, get_password_hash, create_access_token
from jose import jwt, JWTError
from bson import ObjectId
from config import SECRET_KEY, ALGORITHM
import os

auth_router = APIRouter()

def get_current_user_from_cookie(token: str = Cookie(None)):
    if not token:
        print("Debug: Thiếu token trong cookie")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Không tìm thấy token trong cookie. Vui lòng đăng nhập."
        )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            print("Debug: Token không hợp lệ - không có user_id")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ. Vui lòng đăng nhập lại."
            )
        print(f"Debug: Token hợp lệ với user_id {user_id}")
        return user_id
    except JWTError as e:
        print(f"Debug: Lỗi JWT - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token đã hết hạn hoặc không hợp lệ. Vui lòng đăng nhập lại."
        )

# Đăng ký người dùng
@auth_router.post("/register")
async def register(data: RegisterModel):
    try:
        if await user.find_one({"email": data.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email đã tồn tại trong hệ thống"
            )
        hashed_pw = get_password_hash(data.password)
        result = await user.insert_one({
            "email": data.email,
            "password": hashed_pw,
            "username": data.username or "",
            "zone": "user"
        })
        print(f"Debug: Đăng ký thành công với email {data.email}")
        return {"message": "Đăng ký thành công!"}
    except Exception as e:
        print(f"Debug: Lỗi khi đăng ký - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi đăng ký: {str(e)}"
        )

# Đăng nhập
@auth_router.post("/login")
async def login(data: LoginModel, response: Response):
    try:
        u = await user.find_one({"email": data.email})
        if not u or not verify_password(data.password, u["password"]):
            print(f"Debug: Đăng nhập thất bại cho email {data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sai email hoặc mật khẩu"
            )
        token = create_access_token({
            "email": u["email"],
            "user_id": str(u["_id"]),
            "username": u.get("username", ""),
            "zone": u.get("zone", "user")
        })
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response.set_cookie(
            "token",
            token,
            httponly=True,
            secure=True,       # luôn bật nếu dùng HTTPS
            samesite="none",   # BẮT BUỘC khi FE/BE khác domain
            max_age=86400
        )
        print(f"Debug: Đã đặt cookie cho người dùng {u['email']} với token {token[:10]}...")
        return {"message": "Đăng nhập thành công", "token_type": "bearer"}
    except Exception as e:
        print(f"Debug: Lỗi khi đăng nhập - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi đăng nhập: {str(e)}"
        )

# Đăng xuất
@auth_router.post("/logout")
async def logout(response: Response):
    try:
        is_production = os.getenv("ENVIRONMENT", "development") == "production"
        response.delete_cookie(
            "token",
            httponly=True,
            secure=is_production,
            samesite="lax"
        )
        print("Debug: Đã xóa cookie token")
        return {"message": "Đăng xuất thành công"}
    except Exception as e:
        print(f"Debug: Lỗi khi đăng xuất - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi đăng xuất: {str(e)}"
        )

# Lấy thông tin người dùng
@auth_router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_from_cookie)):
    try:
        if not ObjectId.is_valid(user_id):
            print(f"Debug: user_id không hợp lệ - {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Mã người dùng không hợp lệ"
            )
        user_data = await user.find_one({"_id": ObjectId(user_id)})
        if not user_data:
            print(f"Debug: Không tìm thấy người dùng với user_id {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Không tìm thấy người dùng"
            )
        print(f"Debug: Lấy dữ liệu người dùng thành công cho user_id {user_id}")
        return {
            "username": user_data.get("username", ""),
            "zone": user_data.get("zone", "user")
        }
    except Exception as e:
        print(f"Debug: Lỗi khi lấy thông tin người dùng - {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi máy chủ khi lấy thông tin người dùng: {str(e)}"
        )
