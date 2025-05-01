"""
Initialize the PILT Dashboard database.
This script creates necessary tables and seeds sample data.
"""
import logging
from migrations import create_tables, seed_sample_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize the database with tables and sample data."""
    logger.info("Initializing database...")
    
    # Create tables
    logger.info("Creating database tables...")
    if create_tables():
        logger.info("Tables created successfully.")
    else:
        logger.error("Failed to create tables. Database initialization stopped.")
        return False
    
    # Seed sample data
    logger.info("Seeding sample data...")
    if seed_sample_data(force_reseed=False):
        logger.info("Sample data seeded successfully.")
    else:
        logger.error("Failed to seed sample data.")
        return False
    
    logger.info("Database initialization completed successfully!")
    return True

if __name__ == "__main__":
    initialize_database()