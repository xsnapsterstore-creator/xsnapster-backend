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
    allow_origins=[
        "http://localhost:3000",
        "https://xsnapster.store",
        "https://www.xsnapster.store",
        "https://xsnapster.vercel.app",
        "https://dev.xsnapster.store",
        "http://localhost:4000",
        "http://72.61.225.41:3000"
    ],
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
