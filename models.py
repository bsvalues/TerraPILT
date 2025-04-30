"""
SQLAlchemy ORM models for PILT Dashboard.
This module defines the database schema and relationships.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class District(Base):
    """Tax district entity."""
    __tablename__ = 'districts'
    
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(Date, default=datetime.now().date())
    updated_at = Column(Date, onupdate=datetime.now().date())
    
    properties = relationship("Property", back_populates="district")
    levy_rates = relationship("LevyRate", back_populates="district")
    
    def __repr__(self):
        return f"<District(id={self.id}, code='{self.code}', name='{self.name}')>"

class Property(Base):
    """Property entity with tax assessment information."""
    __tablename__ = 'properties'
    
    id = Column(Integer, primary_key=True)
    geo_id = Column(String, unique=True, nullable=False)
    district_id = Column(Integer, ForeignKey('districts.id'), nullable=False)
    
    # Valuation fields
    assessed_value = Column(Float, nullable=False)
    market_value = Column(Float, nullable=True)
    size_acres = Column(Float, nullable=True)
    
    # Market value components
    market_value_source = Column(String(1), nullable=True)  # 'M' or 'C'
    land_segmented_market_value = Column(Float, nullable=True)
    market_flat_value = Column(Float, nullable=True)
    market_adjustment_value = Column(Float, nullable=True)
    
    # Agricultural value components
    ag_unit_price = Column(Float, nullable=True)
    ag_value = Column(Float, nullable=True)
    ag_adjustment_value = Column(Float, nullable=True)
    ag_calculated_value = Column(Float, nullable=True)
    ag_flat_value = Column(Float, nullable=True)
    ag_value_source = Column(String(1), nullable=True)  # 'M' or 'C'
    
    created_at = Column(Date, default=datetime.now().date())
    updated_at = Column(Date, onupdate=datetime.now().date())
    
    district = relationship("District", back_populates="properties")
    
    def __repr__(self):
        return f"<Property(id={self.id}, geo_id='{self.geo_id}', assessed_value={self.assessed_value})>"

class LevyRate(Base):
    """Levy rate by district and year."""
    __tablename__ = 'levy_rates'
    
    id = Column(Integer, primary_key=True)
    district_id = Column(Integer, ForeignKey('districts.id'), nullable=False)
    year = Column(Integer, nullable=False)
    rate = Column(Float, nullable=False)
    created_at = Column(Date, default=datetime.now().date())
    updated_at = Column(Date, onupdate=datetime.now().date())
    
    district = relationship("District", back_populates="levy_rates")
    
    __table_args__ = (
        UniqueConstraint('district_id', 'year', name='uix_levy_district_year'),
    )
    
    def __repr__(self):
        return f"<LevyRate(district_id={self.district_id}, year={self.year}, rate={self.rate})>"

class Deduction(Base):
    """Deductions applied to PILT calculations."""
    __tablename__ = 'deductions'
    
    id = Column(Integer, primary_key=True)
    district_id = Column(Integer, ForeignKey('districts.id'), nullable=False)
    year = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False, default=0.0)
    description = Column(String, nullable=True)
    created_at = Column(Date, default=datetime.now().date())
    updated_at = Column(Date, onupdate=datetime.now().date())
    
    __table_args__ = (
        UniqueConstraint('district_id', 'year', name='uix_deduction_district_year'),
    )
    
    def __repr__(self):
        return f"<Deduction(district_id={self.district_id}, year={self.year}, amount={self.amount})>"