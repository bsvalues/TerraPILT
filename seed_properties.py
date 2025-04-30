"""
Seed property data for the PILT Dashboard database.
"""
import os
import random
import logging
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, District, Property, LevyRate, Deduction

# Configure logging
logging.basicConfig(level=logging.INFO)
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

def seed_property_data(num_properties=100):
    """
    Seed the database with sample property data.
    
    Args:
        num_properties (int): Number of properties to create
    """
    try:
        # Connect to the database
        engine = create_engine(get_database_url())
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if properties already exist
        existing_properties = session.query(Property).count()
        if existing_properties > 0:
            logger.warning(f"Database already contains {existing_properties} properties.")
            confirm = input("Do you want to proceed and add more sample data? (y/N): ")
            if confirm.lower() != 'y':
                logger.info("Seed operation aborted.")
                session.close()
                return
        
        # Get all district IDs
        district_ids = [d.id for d in session.query(District).all()]
        if not district_ids:
            logger.error("No districts found in database. Please run migrations.py --seed first.")
            session.close()
            return
            
        # Create sample properties
        logger.info(f"Creating {num_properties} sample properties...")
        properties = []
        
        for i in range(1, num_properties + 1):
            # Assign to a random district
            district_id = random.choice(district_ids)
            
            # Generate a unique geo_id
            geo_id = f"GEO-{i}-{datetime.now().strftime('%Y%m%d')}"
            
            # Generate property values with realistic distributions
            assessed_value = random.uniform(50000, 2000000)  # Between $50k and $2M
            market_value = assessed_value * random.uniform(1.1, 1.5)  # Market value higher than assessed
            
            # Determine source as 'M' (market) or 'C' (calculated)
            market_value_source = 'M' if random.random() > 0.3 else 'C'
            
            # Generate size between 0.1 and 100 acres
            size_acres = random.uniform(0.1, 100)
            
            # Market value components
            land_segmented_market_value = market_value * random.uniform(0.2, 0.6)
            market_flat_value = market_value * random.uniform(0.05, 0.15)
            market_adjustment_value = market_value * random.uniform(-0.1, 0.1)
            
            # Agricultural value components (for some properties)
            has_ag = random.random() > 0.6  # 40% chance of having agricultural value
            
            if has_ag:
                ag_unit_price = random.uniform(100, 2000)
                ag_value = size_acres * ag_unit_price
                ag_adjustment_value = ag_value * random.uniform(-0.15, 0.15)
                ag_calculated_value = ag_value + ag_adjustment_value
                ag_flat_value = ag_value * random.uniform(0.05, 0.2)
                ag_value_source = 'M' if random.random() > 0.5 else 'C'
            else:
                ag_unit_price = None
                ag_value = None
                ag_adjustment_value = None
                ag_calculated_value = None
                ag_flat_value = None
                ag_value_source = None
            
            # Create property object
            property = Property(
                geo_id=geo_id,
                district_id=district_id,
                assessed_value=assessed_value,
                market_value=market_value,
                size_acres=size_acres,
                market_value_source=market_value_source,
                land_segmented_market_value=land_segmented_market_value,
                market_flat_value=market_flat_value,
                market_adjustment_value=market_adjustment_value,
                ag_unit_price=ag_unit_price,
                ag_value=ag_value,
                ag_adjustment_value=ag_adjustment_value,
                ag_calculated_value=ag_calculated_value,
                ag_flat_value=ag_flat_value,
                ag_value_source=ag_value_source,
                created_at=datetime.now().date()
            )
            properties.append(property)
        
        # Add all properties to the session
        session.add_all(properties)
        session.commit()
        logger.info(f"Successfully created {len(properties)} sample properties.")
        
        # Create some sample deductions
        logger.info("Creating sample deductions...")
        deductions = []
        
        for district_id in district_ids:
            # Current year deduction
            current_year = datetime.now().year
            deduction_amount = random.uniform(5000, 50000)
            deduction = Deduction(
                district_id=district_id,
                year=current_year,
                amount=deduction_amount,
                description=f"Standard deduction for district {district_id} in {current_year}",
                created_at=datetime.now().date()
            )
            deductions.append(deduction)
            
            # Previous year deduction
            prev_deduction_amount = random.uniform(4000, 45000)
            prev_deduction = Deduction(
                district_id=district_id,
                year=current_year - 1,
                amount=prev_deduction_amount,
                description=f"Standard deduction for district {district_id} in {current_year - 1}",
                created_at=datetime.now().date()
            )
            deductions.append(prev_deduction)
        
        session.add_all(deductions)
        session.commit()
        logger.info(f"Successfully created {len(deductions)} sample deductions.")
        
        session.close()
        return True
    except Exception as e:
        logger.error(f"Error seeding property data: {str(e)}")
        if 'session' in locals():
            session.rollback()
            session.close()
        return False

if __name__ == '__main__':
    seed_property_data(num_properties=100)