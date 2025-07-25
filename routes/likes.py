from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from bson import ObjectId
from typing import List, Optional
from database import likes
from routes.auth import get_current_user_from_cookie
import logging
from cachetools import TTLCache

likes_router = APIRouter()
cache = TTLCache(maxsize=100, ttl=60)
logger = logging.getLogger(__name__)

class LikeToggleRequest(BaseModel):
    item_id: str
    type: str
    
# Hàm tiện ích để convert ObjectId sang string
def convert_objectid_to_str(document):
    if not document:
        return document
    document["_id"] = str(document["_id"])
    if "user_id" in document:
        document["user_id"] = str(document["user_id"])
    if "item_id" in document:
        document["item_id"] = str(document["item_id"])
    return document

# GET: Lấy tất cả người đã like item
@likes_router.get("/likes")
async def get_users_liked(id: str):
    data = await likes.find({"item_id": ObjectId(id)}).to_list(length=None)
    # Chuyển đổi tất cả các ObjectId về string
    data = [convert_objectid_to_str(doc) for doc in data]
    return data

# GET: Kiểm tra user hiện tại đã like item chưa
@likes_router.get("/likes/user")
async def get_user_like(id: str, user_id: str = Depends(get_current_user_from_cookie)):
    like = await likes.find_one({"item_id": ObjectId(id), "user_id": ObjectId(user_id)})
    if like:
        like = convert_objectid_to_str(like)
    return like or {}

@likes_router.post("/likes/toggle")
async def toggle_like(data: LikeToggleRequest, user_id: str = Depends(get_current_user_from_cookie)):
    item_id = ObjectId(data.item_id)
    uid = ObjectId(user_id)
    like = await likes.find_one({"item_id": item_id, "user_id": uid})

    if like:
        if like["type"] == data.type:
            await likes.delete_one({"_id": like["_id"]})
            cache.pop(f"likes_{data.item_id}", None)
            count = await likes.count_documents({"item_id": item_id})
            return {"liked": False, "count": count}
        else:
            await likes.update_one({"_id": like["_id"]}, {"$set": {"type": data.type}})
            count = await likes.count_documents({"item_id": item_id})
            cache[f"likes_{data.item_id}"] = count
            return {"liked": True, "updated": True, "count": count}
    else:
        await likes.insert_one({"item_id": item_id, "user_id": uid, "type": data.type})
        count = await likes.count_documents({"item_id": item_id})
        cache[f"likes_{data.item_id}"] = count
        return {"liked": True, "new": True, "count": count}

@likes_router.post("/likes/batch-count")
async def batch_count(review_ids: List[str]):
    result, valid_ids, id_map = [], [], {}

    for r_id in set(review_ids):
        try:
            oid = ObjectId(r_id)
            id_map[str(oid)] = r_id
            if f"likes_{r_id}" in cache:
                result.append({"id": r_id, "count": cache[f"likes_{r_id}"]})
            else:
                valid_ids.append(oid)
        except Exception:
            result.append({"id": r_id, "count": 0})

    if valid_ids:
        pipeline = [
            {"$match": {"item_id": {"$in": valid_ids}}},
            {"$group": {"_id": "$item_id", "count": {"$sum": 1}}}
        ]
        counts = await likes.aggregate(pipeline).to_list(length=None)
        found = set()
        for c in counts:
            r_id = str(c["_id"])
            result.append({"id": id_map[r_id], "count": c["count"]})
            cache[f"likes_{id_map[r_id]}"] = c["count"]
            found.add(r_id)

        for oid in valid_ids:
            if str(oid) not in found:
                result.append({"id": id_map[str(oid)], "count": 0})
                cache[f"likes_{id_map[str(oid)]}"] = 0

    return result
