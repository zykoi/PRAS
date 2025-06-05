from sqlalchemy import create_engine, Column, Integer, String, Float, Date, ForeignKey, Enum, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

Base = declarative_base()

class PropertyStatus(enum.Enum):
    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"

class ContractStatus(enum.Enum):
    ACTIVE = "active"
    TERMINATED = "terminated"
    EXPIRED = "expired"

class Property(Base):
    __tablename__ = 'properties'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    address = Column(String(200))
    area = Column(Float)
    floor = Column(Integer)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.AVAILABLE)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    contracts = relationship("Contract", back_populates="property")
    photos = relationship("PropertyPhoto", back_populates="property")
    inventory_items = relationship("InventoryItem", back_populates="property")
    maintenance_records = relationship("Maintenance", back_populates="property")

class PropertyPhoto(Base):
    __tablename__ = 'property_photos'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    file_path = Column(String(500))
    description = Column(String(200))
    is_main = Column(Integer, default=0)  # 0 - не главное, 1 - главное фото
    created_at = Column(DateTime, default=datetime.now)

    # Отношения
    property = relationship("Property", back_populates="photos")

class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    name = Column(String(100))
    description = Column(Text)
    quantity = Column(Integer)
    condition = Column(String(50))  # new, good, fair, poor
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    property = relationship("Property", back_populates="inventory_items")

class Tenant(Base):
    __tablename__ = 'tenants'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    legal_info = Column(String(200))  # ИНН, ОГРН и т.д.
    contact_info = Column(String(200))  # email, телефон
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    contracts = relationship("Contract", back_populates="tenant")

class Contract(Base):
    __tablename__ = 'contracts'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'), nullable=False)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    start_date = Column(Date)
    end_date = Column(Date, nullable=False)
    rent_amount = Column(Float, default=0.0)
    deposit = Column(Float, default=0.0)
    area = Column(Float)
    status = Column(Enum(ContractStatus), default=ContractStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    property = relationship("Property", back_populates="contracts")
    tenant = relationship("Tenant", back_populates="contracts")
    payments = relationship("Payment", back_populates="contract")
    documents = relationship("Document", back_populates="contract")

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    amount = Column(Float)
    due_date = Column(Date)
    payment_date = Column(Date)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    contract = relationship("Contract", back_populates="payments")

class Maintenance(Base):
    __tablename__ = 'maintenance'

    id = Column(Integer, primary_key=True)
    property_id = Column(Integer, ForeignKey('properties.id'))
    date = Column(Date)
    description = Column(Text)
    status = Column(String(20))  # planned, in_progress, completed
    cost = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    property = relationship("Property", back_populates="maintenance_records")

class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('contracts.id'))
    type = Column(String(50))  # contract, handover_act, reconciliation_act, termination_notice
    file_path = Column(String(500))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Отношения
    contract = relationship("Contract", back_populates="documents")

def init_db():
    engine = create_engine('sqlite:///rental.db')
    Base.metadata.create_all(engine)
    return engine

Session = sessionmaker() 