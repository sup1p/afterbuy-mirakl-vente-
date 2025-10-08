from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean(), default=False)
    
    uploaded_fabrics = relationship("UploadedFabric", back_populates="user")
    uploaded_eans = relationship("UploadedEan", back_populates="user")

class UploadedFabric(Base):
    __tablename__ = "uploaded_fabrics"
    id = Column(Integer, primary_key=True, index=True)
    afterbuy_fabric_id = Column(Integer, nullable=False)
    market = Column(String, nullable=False)  # "xl" "jv"
    status = Column(String, default="pending")  # pending, processed, error
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date_time = Column(DateTime, default=datetime.now(), nullable=False)

    user = relationship("User", back_populates="uploaded_fabrics")
    uploaded_eans = relationship("UploadedEan", back_populates="uploaded_fabric", cascade="all, delete-orphan")
    
class UploadedEan(Base):
    __tablename__ = "uploaded_eans"
    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String, nullable=False, index=True)
    afterbuy_fabric_id = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    image_1 = Column(String, nullable=False)  # URL
    image_2 = Column(String, nullable=False)  # URL
    image_3 = Column(String, nullable=False)  # URL
    
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_fabric_id = Column(Integer, ForeignKey("uploaded_fabrics.id"), nullable=False)
    
    status = Column(String, default="pending")  # pending, processed, error
    date_time = Column(DateTime, default=datetime.now(), nullable=False)

    user = relationship("User", back_populates="uploaded_eans")
    uploaded_fabric = relationship("UploadedFabric", back_populates="uploaded_eans")