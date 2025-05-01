"""
Validation module for PILT Dashboard.
This module provides functions for validating data inputs.
"""
import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, List, Union, Optional, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass

def validate_pilt_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate the DataFrame containing PILT data.
    
    Args:
        df (pd.DataFrame): DataFrame to validate
        
    Returns:
        Dict[str, Any]: Validation results with keys 'valid', 'errors', 'warnings', 'df'
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'df': df.copy()  # Include a copy of the dataframe in results
    }
    
    # Check if DataFrame is empty
    if df.empty:
        results['valid'] = False
        results['errors'].append("Data frame is empty")
        return results
    
    # Required columns
    required_columns = ['District', 'Assessed_Value', 'Levy_Rate']
    
    # Check for required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        results['valid'] = False
        results['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
    
    # Only continue validation if all required columns are present
    if not missing_columns:
        # Check for null values in required columns
        for col in required_columns:
            null_count = df[col].isna().sum()
            if null_count > 0:
                results['valid'] = False
                results['errors'].append(f"Column '{col}' contains {null_count} null values")
        
        # Check data types and value ranges
        if 'Assessed_Value' in df.columns:
            # Check that Assessed_Value is numeric
            if not pd.api.types.is_numeric_dtype(df['Assessed_Value']):
                # Try to convert to numeric
                try:
                    results['df']['Assessed_Value'] = pd.to_numeric(df['Assessed_Value'], errors='coerce')
                    null_count = results['df']['Assessed_Value'].isna().sum()
                    if null_count > 0:
                        results['warnings'].append(f"Converted 'Assessed_Value' column to numeric, but {null_count} values became NaN")
                except Exception as e:
                    results['valid'] = False
                    results['errors'].append(f"'Assessed_Value' column must contain numeric values: {str(e)}")
            else:
                # Check for negative values
                neg_values = (df['Assessed_Value'] < 0).sum()
                if neg_values > 0:
                    results['valid'] = False
                    results['errors'].append(f"'Assessed_Value' column contains {neg_values} negative values")
                
                # Check for suspiciously high values (outlier detection)
                mean_val = df['Assessed_Value'].mean()
                std_val = df['Assessed_Value'].std()
                if std_val > 0:  # Prevent division by zero
                    threshold = mean_val + 3 * std_val  # 3 standard deviations
                    outliers = (df['Assessed_Value'] > threshold).sum()
                    if outliers > 0:
                        results['warnings'].append(f"'Assessed_Value' column contains {outliers} potential outliers")
        
        if 'Levy_Rate' in df.columns:
            # Check that Levy_Rate is numeric
            if not pd.api.types.is_numeric_dtype(df['Levy_Rate']):
                # Try to convert to numeric
                try:
                    results['df']['Levy_Rate'] = pd.to_numeric(df['Levy_Rate'], errors='coerce')
                    null_count = results['df']['Levy_Rate'].isna().sum()
                    if null_count > 0:
                        results['warnings'].append(f"Converted 'Levy_Rate' column to numeric, but {null_count} values became NaN")
                except Exception as e:
                    results['valid'] = False
                    results['errors'].append(f"'Levy_Rate' column must contain numeric values: {str(e)}")
            else:
                # Check for negative values
                neg_values = (df['Levy_Rate'] < 0).sum()
                if neg_values > 0:
                    results['valid'] = False
                    results['errors'].append(f"'Levy_Rate' column contains {neg_values} negative values")
                
                # Check for suspiciously high levy rates (e.g., > 10)
                high_rates = (df['Levy_Rate'] > 10).sum()
                if high_rates > 0:
                    results['warnings'].append(f"'Levy_Rate' column contains {high_rates} values greater than 10, which may be unusually high")
        
        if 'District' in df.columns:
            # Check for empty district names
            empty_districts = (df['District'].astype(str).str.strip() == '').sum()
            if empty_districts > 0:
                results['valid'] = False
                results['errors'].append(f"'District' column contains {empty_districts} empty values")
            
            # Clean up district names by stripping whitespace
            results['df']['District'] = results['df']['District'].astype(str).str.strip()
    
    # Return validation results with the processed dataframe
    return results

def validate_what_if_options(
    new_rates: Dict[str, float] = {}, 
    value_adjustments: Dict[str, float] = {}, 
    deduction_adjustments: Dict[str, float] = {}
) -> Dict[str, Any]:
    """
    Validate the options for what-if analysis.
    
    Args:
        new_rates (Dict[str, float]): Dictionary with district as key and new levy rate as value
        value_adjustments (Dict[str, float]): Dictionary with district as key and percentage adjustment
            to assessed values as value (e.g., 1.05 for 5% increase)
        deduction_adjustments (Dict[str, float]): Dictionary with district as key and new deduction as value
        
    Returns:
        Dict[str, Any]: Validation results with keys 'valid', 'errors', 'warnings'
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Validate new_rates
    for district, rate in new_rates.items():
        if not isinstance(rate, (int, float)):
            results['valid'] = False
            results['errors'].append(f"New rate for district '{district}' must be a number")
        elif rate < 0:
            results['valid'] = False
            results['errors'].append(f"New rate for district '{district}' cannot be negative")
        elif rate > 10:
            results['warnings'].append(f"New rate for district '{district}' is unusually high (> 10)")
    
    # Validate value_adjustments
    for district, adjustment in value_adjustments.items():
        if not isinstance(adjustment, (int, float)):
            results['valid'] = False
            results['errors'].append(f"Value adjustment for district '{district}' must be a number")
        elif adjustment <= 0:
            results['valid'] = False
            results['errors'].append(f"Value adjustment for district '{district}' must be positive")
        elif adjustment > 2:
            results['warnings'].append(f"Value adjustment for district '{district}' is unusually high (> 100% increase)")
    
    # Validate deduction_adjustments
    for district, deduction in deduction_adjustments.items():
        if not isinstance(deduction, (int, float)):
            results['valid'] = False
            results['errors'].append(f"Deduction for district '{district}' must be a number")
        elif deduction < 0:
            results['valid'] = False
            results['errors'].append(f"Deduction for district '{district}' cannot be negative")
    
    return results

def validate_and_format_excel_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validate and format Excel data for PILT calculations.
    
    Args:
        df (pd.DataFrame): DataFrame from Excel import
        
    Returns:
        Tuple containing:
            - pd.DataFrame: Processed DataFrame ready for calculations
            - Dict[str, Any]: Validation results with keys 'valid', 'errors', 'warnings'
    """
    results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Check if required columns exist with expected or alternative names
    column_mapping = {
        'District': ['district', 'tax_district', 'taxing_district', 'district_name'],
        'Assessed_Value': ['assessed_value', 'assessedvalue', 'value', 'property_value'],
        'Levy_Rate': ['levy_rate', 'levyrate', 'rate', 'tax_rate']
    }
    
    # Try to identify and rename columns
    for required_col, alternatives in column_mapping.items():
        # Skip if the required column already exists
        if required_col in processed_df.columns:
            continue
        
        # Try to find alternative column names (case-insensitive)
        df_cols_lower = [col.lower() for col in processed_df.columns]
        for alt in alternatives:
            if alt.lower() in df_cols_lower:
                idx = df_cols_lower.index(alt.lower())
                original_col = processed_df.columns[idx]
                processed_df.rename(columns={original_col: required_col}, inplace=True)
                results['warnings'].append(f"Renamed column '{original_col}' to '{required_col}'")
                break
    
    # Validate if we have all required columns now
    validation_results = validate_pilt_dataframe(processed_df)
    
    # Merge validation results
    results['valid'] = validation_results['valid']
    results['errors'].extend(validation_results['errors'])
    results['warnings'].extend(validation_results['warnings'])
    
    # If valid, perform additional formatting
    if results['valid']:
        # Convert Assessed_Value to numeric, coercing errors to NaN
        if 'Assessed_Value' in processed_df.columns:
            processed_df['Assessed_Value'] = pd.to_numeric(processed_df['Assessed_Value'], errors='coerce')
            null_after = processed_df['Assessed_Value'].isna().sum()
            if null_after > 0:
                results['warnings'].append(f"Converted {null_after} non-numeric values in 'Assessed_Value' to NaN")
        
        # Convert Levy_Rate to numeric, coercing errors to NaN
        if 'Levy_Rate' in processed_df.columns:
            processed_df['Levy_Rate'] = pd.to_numeric(processed_df['Levy_Rate'], errors='coerce')
            null_after = processed_df['Levy_Rate'].isna().sum()
            if null_after > 0:
                results['warnings'].append(f"Converted {null_after} non-numeric values in 'Levy_Rate' to NaN")
        
        # Clean up District column - strip whitespace
        if 'District' in processed_df.columns:
            processed_df['District'] = processed_df['District'].astype(str).str.strip()
        
        # Drop rows with NaN in critical columns
        critical_columns = ['District', 'Assessed_Value', 'Levy_Rate']
        orig_rows = len(processed_df)
        processed_df.dropna(subset=critical_columns, inplace=True)
        dropped_rows = orig_rows - len(processed_df)
        if dropped_rows > 0:
            results['warnings'].append(f"Dropped {dropped_rows} rows with missing values in critical columns")
    
    return processed_df, results