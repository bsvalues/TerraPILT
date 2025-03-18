"""
Calculation engine for PILT (Payment in Lieu of Taxes) dashboard.
This module handles the calculation of PILT based on property data.
"""
import pandas as pd

def calculate_pilt(df: pd.DataFrame, deductions: dict = None) -> pd.DataFrame:
    """
    Calculate the PILT due for each district based on assessed values and levy rates.
    
    Args:
        df (pd.DataFrame): DataFrame with columns: 'District', 'Assessed_Value', 'Levy_Rate'
        deductions (dict, optional): Dictionary with district as key and deduction amount as value.
            Defaults to None.
    
    Returns:
        pd.DataFrame: DataFrame with additional columns for PILT calculations
    """
    # Make a copy to avoid modifying the original DataFrame
    result_df = df.copy()
    
    # Calculate the base PILT (assessed value per $1000 * levy rate)
    result_df['Base_PILT'] = (result_df['Assessed_Value'] / 1000) * result_df['Levy_Rate']
    
    # Apply deductions if provided
    if deductions:
        result_df['Deduction'] = result_df['District'].map(deductions).fillna(0)
    else:
        result_df['Deduction'] = 0
    
    # Calculate final PILT due
    result_df['PILT_Due'] = result_df['Base_PILT'] - result_df['Deduction']
    
    return result_df

def perform_what_if_analysis(df: pd.DataFrame, new_rates: dict = None, 
                            value_adjustments: dict = None, 
                            deduction_adjustments: dict = None) -> pd.DataFrame:
    """
    Perform "what-if" scenario analysis by adjusting key parameters.
    
    Args:
        df (pd.DataFrame): Original DataFrame with PILT data
        new_rates (dict, optional): Dictionary with district as key and new levy rate as value.
        value_adjustments (dict, optional): Dictionary with district as key and percentage 
            adjustment to assessed values as value (e.g., 1.05 for 5% increase).
        deduction_adjustments (dict, optional): Dictionary with district as key and new deduction as value.
    
    Returns:
        pd.DataFrame: DataFrame with adjusted values and recalculated PILT
    """
    # Make a copy to avoid modifying the original DataFrame
    scenario_df = df.copy()
    
    # Adjust levy rates if provided
    if new_rates:
        for district, rate in new_rates.items():
            mask = scenario_df['District'] == district
            scenario_df.loc[mask, 'Levy_Rate'] = rate
    
    # Adjust assessed values if provided
    if value_adjustments:
        for district, adjustment in value_adjustments.items():
            mask = scenario_df['District'] == district
            scenario_df.loc[mask, 'Assessed_Value'] = scenario_df.loc[mask, 'Assessed_Value'] * adjustment
    
    # Recalculate with adjusted values
    deductions = {}
    if deduction_adjustments:
        deductions = deduction_adjustments
    
    return calculate_pilt(scenario_df, deductions)

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
