from email.policy import default
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """
    Модель пользователя.
    Хранит данные о пользователях, включая имя, хэшированный пароль и статус администратора.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор пользователя
    username = Column(String, unique=True, index=True, nullable=False)  # Уникальное имя пользователя
    hashed_password = Column(String, nullable=False)  # Хэшированный пароль
    is_admin = Column(Boolean(), default=False)  # Флаг, указывающий, является ли пользователь администратором

    # Связь с загруженными тканями
    uploaded_fabrics = relationship("UploadedFabric", back_populates="user")
    # Связь с загруженными EAN-кодами
    uploaded_eans = relationship("UploadedEan", back_populates="user")

class UploadedFabric(Base):
    """
    Модель загруженной ткани.
    Хранит данные о загруженных тканях, включая идентификатор, статус и связь с пользователем.
    """
    __tablename__ = "uploaded_fabrics"
    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор записи
    afterbuy_fabric_id = Column(Integer, nullable=False)  # Идентификатор ткани в системе Afterbuy
    market = Column(String, nullable=False)  # Рынок, например, "xl" или "jv"
    shop = Column(String, default="vente", nullable=False)  # Магазин, например, "vente" или "xxxlutz"
    status = Column(String, default="pending")  # Статус обработки: pending, processed, error
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Связь с пользователем
    date_time = Column(DateTime, default=datetime.now(), nullable=False)  # Дата и время загрузки

    # Связь с пользователем
    user = relationship("User", back_populates="uploaded_fabrics")
    # Связь с загруженными EAN-кодами
    uploaded_eans = relationship("UploadedEan", back_populates="uploaded_fabric", cascade="all, delete-orphan")

class UploadedEan(Base):
    """
    Модель загруженного EAN-кода.
    Хранит данные о загруженных EAN-кодах, включая изображения, статус и связь с тканью.
    """
    __tablename__ = "uploaded_eans"
    id = Column(Integer, primary_key=True, index=True)  # Уникальный идентификатор записи
    ean = Column(String, nullable=False, index=True)  # EAN-код
    afterbuy_fabric_id = Column(Integer, nullable=False)  # Идентификатор ткани в системе Afterbuy
    title = Column(String, nullable=False)  # Название продукта
    image_1 = Column(String, nullable=False)  # URL первого изображения
    image_2 = Column(String, nullable=False)  # URL второго изображения
    image_3 = Column(String, nullable=False)  # URL третьего изображения

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Связь с пользователем
    uploaded_fabric_id = Column(Integer, ForeignKey("uploaded_fabrics.id"), nullable=False)  # Связь с тканью

    status = Column(String, default="pending")  # Статус обработки: pending, processed, error
    date_time = Column(DateTime, default=datetime.now(), nullable=False)  # Дата и время загрузки

    # Связь с пользователем
    user = relationship("User", back_populates="uploaded_eans")
    # Связь с тканью
    uploaded_fabric = relationship("UploadedFabric", back_populates="uploaded_eans")