from sqlalchemy.orm import declarative_base

Base = declarative_base()


from models.users import User, OTP, Address
from models.refresh_token import RefreshToken
from models.products import Product, ProductAnalytics, Category, SubCategory
from models.order import Order, Payment