"""
Simplified Benton County PILT Dashboard
A streamlined version for demonstration purposes.
"""
import streamlit as st
import pandas as pd
import json
import io
import base64
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Benton County PILT Dashboard", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create session state for storing data
if 'pilt_data' not in st.session_state:
    st.session_state.pilt_data = None
if 'calculated_data' not in st.session_state:
    st.session_state.calculated_data = None

# Page title and description 
st.title("Benton County PILT Dashboard")
st.write("""
This dashboard calculates and visualizes Payment in Lieu of Taxes (PILT) 
based on property data from Benton County.
""")

# Sidebar controls
st.sidebar.header("Dashboard Controls")
st.sidebar.subheader("Benton County Property Assessment Division")

# Data source selection 
data_source = st.sidebar.radio("Select data source", ("Sample Data", "Excel File"))

# Sample data function
def generate_sample_data():
    """Generate sample data for demonstration"""
    import random
    districts = ["City of Richland", "City of Kennewick", "City of Pasco", 
                 "West Richland", "Benton City", "Prosser"]
    
    data = []
    for district in districts:
        # Generate between 5-10 properties per district
        num_properties = random.randint(5, 10)
        for i in range(num_properties):
            property_id = f"{district[:3].upper()}-{random.randint(1000, 9999)}"
            assessed_value = random.randint(100000, 5000000)
            levy_rate = round(random.uniform(1.0, 3.5), 2)
            data.append({
                "Property_ID": property_id,
                "District": district,
                "Assessed_Value": assessed_value,
                "Levy_Rate": levy_rate
            })
    
    return pd.DataFrame(data)

# Load data based on selected source
try:
    if data_source == "Sample Data":
        if st.sidebar.button("Load Sample Data"):
            with st.spinner("Generating sample data..."):
                st.session_state.pilt_data = generate_sample_data()
                st.success("Sample data loaded successfully!")
    else:
        uploaded_file = st.sidebar.file_uploader("Upload PILT Excel File", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                sheet_name = st.sidebar.text_input("Sheet Name", "Sheet1")
                st.session_state.pilt_data = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                st.success("Excel file loaded successfully!")
            except Exception as e:
                st.error(f"Error loading Excel file: {str(e)}")
                st.session_state.pilt_data = None
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.session_state.pilt_data = None

# Simple PILT calculation function
def calculate_pilt(df, deductions=None):
    """
    Calculate the PILT due for each district based on assessed values and levy rates.
    """
    if deductions is None:
        deductions = {}
    
    # Make a copy to avoid modifying the original
    result_df = df.copy()
    
    # Calculate base PILT (Assessed_Value * Levy_Rate / 1000)
    result_df['Base_PILT'] = result_df['Assessed_Value'] * result_df['Levy_Rate'] / 1000
    
    # Apply deductions if any
    result_df['Deduction'] = 0.0
    for district, deduction in deductions.items():
        result_df.loc[result_df['District'] == district, 'Deduction'] = deduction / len(result_df[result_df['District'] == district])
    
    # Calculate final PILT due
    result_df['PILT_Due'] = result_df['Base_PILT'] - result_df['Deduction']
    result_df.loc[result_df['PILT_Due'] < 0, 'PILT_Due'] = 0  # Ensure no negative values
    
    return result_df

def aggregate_pilt_by_district(df):
    """
    Aggregate PILT calculations by district.
    """
    district_summary = df.groupby('District').agg({
        'Assessed_Value': 'sum',
        'Base_PILT': 'sum',
        'Deduction': 'sum',
        'PILT_Due': 'sum'
    }).reset_index()
    
    return district_summary

# Main content area - only show if data is loaded
if st.session_state.pilt_data is not None and not st.session_state.pilt_data.empty:
    # Display tabs for different views
    tab1, tab2, tab3 = st.tabs(["Raw Data", "PILT Calculations", "Export"])
    
    with tab1:
        st.header("Raw Property Data")
        # Add filters
        if 'District' in st.session_state.pilt_data.columns:
            district_filter = st.multiselect(
                "Filter by District", 
                options=st.session_state.pilt_data['District'].unique(),
                default=st.session_state.pilt_data['District'].unique()[0]
            )
            filtered_data = st.session_state.pilt_data[
                st.session_state.pilt_data['District'].isin(district_filter)]
        else:
            filtered_data = st.session_state.pilt_data
            
        # Display raw data
        st.dataframe(filtered_data)
        
        # Show data statistics
        st.subheader("Data Summary")
        st.write(f"Total records: {len(filtered_data)}")
        if 'Assessed_Value' in filtered_data.columns:
            st.write(f"Total Assessed Value: ${filtered_data['Assessed_Value'].sum():,.2f}")
            
    with tab2:
        st.header("PILT Calculations")
        
        # Get deductions if any
        deductions = {}
        use_deductions = st.checkbox("Apply Deductions")
        if use_deductions:
            st.info("Enter deduction amounts for specific districts if applicable")
            for district in st.session_state.pilt_data['District'].unique():
                deduction = st.number_input(f"Deduction for {district}", 
                                          min_value=0.0, 
                                          step=1000.0,
                                          format="%.2f")
                if deduction > 0:
                    deductions[district] = deduction
        
        # Calculate PILT
        if st.button("Calculate PILT"):
            with st.spinner("Calculating PILT..."):
                st.session_state.calculated_data = calculate_pilt(
                    st.session_state.pilt_data, 
                    deductions=deductions if use_deductions else {}
                )
                st.success("PILT calculation completed!")
        
        # Display calculated data if available
        if st.session_state.calculated_data is not None:
            # Aggregate by district
            district_summary = aggregate_pilt_by_district(st.session_state.calculated_data)
            
            # Display district summary
            st.subheader("PILT Summary by District")
            st.dataframe(district_summary)
            
            # Display total PILT due
            total_pilt = st.session_state.calculated_data['PILT_Due'].sum()
            st.metric("Total PILT Due", f"${total_pilt:,.2f}")
            
            # Simple bar chart for districts
            st.subheader("PILT by District")
            st.bar_chart(district_summary.set_index('District')['PILT_Due'])

    with tab3:
        st.header("Export Data")
        
        if st.session_state.calculated_data is not None:
            # Aggregate by district for export
            district_summary = aggregate_pilt_by_district(st.session_state.calculated_data)
            total_pilt = st.session_state.calculated_data['PILT_Due'].sum()
            
            export_format = st.selectbox("Export Format", ["CSV", "HTML Report"])
            if st.button("Export PILT Report"):
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if export_format == "CSV":
                    # For CSV, we'll create two separate files - one for detail and one for summary
                    csv_detail = io.StringIO()
                    st.session_state.calculated_data.to_csv(csv_detail, index=False)
                    
                    st.download_button(
                        label="Download CSV Detail Report",
                        data=csv_detail.getvalue(),
                        file_name=f"pilt_detail_{now}.csv",
                        mime="text/csv"
                    )
                    
                    csv_summary = io.StringIO()
                    district_summary.to_csv(csv_summary, index=False)
                    
                    st.download_button(
                        label="Download CSV Summary Report",
                        data=csv_summary.getvalue(),
                        file_name=f"pilt_summary_{now}.csv",
                        mime="text/csv"
                    )
                
                elif export_format == "HTML Report":
                    try:
                        st.info("Preparing Print-Friendly HTML report...")
                        
                        # Format currency values for better display
                        formatted_summary = district_summary.copy()
                        for col in ['Assessed_Value', 'Base_PILT', 'Deduction', 'PILT_Due']:
                            formatted_summary[col] = formatted_summary[col].map('${:,.2f}'.format)
                        
                        # Create HTML content for Print-friendly view
                        html_content = f"""
                        <html>
                        <head>
                            <title>PILT Report - {now}</title>
                            <style>
                                @media print {{
                                    @page {{
                                        size: letter;
                                        margin: 1cm;
                                    }}
                                }}
                                body {{ 
                                    font-family: Arial, sans-serif; 
                                    margin: 20px; 
                                    line-height: 1.4;
                                }}
                                h1 {{ 
                                    color: #0077b6; 
                                    text-align: center; 
                                    border-bottom: 2px solid #0077b6;
                                    padding-bottom: 10px;
                                }}
                                h2 {{ 
                                    color: #0077b6; 
                                    margin-top: 20px; 
                                    border-bottom: 1px solid #ddd;
                                    padding-bottom: 5px;
                                }}
                                table {{ 
                                    border-collapse: collapse; 
                                    width: 100%; 
                                    margin: 15px 0;
                                    font-size: 12px;
                                }}
                                th, td {{ 
                                    border: 1px solid #ddd; 
                                    padding: 8px; 
                                    text-align: left;
                                }}
                                th {{ 
                                    background-color: #f2f2f2; 
                                    font-weight: bold;
                                }}
                                tr:nth-child(even) {{
                                    background-color: #f9f9f9;
                                }}
                                .total {{ 
                                    font-weight: bold; 
                                    font-size: 16px;
                                    margin: 10px 0;
                                    text-align: right;
                                    padding-right: 20px;
                                }}
                                .chart {{
                                    width: 100%;
                                    text-align: center;
                                    margin: 20px 0;
                                }}
                                .header {{
                                    display: flex;
                                    justify-content: space-between;
                                    margin-bottom: 20px;
                                }}
                                .report-info {{
                                    font-size: 12px;
                                    color: #666;
                                    margin-bottom: 20px;
                                }}
                                footer {{
                                    margin-top: 30px;
                                    border-top: 1px solid #ddd;
                                    padding-top: 10px;
                                    font-size: 10px;
                                    color: #666;
                                    text-align: center;
                                }}
                                .print-btn {{
                                    background-color: #0077b6;
                                    color: white;
                                    padding: 10px 15px;
                                    text-align: center;
                                    text-decoration: none;
                                    display: inline-block;
                                    font-size: 16px;
                                    margin: 4px 2px;
                                    cursor: pointer;
                                    border-radius: 4px;
                                    border: none;
                                }}
                                .print-btn:hover {{
                                    background-color: #005f8d;
                                }}
                                .no-print {{
                                    display: block;
                                }}
                                @media print {{
                                    .no-print {{
                                        display: none;
                                    }}
                                }}
                            </style>
                            <script>
                                function printReport() {{
                                    window.print();
                                }}
                            </script>
                        </head>
                        <body>
                            <div class="no-print" style="text-align:center; margin-bottom:20px;">
                                <button class="print-btn" onclick="printReport()">Print this Report</button>
                                <p>Click the button above to print this report or save as PDF using your browser's print function</p>
                            </div>

                            <div class="header">
                                <div>
                                    <h1>Benton County PILT Report</h1>
                                    <div class="report-info">
                                        <p><strong>Generated on:</strong> {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                                        <p><strong>Total Records:</strong> {len(st.session_state.calculated_data)}</p>
                                        <p><strong>Districts:</strong> {len(district_summary)}</p>
                                    </div>
                                </div>
                            </div>
                            
                            <h2>Executive Summary</h2>
                            <p>This report provides a comprehensive analysis of Payment in Lieu of Taxes (PILT) 
                            calculations for Benton County. The total PILT due across all districts 
                            is <strong>${total_pilt:,.2f}</strong>.</p>
                            
                            <h2>PILT Summary by District</h2>
                            {formatted_summary.to_html(index=False)}
                            
                            <p class="total">Total PILT Due: ${total_pilt:,.2f}</p>
                            
                            <h2>PILT Calculation Detail</h2>
                            <p>The following table shows the detailed PILT calculations for each property:</p>
                            {st.session_state.calculated_data.to_html(index=False)}
                            
                            <footer>
                                <p>Benton County PILT Dashboard | Property Assessment Division</p>
                                <p>This document is for informational purposes only.</p>
                            </footer>
                        </body>
                        </html>
                        """
                        
                        # Use base64 encoding for the HTML content
                        encoded_html = base64.b64encode(html_content.encode()).decode()
                        
                        # Create a data URL
                        href = f'data:text/html;base64,{encoded_html}'
                        
                        # Add download button
                        st.markdown(
                            f'<a href="{href}" download="pilt_report_{now}.html" '
                            f'class="element-container" style="background-color:#0077b6; color:white; '
                            f'padding:10px 20px; text-align:center; text-decoration:none; '
                            f'display:inline-block; font-size:16px; margin:10px 2px; cursor:pointer; '
                            f'border-radius:4px;">Download Print-Ready Report</a>',
                            unsafe_allow_html=True
                        )
                        
                        # Add instructions
                        st.success("Report generated successfully!")
                        st.info("""
                        **Instructions:**
                        1. Click the button above to download the HTML report
                        2. Open the HTML file in your web browser
                        3. Use the 'Print' button in the report or your browser's print function (Ctrl+P / Cmd+P)
                        4. Select 'Save as PDF' in the printer options to create a PDF file
                        """)
                        
                    except Exception as e:
                        st.error(f"Error generating report: {str(e)}")
                        st.info("If HTML report generation fails, please try CSV format instead.")
else:
    st.info("Please load data using the controls in the sidebar to get started.")
    
# Footer
st.markdown("---")
st.markdown("Benton County PILT Dashboard | Developed for Property Assessment Division")