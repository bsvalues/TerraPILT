"""
Database migration utilities for PILT Dashboard.
This module provides functions to create and manage database tables.
"""
import argparse
import logging
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import Base, District, Property, LevyRate, Deduction

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_database_url():
    """Get database URL from environment variables."""
    if 'DATABASE_URL' in os.environ:
        return os.environ.get('DATABASE_URL')
    else:
        # Construct connection string from individual credentials
        user = os.environ.get('PGUSER', '')
        password = os.environ.get('PGPASSWORD', '')
        host = os.environ.get('PGHOST', '')
        port = os.environ.get('PGPORT', '5432')
        database = os.environ.get('PGDATABASE', '')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

def create_tables():
    """Create all tables defined in the models."""
    try:
        engine = create_engine(get_database_url())
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Check for existing tables
        model_tables = [
            District.__tablename__,
            Property.__tablename__,
            LevyRate.__tablename__,
            Deduction.__tablename__
        ]
        
        existing_model_tables = [t for t in model_tables if t in existing_tables]
        if existing_model_tables:
            logger.warning(f"Some tables already exist: {existing_model_tables}")
            confirm = input("Do you want to drop and recreate these tables? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Migration aborted.")
                return
        
        # Create tables
        logger.info("Creating tables...")
        Base.metadata.create_all(engine)
        logger.info("Tables created successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error creating tables: {str(e)}")
        return False

def drop_tables():
    """Drop all tables defined in the models."""
    try:
        engine = create_engine(get_database_url())
        confirm = input("Are you sure you want to drop all tables? This will delete all data. (y/N): ")
        if confirm.lower() != 'y':
            logger.info("Drop operation aborted.")
            return
        
        logger.info("Dropping tables...")
        Base.metadata.drop_all(engine)
        logger.info("Tables dropped successfully.")
        
        return True
    except Exception as e:
        logger.error(f"Error dropping tables: {str(e)}")
        return False

def seed_sample_data():
    """Seed the database with sample data."""
    try:
        engine = create_engine(get_database_url())
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if data already exists
        existing_districts = session.query(District).count()
        if existing_districts > 0:
            logger.warning(f"Database already contains {existing_districts} districts.")
            confirm = input("Do you want to proceed and add more sample data? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Seed operation aborted.")
                session.close()
                return
        
        # Create sample districts
        logger.info("Creating sample districts...")
        districts = [
            District(code='CE', name='Current Expense', description='County general fund'),
            District(code='CR', name='County Road', description='County road maintenance'),
            District(code='SS', name='State School', description='State school fund'),
            District(code='CY', name='City', description='City general fund')
        ]
        session.add_all(districts)
        session.commit()
        
        # Create sample levy rates
        logger.info("Creating sample levy rates...")
        current_year = 2025  # Example year
        levy_rates = [
            LevyRate(district_id=1, year=current_year, rate=0.9007089219),
            LevyRate(district_id=2, year=current_year, rate=1.2145630000),
            LevyRate(district_id=3, year=current_year, rate=0.8532140000),
            LevyRate(district_id=4, year=current_year, rate=1.4532650000)
        ]
        session.add_all(levy_rates)
        
        # Create historical levy rates
        for year in range(current_year-3, current_year):
            for district_id in range(1, 5):
                # Slightly vary the rates for historical data
                base_rate = levy_rates[district_id-1].rate
                historical_rate = base_rate * (0.9 + (year - (current_year-3)) * 0.05)
                session.add(LevyRate(district_id=district_id, year=year, rate=historical_rate))
        
        session.commit()
        logger.info("Sample data seeded successfully.")
        
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error seeding sample data: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(description='PILT Dashboard Database Migration Tool')
    parser.add_argument('--create', action='store_true', help='Create database tables')
    parser.add_argument('--drop', action='store_true', help='Drop database tables')
    parser.add_argument('--seed', action='store_true', help='Seed sample data')
    
    args = parser.parse_args()
    
    if args.drop:
        drop_tables()
    
    if args.create:
        create_tables()
    
    if args.seed:
        seed_sample_data()
    
    if not (args.create or args.drop or args.seed):
        parser.print_help()

if __name__ == '__main__':
    main()