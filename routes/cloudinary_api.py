from fastapi import APIRouter, HTTPException, Depends
from models.schemas import DeleteImageModel
import cloudinary.uploader
from routes.auth import get_current_user_from_cookie

cloudinary_router = APIRouter()

@cloudinary_router.post("/api/deleteImage")
async def delete_image(data: DeleteImageModel, user_id: str = Depends(get_current_user_from_cookie)):
    result = cloudinary.uploader.destroy(data.publicId)
    if result.get("result") == "ok":
        return {"message": "Xóa ảnh thành công"}
    raise HTTPException(status_code=400, detail="Không thể xóa ảnh")
