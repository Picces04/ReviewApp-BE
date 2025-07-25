from pydantic import BaseModel, ConfigDict
from typing import Optional
import datetime

class LoginModel(BaseModel):
    email: str
    password: str

class RegisterModel(BaseModel):
    email: str
    password: str
    username: Optional[str] = ""

class Item(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    shop_name: str
    shop_address: str
    rating: int
    review: str
    image: str
    category: str
    timestamp: datetime.datetime

class ItemUpdate(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: Optional[str] = None
    shop_name: Optional[str] = None
    shop_address: Optional[str] = None
    rating: Optional[int] = None
    review: Optional[str] = None
    image: Optional[str] = None
    category: Optional[str] = None
    timestamp: Optional[datetime.datetime] = None

class DeleteImageModel(BaseModel):
    publicId: str
