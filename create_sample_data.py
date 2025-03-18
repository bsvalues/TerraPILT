"""
Create sample Excel workbook for PILT dashboard testing.
"""
import pandas as pd
from datetime import datetime

def create_sample_pilt_data():
    """
    Create sample PILT data for testing the dashboard.
    """
    # Create sample data for 2023
    data_2023 = {
        'District': [
            'District 1', 'District 1', 'District 1', 
            'District 2', 'District 2', 'District 2',
            'District 3', 'District 3', 
            'District 4', 'District 4', 'District 4',
            'District 5', 'District 5'
        ],
        'Property_ID': [
            'P001', 'P002', 'P003',
            'P004', 'P005', 'P006',
            'P007', 'P008',
            'P009', 'P010', 'P011',
            'P012', 'P013'
        ],
        'Assessed_Value': [
            1250000, 780000, 920000,
            2100000, 1850000, 670000,
            950000, 1200000,
            3100000, 2750000, 1900000,
            1450000, 890000
        ],
        'Levy_Rate': [
            10.52, 10.52, 10.52,
            9.85, 9.85, 9.85,
            11.24, 11.24,
            8.75, 8.75, 8.75,
            10.08, 10.08
        ]
    }
    
    df_2023 = pd.DataFrame(data_2023)
    
    # Create historical data (4 years)
    historical_data = []
    
    # 2020 data (base data with lower values)
    data_2020 = {
        'Year': 2020,
        'District': ['District 1', 'District 2', 'District 3', 'District 4', 'District 5'],
        'Assessed_Value': [2500000, 4100000, 1800000, 6950000, 2050000],
        'Levy_Rate': [9.75, 9.12, 10.35, 8.24, 9.45]
    }
    historical_data.append(pd.DataFrame(data_2020))
    
    # 2021 data (slight increase)
    data_2021 = {
        'Year': 2021,
        'District': ['District 1', 'District 2', 'District 3', 'District 4', 'District 5'],
        'Assessed_Value': [2650000, 4350000, 1950000, 7200000, 2180000],
        'Levy_Rate': [9.95, 9.35, 10.65, 8.45, 9.65]
    }
    historical_data.append(pd.DataFrame(data_2021))
    
    # 2022 data (moderate increase)
    data_2022 = {
        'Year': 2022,
        'District': ['District 1', 'District 2', 'District 3', 'District 4', 'District 5'],
        'Assessed_Value': [2800000, 4500000, 2050000, 7480000, 2280000],
        'Levy_Rate': [10.25, 9.55, 10.95, 8.55, 9.85]
    }
    historical_data.append(pd.DataFrame(data_2022))
    
    # 2023 data (aggregated from detail data)
    district_summary_2023 = df_2023.groupby('District').agg({
        'Assessed_Value': 'sum',
        'Levy_Rate': 'first'  # Rates are the same per district
    }).reset_index()
    
    district_summary_2023['Year'] = 2023
    historical_data.append(district_summary_2023)
    
    # Combine historical data
    historical_df = pd.concat(historical_data)
    
    # Create Excel file with both datasets
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"samples/pilt_sample_data_{timestamp}.xlsx"
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        df_2023.to_excel(writer, sheet_name='2023', index=False)
        historical_df.to_excel(writer, sheet_name='Historical', index=False)
    
    print(f"Sample data created: {filename}")
    return filename

if __name__ == "__main__":
    create_sample_pilt_data()