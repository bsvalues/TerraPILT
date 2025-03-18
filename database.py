"""
Database module for SQL integration using SQLAlchemy.
This module handles connection to PostgreSQL database and data retrieval.
"""
import os
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
from datetime import datetime

def get_database_connection():
    """
    Create a database connection using environment variables.
    Returns SQLAlchemy engine object.
    """
    try:
        # Using environment variables for secure credential storage
        if 'DATABASE_URL' in os.environ:
            database_url = os.environ.get('DATABASE_URL')
        else:
            # Construct connection string from individual credentials
            user = os.environ.get('PGUSER', '')
            password = os.environ.get('PGPASSWORD', '')
            host = os.environ.get('PGHOST', '')
            port = os.environ.get('PGPORT', '5432')
            database = os.environ.get('PGDATABASE', '')
            
            database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        
        engine = create_engine(database_url)
        return engine
    except Exception as e:
        raise ConnectionError(f"Failed to establish database connection: {str(e)}")

def load_data(query: str) -> pd.DataFrame:
    """
    Execute the provided SQL query and return the result as a pandas DataFrame.
    
    Args:
        query (str): SQL query to execute
        
    Returns:
        pd.DataFrame: Query results as a DataFrame
        
    Raises:
        Exception: If query execution fails
    """
    try:
        engine = get_database_connection()
        with engine.connect() as connection:
            df = pd.read_sql(query, connection)
        return df
    except ConnectionError as e:
        # Re-raise connection errors to be handled by the caller
        raise e
    except Exception as e:
        raise Exception(f"Error executing query: {str(e)}")

def get_pilt_data():
    """
    Retrieve PILT data for PILT calculations.
    
    Returns:
        pd.DataFrame: PILT data for calculation
    """
    try:
        # Generate sample PILT data for demonstration
        # This is a simplified version that works with PostgreSQL
        sql_query = """
        SELECT 
            generate_series(1, 100) AS prop_id,
            'GEO-' || generate_series(1, 100) AS geo_id,
            (random() * 1000000)::numeric(15,2) AS "Assessed_Value",
            (random() * 1500000)::numeric(15,2) AS market,
            CASE 
                WHEN generate_series(1, 100) % 4 = 0 THEN 'Current Expense'
                WHEN generate_series(1, 100) % 4 = 1 THEN 'County Road'
                WHEN generate_series(1, 100) % 4 = 2 THEN 'State School'
                ELSE 'City'
            END AS "District",
            (random() * 100)::numeric(10,4) AS size_acres,
            CASE WHEN random() > 0.5 THEN 'M' ELSE 'C' END AS mkt_val_source,
            (random() * 500000)::numeric(15,2) AS land_seg_mkt_val,
            (random() * 10000)::numeric(15,2) AS mkt_flat_val,
            (random() * 50000)::numeric(15,2) AS mkt_adj_val,
            (random() * 1000)::numeric(10,2) AS ag_unit_price,
            (random() * 200000)::numeric(15,2) AS ag_val,
            (random() * 20000)::numeric(15,2) AS ag_adj_val,
            (random() * 200000)::numeric(15,2) AS ag_calc_val,
            (random() * 10000)::numeric(15,2) AS ag_flat_val,
            CASE WHEN random() > 0.5 THEN 'M' ELSE 'C' END AS ag_val_source,
            CASE 
                WHEN generate_series(1, 100) % 4 = 0 THEN 0.9007089219 
                WHEN generate_series(1, 100) % 4 = 1 THEN 1.2145630000
                WHEN generate_series(1, 100) % 4 = 2 THEN 0.8532140000
                ELSE 1.4532650000
            END AS "Levy_Rate"
        """
        return load_data(sql_query)
    except Exception as e:
        raise Exception(f"Failed to retrieve PILT data: {str(e)}")

def get_historical_pilt_data(years=4):
    """
    Retrieve historical PILT data for trend analysis.
    
    Args:
        years (int): Number of years of historical data to retrieve
        
    Returns:
        pd.DataFrame: Historical PILT data for visualization
    """
    # This is a simplified query for demonstration
    try:
        # Generate historical data for the current year and previous years
        current_year = datetime.now().year
        sql_query = f"""
        SELECT 
            generate_series({current_year-years+1}, {current_year}, 1) AS year,
            (random() * 70000000 + 30000000)::numeric(15,2) * 
              (1 + (generate_series(0, {years-1}, 1)::float/20)) AS total_assessed_value,
            (random() * 0.3 + 0.8)::numeric(5,4) * 
              (1 + (generate_series(0, {years-1}, 1)::float/50)) AS avg_levy_rate
        """
        return load_data(sql_query)
    except Exception as e:
        # If the historical query fails, create a message but don't crash the application
        st.warning(f"Unable to retrieve historical data: {str(e)}")
        # Create sample historical data
        import pandas as pd
        from datetime import datetime
        
        current_year = datetime.now().year
        years_list = list(range(current_year-years+1, current_year+1))
        
        return pd.DataFrame({
            'year': years_list,
            'total_assessed_value': [50000000 * (1 + i*0.05) for i in range(years)],
            'avg_levy_rate': [0.95 * (1 + i*0.02) for i in range(years)]
        })

def get_districts():
    """
    Get a list of all tax districts for filtering.
    
    Returns:
        pd.DataFrame: District information
    """
    try:
        # Generate sample districts
        sql_query = """
        SELECT 
            CASE 
                WHEN generate_series(1, 4) = 1 THEN 'Current Expense'
                WHEN generate_series(1, 4) = 2 THEN 'County Road'
                WHEN generate_series(1, 4) = 3 THEN 'State School'
                ELSE 'City'
            END AS district_name,
            CASE 
                WHEN generate_series(1, 4) = 1 THEN 'CE'
                WHEN generate_series(1, 4) = 2 THEN 'CR'
                WHEN generate_series(1, 4) = 3 THEN 'SS'
                ELSE 'CY'
            END AS district_code,
            CASE 
                WHEN generate_series(1, 4) = 1 THEN 0.9007089219 
                WHEN generate_series(1, 4) = 2 THEN 1.2145630000
                WHEN generate_series(1, 4) = 3 THEN 0.8532140000
                ELSE 1.4532650000
            END AS levy_rate
        """
        return load_data(sql_query)
    except Exception as e:
        # If districts query fails, return a default district dataframe
        districts = pd.DataFrame({
            'district_name': ['Current Expense', 'County Road', 'State School', 'City'],
            'district_code': ['CE', 'CR', 'SS', 'CY'],
            'levy_rate': [0.9007089219, 1.2145630000, 0.8532140000, 1.4532650000]
        })
        return districts
