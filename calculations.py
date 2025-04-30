"""
Calculation engine for PILT (Payment in Lieu of Taxes) dashboard.
This module handles the calculation of PILT based on property data.
"""
import pandas as pd
import logging
from typing import Dict, Any, Optional, Union, Tuple
from validation import validate_pilt_dataframe, ValidationError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_pilt(df: pd.DataFrame, deductions: dict = {}, validate: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Calculate the PILT due for each district based on assessed values and levy rates.
    
    Args:
        df (pd.DataFrame): DataFrame with columns: 'District', 'Assessed_Value', 'Levy_Rate'
        deductions (dict, optional): Dictionary with district as key and deduction amount as value.
            Defaults to empty dict.
        validate (bool, optional): Whether to validate the input data. Defaults to True.
    
    Returns:
        Tuple containing:
            - pd.DataFrame: DataFrame with additional columns for PILT calculations
            - Dict[str, Any]: Validation results with keys 'valid', 'errors', 'warnings'
    
    Raises:
        ValidationError: If validation is enabled and the data fails validation
    """
    validation_result = {"valid": True, "errors": [], "warnings": []}
    
    # Validate input data if requested
    if validate:
        validation_result = validate_pilt_dataframe(df)
        if not validation_result["valid"]:
            error_msg = "; ".join(validation_result["errors"])
            logger.error(f"Validation failed: {error_msg}")
            raise ValidationError(f"PILT calculation failed due to validation errors", 
                                 validation_result["errors"])
        
        # Use the validated DataFrame
        working_df = validation_result["df"]
    else:
        # Skip validation but still make a copy
        working_df = df.copy()
    
    # Calculate the base PILT (assessed value per $1000 * levy rate)
    working_df['Base_PILT'] = (working_df['Assessed_Value'] / 1000) * working_df['Levy_Rate']
    
    # Apply deductions if provided
    if deductions:
        # Validate deductions
        invalid_districts = [d for d in deductions.keys() 
                            if d not in working_df['District'].unique()]
        if invalid_districts:
            warning = f"Deductions provided for non-existent districts: {invalid_districts}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
        
        working_df['Deduction'] = working_df['District'].map(deductions).fillna(0)
    else:
        working_df['Deduction'] = 0
    
    # Ensure deductions don't exceed Base_PILT (negative PILT_Due not allowed)
    negative_pilt = working_df['Deduction'] > working_df['Base_PILT']
    if negative_pilt.any():
        warning = f"Deductions exceed Base PILT for {negative_pilt.sum()} records. Capping at Base_PILT."
        validation_result["warnings"].append(warning)
        logger.warning(warning)
        
        # Cap deductions at Base_PILT value
        working_df.loc[negative_pilt, 'Deduction'] = working_df.loc[negative_pilt, 'Base_PILT']
    
    # Calculate final PILT due
    working_df['PILT_Due'] = working_df['Base_PILT'] - working_df['Deduction']
    
    # Log calculation summary
    total_pilt = working_df['PILT_Due'].sum()
    district_count = working_df['District'].nunique()
    logger.info(f"PILT calculation completed for {district_count} districts. Total PILT: ${total_pilt:,.2f}")
    
    return working_df, validation_result

def perform_what_if_analysis(df: pd.DataFrame, new_rates: dict = {}, 
                            value_adjustments: dict = {}, 
                            deduction_adjustments: dict = {}, 
                            validate: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Perform "what-if" scenario analysis by adjusting key parameters.
    
    Args:
        df (pd.DataFrame): Original DataFrame with PILT data
        new_rates (dict, optional): Dictionary with district as key and new levy rate as value.
        value_adjustments (dict, optional): Dictionary with district as key and percentage 
            adjustment to assessed values as value (e.g., 1.05 for 5% increase).
        deduction_adjustments (dict, optional): Dictionary with district as key and new deduction as value.
        validate (bool, optional): Whether to validate the data. Defaults to True.
    
    Returns:
        Tuple containing:
            - pd.DataFrame: DataFrame with adjusted values and recalculated PILT
            - Dict[str, Any]: Validation results with keys 'valid', 'errors', 'warnings'
    """
    validation_result = {"valid": True, "errors": [], "warnings": []}
    
    # First validate the input data if requested
    if validate:
        initial_validation = validate_pilt_dataframe(df)
        if not initial_validation["valid"]:
            error_msg = "; ".join(initial_validation["errors"])
            logger.error(f"Initial validation failed: {error_msg}")
            raise ValidationError(f"What-if analysis failed due to validation errors in input data", 
                                 initial_validation["errors"])
        
        # Use the validated DataFrame
        working_df = initial_validation["df"].copy()
        # Merge any warnings from initial validation
        validation_result["warnings"].extend(initial_validation["warnings"])
    else:
        # Skip validation but still make a copy
        working_df = df.copy()
    
    # Validate adjustment parameters
    districts = working_df['District'].unique()
    
    # Validate new_rates
    if new_rates:
        invalid_districts = [d for d in new_rates.keys() if d not in districts]
        invalid_rates = {d: r for d, r in new_rates.items() 
                        if d in districts and (not isinstance(r, (int, float)) or r < 0)}
        
        if invalid_districts:
            warning = f"New rates provided for non-existent districts: {invalid_districts}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            
        if invalid_rates:
            warning = f"Invalid rate values: {invalid_rates}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            # Remove invalid rates to prevent calculation errors
            for district in invalid_rates:
                del new_rates[district]
        
        # Apply valid new rates
        for district, rate in new_rates.items():
            if district in districts:
                mask = working_df['District'] == district
                working_df.loc[mask, 'Levy_Rate'] = rate
                logger.info(f"Adjusted levy rate for '{district}' to {rate}")
    
    # Validate value_adjustments
    if value_adjustments:
        invalid_districts = [d for d in value_adjustments.keys() if d not in districts]
        invalid_adjustments = {d: a for d, a in value_adjustments.items() 
                             if d in districts and (not isinstance(a, (int, float)) or a <= 0)}
        
        if invalid_districts:
            warning = f"Value adjustments provided for non-existent districts: {invalid_districts}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            
        if invalid_adjustments:
            warning = f"Invalid value adjustment factors: {invalid_adjustments}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            # Remove invalid adjustments
            for district in invalid_adjustments:
                del value_adjustments[district]
        
        # Apply valid value adjustments
        for district, adjustment in value_adjustments.items():
            if district in districts:
                mask = working_df['District'] == district
                original_value = working_df.loc[mask, 'Assessed_Value'].sum()
                working_df.loc[mask, 'Assessed_Value'] = working_df.loc[mask, 'Assessed_Value'] * adjustment
                new_value = working_df.loc[mask, 'Assessed_Value'].sum()
                logger.info(f"Adjusted assessed value for '{district}' by factor {adjustment}. " +
                           f"Changed from ${original_value:,.2f} to ${new_value:,.2f}")
    
    # Prepare deductions
    final_deductions = {}
    if deduction_adjustments:
        invalid_districts = [d for d in deduction_adjustments.keys() if d not in districts]
        invalid_deductions = {d: v for d, v in deduction_adjustments.items() 
                            if d in districts and (not isinstance(v, (int, float)) or v < 0)}
        
        if invalid_districts:
            warning = f"Deduction adjustments provided for non-existent districts: {invalid_districts}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            
        if invalid_deductions:
            warning = f"Invalid deduction values: {invalid_deductions}"
            validation_result["warnings"].append(warning)
            logger.warning(warning)
            # Remove invalid deductions
            for district in invalid_deductions:
                del deduction_adjustments[district]
        
        # Use valid deduction adjustments
        final_deductions = {d: v for d, v in deduction_adjustments.items() if d in districts}
        
        for district, deduction in final_deductions.items():
            logger.info(f"Set deduction for '{district}' to ${deduction:,.2f}")
    
    # Recalculate with adjusted values
    result_df, calc_validation = calculate_pilt(working_df, final_deductions, validate=False)
    
    # Merge validation results
    validation_result["warnings"].extend(calc_validation["warnings"])
    
    logger.info(f"What-if analysis completed with {len(validation_result['warnings'])} warnings")
    
    return result_df, validation_result

def aggregate_pilt_by_district(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate PILT calculations by district.
    
    Args:
        df (pd.DataFrame): DataFrame with PILT calculations
        
    Returns:
        pd.DataFrame: Aggregated summary by district
    """
    # Group by district and sum the relevant columns
    summary = df.groupby('District').agg({
        'Assessed_Value': 'sum',
        'Base_PILT': 'sum',
        'Deduction': 'sum',
        'PILT_Due': 'sum'
    }).reset_index()
    
    # Add average levy rate per district
    levy_rates = df.groupby('District')['Levy_Rate'].mean().reset_index()
    summary = summary.merge(levy_rates, on='District')
    
    return summary

def calculate_year_over_year_changes(current_df: pd.DataFrame, previous_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate year-over-year changes in PILT values.
    
    Args:
        current_df (pd.DataFrame): Current year's PILT data by district
        previous_df (pd.DataFrame): Previous year's PILT data by district
        
    Returns:
        pd.DataFrame: DataFrame with year-over-year changes
    """
    # Ensure both DataFrames have the same structure
    if set(current_df.columns) != set(previous_df.columns):
        raise ValueError("Current and previous year DataFrames must have the same columns")
    
    # Merge current and previous year data
    merged = current_df.merge(
        previous_df, 
        on='District', 
        suffixes=('_current', '_previous')
    )
    
    # Calculate changes
    for column in ['Assessed_Value', 'Levy_Rate', 'Base_PILT', 'Deduction', 'PILT_Due']:
        current_col = f"{column}_current"
        previous_col = f"{column}_previous"
        change_col = f"{column}_change"
        pct_change_col = f"{column}_pct_change"
        
        merged[change_col] = merged[current_col] - merged[previous_col]
        # Avoid division by zero
        merged[pct_change_col] = merged.apply(
            lambda row: (row[current_col] - row[previous_col]) / row[previous_col] * 100 
            if row[previous_col] != 0 else float('inf'),
            axis=1
        )
    
    return merged

def generate_historical_pilt_trend(historical_data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate historical PILT trend data for visualization.
    
    Args:
        historical_data (pd.DataFrame): Historical data with years, assessed values, and levy rates
        
    Returns:
        pd.DataFrame: Processed data for year-over-year trend visualization
    """
    # Create a copy of the historical data
    trend_data = historical_data.copy()
    
    # Calculate estimated PILT for each year based on total assessed value and average levy rate
    if 'total_assessed_value' in trend_data.columns and 'avg_levy_rate' in trend_data.columns:
        trend_data['estimated_pilt'] = (trend_data['total_assessed_value'] / 1000) * trend_data['avg_levy_rate']
    
    return trend_data
