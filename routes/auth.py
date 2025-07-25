from fastapi import APIRouter, HTTPException, Response, Depends, Cookie, status
from models.schemas import LoginModel, RegisterModel
from database import user
from auth import verify_password, get_password_hash, create_access_token
from jose import jwt, JWTError
from bson import ObjectId
from config import SECRET_KEY, ALGORITHM

auth_router = APIRouter()
\

def get_current_user_from_cookie(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Expired or invalid token")

@auth_router.post("/register")
async def register(data: RegisterModel):
    if await user.find_one({"email": data.email}):
        raise HTTPException(status_code=400, detail="Email đã tồn tại")
    hashed_pw = get_password_hash(data.password)
    await user.insert_one({
        "email": data.email,
        "password": hashed_pw,
        "username": data.username or "",
        "zone": "user"
    })
    return {"message": "Đăng ký thành công!"}

@auth_router.post("/login")
async def login(data: LoginModel, response: Response):
    u = await user.find_one({"email": data.email})
    if not u or not verify_password(data.password, u["password"]):
        raise HTTPException(status_code=400, detail="Sai tài khoản hoặc mật khẩu")
    token = create_access_token({
        "email": u["email"],
        "user_id": str(u["_id"]),
        "username": u.get("username", ""),
        "zone": u.get("zone", "user")
    })
    response.set_cookie("token", token, httponly=True, secure=True, samesite="strict", max_age=86400)
    return {"message": "Đăng nhập thành công", "token_type": "bearer"}

@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("token", httponly=True, secure=True, samesite="strict")
    return {"message": "Đăng xuất thành công"}

@auth_router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_from_cookie)):
    user_data = await user.find_one({"_id": ObjectId(user_id)})
    if not user_data:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")
    return {
        "username": user_data.get("username", ""),
        "zone": user_data.get("zone", "user")
    }
