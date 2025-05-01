"""
Data import module for PILT Dashboard.
This module handles importing data from Excel and CSV files into the database.
"""
import os
import logging
import pandas as pd
import numpy as np
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Tuple, Optional, Any, Union

from database import get_engine
from models import Base, District, Property, LevyRate, Deduction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_from_excel(
    file_path: str, 
    district_sheet: str = "Districts", 
    property_sheet: str = "Properties",
    levy_rate_sheet: str = "LevyRates",
    deduction_sheet: str = "Deductions",
    year: int = 2025,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Import data from Excel file into the database.
    
    Args:
        file_path (str): Path to Excel file
        district_sheet (str): Name of sheet containing district data
        property_sheet (str): Name of sheet containing property data
        levy_rate_sheet (str): Name of sheet containing levy rate data
        deduction_sheet (str): Name of sheet containing deduction data
        year (int): Default year for levy rates and deductions if not specified in the file
        clear_existing (bool): Whether to clear existing data before import
        
    Returns:
        Dict[str, Any]: Results with counts of imported records and any errors
    """
    results = {
        "success": True,
        "districts_imported": 0,
        "properties_imported": 0,
        "levy_rates_imported": 0, 
        "deductions_imported": 0,
        "errors": [],
        "warnings": []
    }
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Process districts
        try:
            district_df = pd.read_excel(file_path, sheet_name=district_sheet)
            if clear_existing:
                logger.warning("Clearing existing data before import")
                # Delete in reverse order of dependencies
                session.query(LevyRate).delete()
                session.query(Deduction).delete()
                session.query(Property).delete()
                session.query(District).delete()
                session.commit()
                
            # Check required columns
            required_district_columns = ['code', 'name']
            missing_columns = [col for col in required_district_columns if col not in district_df.columns]
            if missing_columns:
                error = f"Missing required columns in district sheet: {missing_columns}"
                results["errors"].append(error)
                logger.error(error)
            else:
                # Clean data - handle NaNs, etc.
                district_df = district_df.replace({np.nan: None})
                
                # Create district lookup dictionary for references
                district_lookup = {}
                
                # Import districts
                for _, row in district_df.iterrows():
                    try:
                        # Check if district already exists
                        existing_district = session.query(District).filter_by(code=row['code']).first()
                        if existing_district and not clear_existing:
                            district_lookup[row['code']] = existing_district.id
                            warning = f"District with code '{row['code']}' already exists, skipping."
                            results["warnings"].append(warning)
                            logger.warning(warning)
                            continue
                            
                        # Create new district
                        district = District(
                            code=row['code'],
                            name=row['name'],
                            description=row.get('description')
                        )
                        session.add(district)
                        session.flush()  # Flush to get the ID
                        district_lookup[row['code']] = district.id
                        results["districts_imported"] += 1
                    except Exception as e:
                        error = f"Error importing district {row.get('code', 'unknown')}: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                session.commit()
                logger.info(f"Imported {results['districts_imported']} districts")
                
                # Process levy rates if available
                try:
                    levy_rate_df = pd.read_excel(file_path, sheet_name=levy_rate_sheet)
                    
                    # Check required columns
                    required_levy_columns = ['district_code', 'rate']
                    missing_columns = [col for col in required_levy_columns if col not in levy_rate_df.columns]
                    if missing_columns:
                        warning = f"Missing required columns in levy rate sheet: {missing_columns}"
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        # Clean data
                        levy_rate_df = levy_rate_df.replace({np.nan: None})
                        
                        # Import levy rates
                        for _, row in levy_rate_df.iterrows():
                            try:
                                district_code = row['district_code']
                                if district_code not in district_lookup:
                                    warning = f"District code '{district_code}' not found for levy rate, skipping."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    continue
                                    
                                # Get or set year
                                levy_year = row.get('year', year)
                                
                                # Check if levy rate already exists
                                existing_levy = session.query(LevyRate).filter_by(
                                    district_id=district_lookup[district_code],
                                    year=levy_year
                                ).first()
                                
                                if existing_levy and not clear_existing:
                                    warning = f"Levy rate for district '{district_code}', year {levy_year} already exists, updating."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    existing_levy.rate = row['rate']
                                else:
                                    # Create new levy rate
                                    levy_rate = LevyRate(
                                        district_id=district_lookup[district_code],
                                        year=levy_year,
                                        rate=row['rate']
                                    )
                                    session.add(levy_rate)
                                
                                results["levy_rates_imported"] += 1
                            except Exception as e:
                                error = f"Error importing levy rate: {str(e)}"
                                results["errors"].append(error)
                                logger.error(error)
                        
                        session.commit()
                        logger.info(f"Imported {results['levy_rates_imported']} levy rates")
                
                except Exception as e:
                    if "No sheet named" in str(e):
                        warning = f"Levy rate sheet '{levy_rate_sheet}' not found, skipping."
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        error = f"Error processing levy rates: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                # Process deductions if available
                try:
                    deduction_df = pd.read_excel(file_path, sheet_name=deduction_sheet)
                    
                    # Check required columns
                    required_deduction_columns = ['district_code', 'amount']
                    missing_columns = [col for col in required_deduction_columns if col not in deduction_df.columns]
                    if missing_columns:
                        warning = f"Missing required columns in deduction sheet: {missing_columns}"
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        # Clean data
                        deduction_df = deduction_df.replace({np.nan: None})
                        
                        # Import deductions
                        for _, row in deduction_df.iterrows():
                            try:
                                district_code = row['district_code']
                                if district_code not in district_lookup:
                                    warning = f"District code '{district_code}' not found for deduction, skipping."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    continue
                                    
                                # Get or set year
                                deduction_year = row.get('year', year)
                                
                                # Check if deduction already exists
                                existing_deduction = session.query(Deduction).filter_by(
                                    district_id=district_lookup[district_code],
                                    year=deduction_year
                                ).first()
                                
                                if existing_deduction and not clear_existing:
                                    warning = f"Deduction for district '{district_code}', year {deduction_year} already exists, updating."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    existing_deduction.amount = row['amount']
                                    existing_deduction.description = row.get('description')
                                else:
                                    # Create new deduction
                                    deduction = Deduction(
                                        district_id=district_lookup[district_code],
                                        year=deduction_year,
                                        amount=row['amount'],
                                        description=row.get('description')
                                    )
                                    session.add(deduction)
                                
                                results["deductions_imported"] += 1
                            except Exception as e:
                                error = f"Error importing deduction: {str(e)}"
                                results["errors"].append(error)
                                logger.error(error)
                        
                        session.commit()
                        logger.info(f"Imported {results['deductions_imported']} deductions")
                
                except Exception as e:
                    if "No sheet named" in str(e):
                        warning = f"Deduction sheet '{deduction_sheet}' not found, skipping."
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        error = f"Error processing deductions: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                # Process properties if available
                try:
                    property_df = pd.read_excel(file_path, sheet_name=property_sheet)
                    
                    # Check required columns
                    required_property_columns = ['district_code', 'geo_id', 'assessed_value']
                    missing_columns = [col for col in required_property_columns if col not in property_df.columns]
                    if missing_columns:
                        warning = f"Missing required columns in property sheet: {missing_columns}"
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        # Clean data
                        property_df = property_df.replace({np.nan: None})
                        
                        # Import properties
                        for _, row in property_df.iterrows():
                            try:
                                district_code = row['district_code']
                                if district_code not in district_lookup:
                                    warning = f"District code '{district_code}' not found for property, skipping."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    continue
                                    
                                # Check if property already exists
                                existing_property = session.query(Property).filter_by(
                                    geo_id=row['geo_id']
                                ).first()
                                
                                if existing_property and not clear_existing:
                                    warning = f"Property with geo_id '{row['geo_id']}' already exists, updating."
                                    results["warnings"].append(warning)
                                    logger.warning(warning)
                                    
                                    # Update existing property
                                    existing_property.district_id = district_lookup[district_code]
                                    existing_property.assessed_value = row['assessed_value']
                                    existing_property.market_value = row.get('market_value')
                                    existing_property.size_acres = row.get('size_acres')
                                else:
                                    # Create new property
                                    property = Property(
                                        geo_id=row['geo_id'],
                                        district_id=district_lookup[district_code],
                                        assessed_value=row['assessed_value'],
                                        market_value=row.get('market_value'),
                                        size_acres=row.get('size_acres')
                                    )
                                    session.add(property)
                                
                                results["properties_imported"] += 1
                            except Exception as e:
                                error = f"Error importing property {row.get('geo_id', 'unknown')}: {str(e)}"
                                results["errors"].append(error)
                                logger.error(error)
                        
                        session.commit()
                        logger.info(f"Imported {results['properties_imported']} properties")
                
                except Exception as e:
                    if "No sheet named" in str(e):
                        warning = f"Property sheet '{property_sheet}' not found, skipping."
                        results["warnings"].append(warning)
                        logger.warning(warning)
                    else:
                        error = f"Error processing properties: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
        
        except Exception as e:
            if "No sheet named" in str(e):
                error = f"District sheet '{district_sheet}' not found. Import failed."
                results["errors"].append(error)
                logger.error(error)
            else:
                error = f"Error processing districts: {str(e)}"
                results["errors"].append(error)
                logger.error(error)
            
            results["success"] = False
            
    except Exception as e:
        error = f"Error during import: {str(e)}"
        results["errors"].append(error)
        logger.error(error)
        results["success"] = False
        
        # Make sure to close session
        if 'session' in locals():
            session.close()
            
    return results


def import_from_csv(
    district_file: str,
    property_file: Optional[str] = None,
    levy_rate_file: Optional[str] = None,
    deduction_file: Optional[str] = None,
    year: int = 2025,
    clear_existing: bool = False
) -> Dict[str, Any]:
    """
    Import data from CSV files into the database.
    
    Args:
        district_file (str): Path to CSV file containing district data
        property_file (str, optional): Path to CSV file containing property data
        levy_rate_file (str, optional): Path to CSV file containing levy rate data
        deduction_file (str, optional): Path to CSV file containing deduction data
        year (int): Default year for levy rates and deductions if not specified in the files
        clear_existing (bool): Whether to clear existing data before import
        
    Returns:
        Dict[str, Any]: Results with counts of imported records and any errors
    """
    results = {
        "success": True,
        "districts_imported": 0,
        "properties_imported": 0,
        "levy_rates_imported": 0, 
        "deductions_imported": 0,
        "errors": [],
        "warnings": []
    }
    
    try:
        engine = get_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Process districts
        try:
            district_df = pd.read_csv(district_file)
            if clear_existing:
                logger.warning("Clearing existing data before import")
                # Delete in reverse order of dependencies
                session.query(LevyRate).delete()
                session.query(Deduction).delete()
                session.query(Property).delete()
                session.query(District).delete()
                session.commit()
                
            # Check required columns
            required_district_columns = ['code', 'name']
            missing_columns = [col for col in required_district_columns if col not in district_df.columns]
            if missing_columns:
                error = f"Missing required columns in district file: {missing_columns}"
                results["errors"].append(error)
                logger.error(error)
            else:
                # Clean data - handle NaNs, etc.
                district_df = district_df.replace({np.nan: None})
                
                # Create district lookup dictionary for references
                district_lookup = {}
                
                # Import districts
                for _, row in district_df.iterrows():
                    try:
                        # Check if district already exists
                        existing_district = session.query(District).filter_by(code=row['code']).first()
                        if existing_district and not clear_existing:
                            district_lookup[row['code']] = existing_district.id
                            warning = f"District with code '{row['code']}' already exists, skipping."
                            results["warnings"].append(warning)
                            logger.warning(warning)
                            continue
                            
                        # Create new district
                        district = District(
                            code=row['code'],
                            name=row['name'],
                            description=row.get('description')
                        )
                        session.add(district)
                        session.flush()  # Flush to get the ID
                        district_lookup[row['code']] = district.id
                        results["districts_imported"] += 1
                    except Exception as e:
                        error = f"Error importing district {row.get('code', 'unknown')}: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                session.commit()
                logger.info(f"Imported {results['districts_imported']} districts")
                
                # Process levy rates if available
                if levy_rate_file:
                    try:
                        levy_rate_df = pd.read_csv(levy_rate_file)
                        
                        # Check required columns
                        required_levy_columns = ['district_code', 'rate']
                        missing_columns = [col for col in required_levy_columns if col not in levy_rate_df.columns]
                        if missing_columns:
                            warning = f"Missing required columns in levy rate file: {missing_columns}"
                            results["warnings"].append(warning)
                            logger.warning(warning)
                        else:
                            # Clean data
                            levy_rate_df = levy_rate_df.replace({np.nan: None})
                            
                            # Import levy rates
                            for _, row in levy_rate_df.iterrows():
                                try:
                                    district_code = row['district_code']
                                    if district_code not in district_lookup:
                                        warning = f"District code '{district_code}' not found for levy rate, skipping."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        continue
                                        
                                    # Get or set year
                                    levy_year = row.get('year', year)
                                    
                                    # Check if levy rate already exists
                                    existing_levy = session.query(LevyRate).filter_by(
                                        district_id=district_lookup[district_code],
                                        year=levy_year
                                    ).first()
                                    
                                    if existing_levy and not clear_existing:
                                        warning = f"Levy rate for district '{district_code}', year {levy_year} already exists, updating."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        existing_levy.rate = row['rate']
                                    else:
                                        # Create new levy rate
                                        levy_rate = LevyRate(
                                            district_id=district_lookup[district_code],
                                            year=levy_year,
                                            rate=row['rate']
                                        )
                                        session.add(levy_rate)
                                    
                                    results["levy_rates_imported"] += 1
                                except Exception as e:
                                    error = f"Error importing levy rate: {str(e)}"
                                    results["errors"].append(error)
                                    logger.error(error)
                            
                            session.commit()
                            logger.info(f"Imported {results['levy_rates_imported']} levy rates")
                    
                    except Exception as e:
                        error = f"Error processing levy rates: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                # Process deductions if available
                if deduction_file:
                    try:
                        deduction_df = pd.read_csv(deduction_file)
                        
                        # Check required columns
                        required_deduction_columns = ['district_code', 'amount']
                        missing_columns = [col for col in required_deduction_columns if col not in deduction_df.columns]
                        if missing_columns:
                            warning = f"Missing required columns in deduction file: {missing_columns}"
                            results["warnings"].append(warning)
                            logger.warning(warning)
                        else:
                            # Clean data
                            deduction_df = deduction_df.replace({np.nan: None})
                            
                            # Import deductions
                            for _, row in deduction_df.iterrows():
                                try:
                                    district_code = row['district_code']
                                    if district_code not in district_lookup:
                                        warning = f"District code '{district_code}' not found for deduction, skipping."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        continue
                                        
                                    # Get or set year
                                    deduction_year = row.get('year', year)
                                    
                                    # Check if deduction already exists
                                    existing_deduction = session.query(Deduction).filter_by(
                                        district_id=district_lookup[district_code],
                                        year=deduction_year
                                    ).first()
                                    
                                    if existing_deduction and not clear_existing:
                                        warning = f"Deduction for district '{district_code}', year {deduction_year} already exists, updating."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        existing_deduction.amount = row['amount']
                                        existing_deduction.description = row.get('description')
                                    else:
                                        # Create new deduction
                                        deduction = Deduction(
                                            district_id=district_lookup[district_code],
                                            year=deduction_year,
                                            amount=row['amount'],
                                            description=row.get('description')
                                        )
                                        session.add(deduction)
                                    
                                    results["deductions_imported"] += 1
                                except Exception as e:
                                    error = f"Error importing deduction: {str(e)}"
                                    results["errors"].append(error)
                                    logger.error(error)
                            
                            session.commit()
                            logger.info(f"Imported {results['deductions_imported']} deductions")
                    
                    except Exception as e:
                        error = f"Error processing deductions: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
                
                # Process properties if available
                if property_file:
                    try:
                        property_df = pd.read_csv(property_file)
                        
                        # Check required columns
                        required_property_columns = ['district_code', 'geo_id', 'assessed_value']
                        missing_columns = [col for col in required_property_columns if col not in property_df.columns]
                        if missing_columns:
                            warning = f"Missing required columns in property file: {missing_columns}"
                            results["warnings"].append(warning)
                            logger.warning(warning)
                        else:
                            # Clean data
                            property_df = property_df.replace({np.nan: None})
                            
                            # Import properties
                            for _, row in property_df.iterrows():
                                try:
                                    district_code = row['district_code']
                                    if district_code not in district_lookup:
                                        warning = f"District code '{district_code}' not found for property, skipping."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        continue
                                        
                                    # Check if property already exists
                                    existing_property = session.query(Property).filter_by(
                                        geo_id=row['geo_id']
                                    ).first()
                                    
                                    if existing_property and not clear_existing:
                                        warning = f"Property with geo_id '{row['geo_id']}' already exists, updating."
                                        results["warnings"].append(warning)
                                        logger.warning(warning)
                                        
                                        # Update existing property
                                        existing_property.district_id = district_lookup[district_code]
                                        existing_property.assessed_value = row['assessed_value']
                                        existing_property.market_value = row.get('market_value')
                                        existing_property.size_acres = row.get('size_acres')
                                    else:
                                        # Create new property
                                        property = Property(
                                            geo_id=row['geo_id'],
                                            district_id=district_lookup[district_code],
                                            assessed_value=row['assessed_value'],
                                            market_value=row.get('market_value'),
                                            size_acres=row.get('size_acres')
                                        )
                                        session.add(property)
                                    
                                    results["properties_imported"] += 1
                                except Exception as e:
                                    error = f"Error importing property {row.get('geo_id', 'unknown')}: {str(e)}"
                                    results["errors"].append(error)
                                    logger.error(error)
                            
                            session.commit()
                            logger.info(f"Imported {results['properties_imported']} properties")
                    
                    except Exception as e:
                        error = f"Error processing properties: {str(e)}"
                        results["errors"].append(error)
                        logger.error(error)
        
        except Exception as e:
            error = f"Error processing districts: {str(e)}"
            results["errors"].append(error)
            logger.error(error)
            
            results["success"] = False
            
    except Exception as e:
        error = f"Error during import: {str(e)}"
        results["errors"].append(error)
        logger.error(error)
        results["success"] = False
        
        # Make sure to close session
        if 'session' in locals():
            session.close()
            
    return results


def create_sample_excel_template(output_path: str) -> bool:
    """
    Create a sample Excel template with the correct format for data import.
    
    Args:
        output_path (str): Path to save the Excel template
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create a pandas Excel writer
        with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
            # Districts sheet
            districts_df = pd.DataFrame({
                'code': ['CE', 'CR', 'SS', 'CY'],
                'name': ['Current Expense', 'County Road', 'State School', 'City'],
                'description': ['County general fund', 'County road maintenance', 
                                'State school fund', 'City general fund']
            })
            districts_df.to_excel(writer, sheet_name='Districts', index=False)
            
            # Levy rates sheet
            levy_rates_df = pd.DataFrame({
                'district_code': ['CE', 'CR', 'SS', 'CY'],
                'year': [2025, 2025, 2025, 2025],
                'rate': [0.9007089219, 1.2145630000, 0.8532140000, 1.4532650000]
            })
            levy_rates_df.to_excel(writer, sheet_name='LevyRates', index=False)
            
            # Deductions sheet
            deductions_df = pd.DataFrame({
                'district_code': ['CE', 'CR', 'SS', 'CY'],
                'year': [2025, 2025, 2025, 2025],
                'amount': [25000, 15000, 10000, 5000],
                'description': ['Standard deduction', 'Road maintenance credit', 
                               'Education credit', 'Municipal services credit']
            })
            deductions_df.to_excel(writer, sheet_name='Deductions', index=False)
            
            # Properties sheet (sample with 5 properties)
            properties_df = pd.DataFrame({
                'district_code': ['CE', 'CE', 'CR', 'SS', 'CY'],
                'geo_id': ['GEO-1-1', 'GEO-1-2', 'GEO-2-1', 'GEO-3-1', 'GEO-4-1'],
                'assessed_value': [1250000, 950000, 1450000, 2100000, 1750000],
                'market_value': [1500000, 1100000, 1700000, 2300000, 1900000],
                'size_acres': [25.5, 15.2, 40.7, 80.3, 30.9]
            })
            properties_df.to_excel(writer, sheet_name='Properties', index=False)
            
            # Documentation sheet
            documentation = [
                ['PILT Data Import Template', ''],
                ['', ''],
                ['This Excel file contains templates for importing data into the PILT Dashboard.', ''],
                ['', ''],
                ['Sheets:', ''],
                ['Districts', 'Required - Contains tax district information'],
                ['Properties', 'Contains property data with assessed values'],
                ['LevyRates', 'Contains levy rates by district and year'],
                ['Deductions', 'Contains deductions by district and year'],
                ['', ''],
                ['Required columns for each sheet:', ''],
                ['Districts:', 'code, name'],
                ['Properties:', 'district_code, geo_id, assessed_value'],
                ['LevyRates:', 'district_code, rate'],
                ['Deductions:', 'district_code, amount'],
                ['', ''],
                ['Notes:', ''],
                ['- The district_code in Properties, LevyRates, and Deductions must match a code in the Districts sheet', ''],
                ['- If year is not specified in LevyRates or Deductions, the current year will be used', ''],
                ['- All monetary values should be entered as numbers without currency symbols or commas', '']
            ]
            docs_df = pd.DataFrame(documentation)
            docs_df.to_excel(writer, sheet_name='Documentation', index=False, header=False)
            
            # Get the xlsxwriter workbook and worksheet objects
            workbook = writer.book
            
            # Add formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4B8BBE',
                'font_color': 'white',
                'border': 1
            })
            
            # Format the header rows in each sheet
            for sheet_name in ['Districts', 'Properties', 'LevyRates', 'Deductions']:
                worksheet = writer.sheets[sheet_name]
                for col_num, value in enumerate(pd.DataFrame(writer.sheets[sheet_name].get_header_row()).iloc[0]):
                    worksheet.write(0, col_num, value, header_format)
                    worksheet.set_column(col_num, col_num, 15)
            
            # Format the documentation sheet
            doc_worksheet = writer.sheets['Documentation']
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 14,
                'font_color': '#4B8BBE'
            })
            doc_worksheet.write('A1', 'PILT Data Import Template', title_format)
            doc_worksheet.set_column('A:A', 40)
            doc_worksheet.set_column('B:B', 60)
        
        logger.info(f"Sample Excel template created at {output_path}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating Excel template: {str(e)}")
        return False


def create_sample_csv_templates(output_dir: str) -> bool:
    """
    Create sample CSV templates with the correct format for data import.
    
    Args:
        output_dir (str): Directory to save the CSV templates
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        # Districts CSV
        districts_df = pd.DataFrame({
            'code': ['CE', 'CR', 'SS', 'CY'],
            'name': ['Current Expense', 'County Road', 'State School', 'City'],
            'description': ['County general fund', 'County road maintenance', 
                           'State school fund', 'City general fund']
        })
        districts_path = os.path.join(output_dir, 'districts.csv')
        districts_df.to_csv(districts_path, index=False)
        
        # Levy rates CSV
        levy_rates_df = pd.DataFrame({
            'district_code': ['CE', 'CR', 'SS', 'CY'],
            'year': [2025, 2025, 2025, 2025],
            'rate': [0.9007089219, 1.2145630000, 0.8532140000, 1.4532650000]
        })
        levy_rates_path = os.path.join(output_dir, 'levy_rates.csv')
        levy_rates_df.to_csv(levy_rates_path, index=False)
        
        # Deductions CSV
        deductions_df = pd.DataFrame({
            'district_code': ['CE', 'CR', 'SS', 'CY'],
            'year': [2025, 2025, 2025, 2025],
            'amount': [25000, 15000, 10000, 5000],
            'description': ['Standard deduction', 'Road maintenance credit', 
                           'Education credit', 'Municipal services credit']
        })
        deductions_path = os.path.join(output_dir, 'deductions.csv')
        deductions_df.to_csv(deductions_path, index=False)
        
        # Properties CSV (sample with 5 properties)
        properties_df = pd.DataFrame({
            'district_code': ['CE', 'CE', 'CR', 'SS', 'CY'],
            'geo_id': ['GEO-1-1', 'GEO-1-2', 'GEO-2-1', 'GEO-3-1', 'GEO-4-1'],
            'assessed_value': [1250000, 950000, 1450000, 2100000, 1750000],
            'market_value': [1500000, 1100000, 1700000, 2300000, 1900000],
            'size_acres': [25.5, 15.2, 40.7, 80.3, 30.9]
        })
        properties_path = os.path.join(output_dir, 'properties.csv')
        properties_df.to_csv(properties_path, index=False)
        
        # Documentation text file
        documentation = """
PILT Data Import CSV Templates

This directory contains CSV templates for importing data into the PILT Dashboard.

Files:
- districts.csv: Required - Contains tax district information
- properties.csv: Contains property data with assessed values
- levy_rates.csv: Contains levy rates by district and year
- deductions.csv: Contains deductions by district and year

Required columns for each file:
- districts.csv: code, name
- properties.csv: district_code, geo_id, assessed_value
- levy_rates.csv: district_code, rate
- deductions.csv: district_code, amount

Notes:
- The district_code in properties.csv, levy_rates.csv, and deductions.csv must match a code in districts.csv
- If year is not specified in levy_rates.csv or deductions.csv, the current year will be used
- All monetary values should be entered as numbers without currency symbols or commas
        """
        
        documentation_path = os.path.join(output_dir, 'README.txt')
        with open(documentation_path, 'w') as f:
            f.write(documentation)
        
        logger.info(f"Sample CSV templates created in {output_dir}")
        return True
    
    except Exception as e:
        logger.error(f"Error creating CSV templates: {str(e)}")
        return False