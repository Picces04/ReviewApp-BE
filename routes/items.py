from fastapi import APIRouter, HTTPException, Depends, Query
from bson import ObjectId
from models.schemas import Item, ItemUpdate
from database import items
import json
from bson.json_util import dumps
from routes.auth import get_current_user_from_cookie

items_router = APIRouter()

@items_router.get("/allItems")
async def get_all_items(category: str = Query(None)):
    query = {"category": category} if category else {}
    result = await items.find(query).sort("timestamp", -1).to_list(length=None)
    return json.loads(dumps(result))

@items_router.get("/profile")
async def get_user_items(
    category: str = Query(None),
    user_id: str = Depends(get_current_user_from_cookie)
):
    query = {"user_id": user_id}
    if category:
        query["category"] = category
    items_data = await items.find(query).sort("timestamp", -1).to_list(length=None)
    return json.loads(dumps(items_data))

@items_router.post("/insertItems")
async def insert_item(data: Item, user_id: str = Depends(get_current_user_from_cookie)):
    item_data = data.model_dump()
    item_data["user_id"] = user_id
    result = await items.insert_one(item_data)
    return {"message": "Thêm thành công!", "id": str(result.inserted_id)}

@items_router.put("/updateItem/{item_id}")
async def update_item(item_id: str, data: ItemUpdate, user_id: str = Depends(get_current_user_from_cookie)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    result = await items.update_one(
        {"_id": ObjectId(item_id), "user_id": user_id},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Không tìm thấy item hoặc không có quyền")
    return {"message": "Cập nhật thành công"}

@items_router.delete("/deleteItem/{item_id}")
async def delete_item(item_id: str):
    result = await items.delete_one({"_id": ObjectId(item_id)})
    if result.deleted_count == 1:
        return {"message": "Xóa thành công"}
    raise HTTPException(status_code=404, detail="Không tìm thấy item")
