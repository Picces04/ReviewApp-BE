from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.auth import auth_router
from routes.items import items_router
from routes.likes import likes_router
from routes.cloudinary_api import cloudinary_router
from config import FRONTEND_URL

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "https://review-app-fe.vercel.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(items_router)
app.include_router(likes_router)
app.include_router(cloudinary_router)

# Run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
