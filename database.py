"""
Database module for SQL integration using SQLAlchemy.
This module handles connection to PostgreSQL database and data retrieval.
"""
import os
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

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
    Retrieve PILT data using a complex query that joins multiple tables.
    
    Returns:
        pd.DataFrame: PILT data for calculation
    """
    sql_query = """
    WITH CurrentYear AS (
        SELECT appr_yr AS current_year, appr_yr - 1 AS prev_year
        FROM pacs_oltp.dbo.pacs_system
    ),
    NonExemptProps AS (
        SELECT prop_id
        FROM property_exemption
        CROSS JOIN CurrentYear
        WHERE exmpt_tax_yr = prev_year
          AND exmpt_type_cd IN ('SNR/DSBL', 'EX')
    )
    SELECT DISTINCT
        pv.prop_id,
        p.geo_id,
        pv.assessed_val AS Assessed_Value,
        pv.market,
        'Current Expense' AS District,
        ld.size_acres,
        ld.mkt_val_source,
        ld.land_seg_mkt_val,
        ld.mkt_flat_val,
        ld.mkt_adj_val,
        ld.ag_unit_price,
        ld.ag_val,
        ld.ag_adj_val,
        ld.ag_calc_val,
        ld.ag_flat_val,
        ld.ag_val_source,
        0.9007089219 AS Levy_Rate  -- Example rate for Current Expense
    FROM property_val AS pv WITH (NOLOCK)
    INNER JOIN prop_supp_assoc AS psa WITH (NOLOCK)
        ON pv.prop_id = psa.prop_id
       AND pv.prop_val_yr = psa.owner_tax_yr
       AND pv.sup_num = psa.sup_num
    INNER JOIN property AS p WITH (NOLOCK)
        ON pv.prop_id = p.prop_id
    INNER JOIN land_detail AS ld WITH (NOLOCK)
        ON pv.prop_id = ld.prop_id
       AND pv.prop_val_yr = ld.prop_val_yr
       AND pv.sup_num = ld.sup_num
       AND ld.sale_id = 0
       AND ld.land_type_cd IN ('4', '41', '42', '45', '46', '47')
    CROSS JOIN (SELECT appr_yr AS current_year FROM pacs_oltp.dbo.pacs_system) CY
    WHERE pv.prop_val_yr = CY.current_year
      AND pv.prop_inactive_dt IS NULL
      AND pv.prop_id NOT IN (SELECT prop_id FROM NonExemptProps)
    ORDER BY p.geo_id;
    """
    
    try:
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
    # In a real scenario, you would adjust the query to retrieve historical data
    sql_query = f"""
    WITH years AS (
        SELECT generate_series(
            (SELECT appr_yr FROM pacs_oltp.dbo.pacs_system) - {years-1}, 
            (SELECT appr_yr FROM pacs_oltp.dbo.pacs_system), 
            1
        ) AS year
    )
    SELECT 
        y.year,
        SUM(pv.assessed_val) AS total_assessed_value,
        AVG(t.rate) AS avg_levy_rate
    FROM years y
    LEFT JOIN property_val pv ON pv.prop_val_yr = y.year
    LEFT JOIN tax_area t ON t.tax_yr = y.year
    GROUP BY y.year
    ORDER BY y.year;
    """
    
    try:
        return load_data(sql_query)
    except Exception as e:
        # If the historical query fails, create a message but don't crash the application
        st.warning(f"Unable to retrieve historical data: {str(e)}")
        # Return empty DataFrame with expected structure
        return pd.DataFrame(columns=['year', 'total_assessed_value', 'avg_levy_rate'])

def get_districts():
    """
    Get a list of all tax districts for filtering.
    
    Returns:
        pd.DataFrame: District information
    """
    sql_query = """
    SELECT DISTINCT district_name, district_code, levy_rate
    FROM tax_district
    ORDER BY district_name;
    """
    
    try:
        return load_data(sql_query)
    except Exception as e:
        # If districts query fails, return a default district dataframe
        default_districts = pd.DataFrame({
            'district_name': ['Current Expense'],
            'district_code': ['CE'],
            'levy_rate': [0.9007089219]
        })
        return default_districts
