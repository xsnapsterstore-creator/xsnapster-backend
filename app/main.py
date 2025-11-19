from fastapi import FastAPI
from db.base import Base
from db.session import db, get_db
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from api.routes.v1 import auth, products, users, category, address, order
from core.error_handlers import setup_exception_handlers


# db.create_tables()

app = FastAPI(
    title="xSnapster backend server",
    description="Backend APIs for ecommerce platform xSnapster",
    version="1.0.0",
)

setup_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(category.category_router)
app.include_router(category.subcategory_router)
app.include_router(address.router)
app.include_router(order.router)

@app.get("/", tags=["Root"])
def root():
    return {"message": "xSnapster API is running 🚀"}
