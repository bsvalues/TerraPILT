"""
Benton County PILT Dashboard
Interactive Streamlit application for calculating and visualizing 
Payment in Lieu of Taxes (PILT) data.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import io
import base64
import tempfile
import pdfkit
import csv
from datetime import datetime

# Import custom modules
from database import load_data, get_pilt_data, get_historical_pilt_data, get_districts
from calculations import (
    calculate_pilt, 
    perform_what_if_analysis, 
    aggregate_pilt_by_district,
    generate_historical_pilt_trend
)

# Configure Streamlit page
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
if 'historical_data' not in st.session_state:
    st.session_state.historical_data = None

# Page title and description with improved styling
st.markdown("""
<div style="background-color:#0077b6; padding:10px; border-radius:10px">
    <h1 style="color:white; text-align:center">Benton County PILT Dashboard</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background-color:#f8f9fa; padding:15px; border-radius:5px; margin:10px 0px">
    <p style="font-size:16px">
        This dashboard calculates and visualizes <b>Payment in Lieu of Taxes (PILT)</b> 
        based on property data from Benton County. Select your preferred data source and use 
        the interactive controls to perform analysis.
    </p>
    <p>
        <b>Features:</b>
        <ul>
            <li>Load data from SQL Database or Excel files</li>
            <li>Calculate PILT based on assessed values and levy rates</li>
            <li>Conduct "what-if" analysis with adjustable parameters</li>
            <li>View interactive visualizations of PILT data</li>
            <li>Export reports in multiple formats</li>
        </ul>
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar for data source selection and controls
st.sidebar.title("Data Source")
data_source = st.sidebar.radio("Select Data Source", ("SQL Database", "Excel File"))

# Load data based on selected source
try:
    if data_source == "SQL Database":
        if st.sidebar.button("Load Data from Database"):
            with st.spinner("Loading data from database..."):
                st.session_state.pilt_data = get_pilt_data()
                st.session_state.historical_data = get_historical_pilt_data()
                st.success("Data loaded successfully!")
    else:
        uploaded_file = st.sidebar.file_uploader("Upload PILT Excel File", type=["xlsx", "xls"])
        if uploaded_file is not None:
            try:
                sheet_name = st.sidebar.text_input("Sheet Name", "2023")
                st.session_state.pilt_data = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                st.success("Excel file loaded successfully!")
                
                # Try to load historical data if available
                try:
                    historical_sheet = st.sidebar.text_input("Historical Data Sheet (Optional)", "Historical")
                    st.session_state.historical_data = pd.read_excel(uploaded_file, sheet_name=historical_sheet)
                except Exception:
                    st.warning("Could not load historical data sheet. Year-over-year analysis may be limited.")
            except Exception as e:
                st.error(f"Error loading Excel file: {str(e)}")
                st.session_state.pilt_data = None
except Exception as e:
    st.error(f"Error loading data: {str(e)}")
    st.session_state.pilt_data = None

# Main content area - only show if data is loaded
if st.session_state.pilt_data is not None and not st.session_state.pilt_data.empty:
    # Display tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Raw Data", "PILT Calculations", "Visualizations", "What-If Analysis"])
    
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
                    deductions=deductions if use_deductions else None
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
            
            # Export options
            export_format = st.selectbox("Export Format", ["Excel", "CSV", "PDF"])
            if st.button("Export PILT Report"):
                now = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if export_format == "Excel":
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        st.session_state.calculated_data.to_excel(
                            writer, index=False, sheet_name='PILT_Detail'
                        )
                        district_summary.to_excel(
                            writer, index=False, sheet_name='PILT_Summary'
                        )
                    
                    # Download button
                    output.seek(0)
                    st.download_button(
                        label="Download Excel Report",
                        data=output,
                        file_name=f"pilt_report_{now}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                
                elif export_format == "CSV":
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
                
                elif export_format == "PDF":
                    try:
                        # Create HTML content for PDF
                        html_content = f"""
                        <html>
                        <head>
                            <title>PILT Report - {now}</title>
                            <style>
                                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                                h1 {{ color: #0077b6; text-align: center; }}
                                h2 {{ color: #0077b6; margin-top: 20px; }}
                                table {{ border-collapse: collapse; width: 100%; margin-top: 10px; }}
                                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                                th {{ background-color: #f2f2f2; }}
                                .total {{ font-weight: bold; }}
                            </style>
                        </head>
                        <body>
                            <h1>Benton County PILT Report</h1>
                            <p>Generated on: {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>
                            
                            <h2>PILT Summary by District</h2>
                            {district_summary.to_html(index=False)}
                            
                            <p class="total">Total PILT Due: ${total_pilt:,.2f}</p>
                            
                            <h2>PILT Detail</h2>
                            {st.session_state.calculated_data.to_html(index=False)}
                        </body>
                        </html>
                        """
                        
                        # Create PDF
                        with tempfile.NamedTemporaryFile(suffix='.html') as f:
                            f.write(html_content.encode('utf-8'))
                            f.flush()
                            
                            pdf_data = pdfkit.from_file(f.name, False)
                            
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_data,
                                file_name=f"pilt_report_{now}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Error generating PDF: {str(e)}")
                        st.info("If PDF generation fails, please try Excel or CSV format instead.")
    
    with tab3:
        st.header("PILT Visualizations")
        
        if st.session_state.calculated_data is not None:
            # District comparison chart
            st.subheader("PILT by District")
            district_summary = aggregate_pilt_by_district(st.session_state.calculated_data)
            
            fig_district = px.bar(
                district_summary, 
                x='District', 
                y='PILT_Due',
                title="PILT Due by District",
                labels={"PILT_Due": "PILT Amount ($)", "District": "Tax District"},
                color='District'
            )
            st.plotly_chart(fig_district, use_container_width=True)
            
            # Assessed Value vs PILT chart
            st.subheader("Assessed Value vs PILT")
            fig_comparison = px.scatter(
                district_summary, 
                x='Assessed_Value', 
                y='PILT_Due',
                size='PILT_Due',
                color='District',
                title="Assessed Value vs PILT Due",
                labels={
                    "Assessed_Value": "Assessed Value ($)", 
                    "PILT_Due": "PILT Amount ($)"
                },
                hover_data=['Levy_Rate']
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Historical trend visualization if data is available
        if st.session_state.historical_data is not None and not st.session_state.historical_data.empty:
            st.subheader("Historical PILT Trends")
            
            # Process historical data
            trend_data = generate_historical_pilt_trend(st.session_state.historical_data)
            
            # Create trend chart
            if 'year' in trend_data.columns and 'estimated_pilt' in trend_data.columns:
                fig_trend = px.line(
                    trend_data,
                    x='year',
                    y='estimated_pilt',
                    title="Year-over-Year PILT Trend",
                    labels={"year": "Year", "estimated_pilt": "Estimated PILT ($)"},
                    markers=True
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            else:
                st.warning("Historical data does not contain required columns for trend visualization")

    with tab4:
        st.header("What-If Scenario Analysis")
        
        if st.session_state.pilt_data is not None:
            st.write("""
            Adjust parameters below to see how they would affect PILT calculations.
            This allows for scenario planning and impact analysis.
            """)
            
            # Get unique districts for scenario analysis
            districts = st.session_state.pilt_data['District'].unique()
            
            # Create columns for adjustments
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Levy Rate Adjustments")
                new_rates = {}
                for district in districts:
                    # Get current average levy rate
                    current_rate = st.session_state.pilt_data[
                        st.session_state.pilt_data['District'] == district
                    ]['Levy_Rate'].mean()
                    
                    # Create slider for adjustment
                    new_rate = st.slider(
                        f"Levy Rate for {district}",
                        min_value=float(current_rate * 0.5),
                        max_value=float(current_rate * 1.5),
                        value=float(current_rate),
                        step=0.01,
                        format="%.4f"
                    )
                    new_rates[district] = new_rate
            
            with col2:
                st.subheader("Assessed Value Adjustments")
                value_adjustments = {}
                for district in districts:
                    # Create percentage adjustment slider
                    pct_change = st.slider(
                        f"Assessed Value Adjustment for {district} (%)",
                        min_value=-50,
                        max_value=50,
                        value=0,
                        step=1
                    )
                    # Convert percentage to multiplier
                    value_adjustments[district] = 1 + (pct_change / 100)
            
            # Deduction adjustments
            st.subheader("Deduction Adjustments")
            use_scenario_deductions = st.checkbox("Apply Scenario Deductions")
            deduction_adjustments = {}
            if use_scenario_deductions:
                for district in districts:
                    deduction = st.number_input(
                        f"Scenario Deduction for {district}",
                        min_value=0.0,
                        step=1000.0,
                        format="%.2f"
                    )
                    if deduction > 0:
                        deduction_adjustments[district] = deduction
            
            # Run scenario analysis
            if st.button("Run Scenario Analysis"):
                with st.spinner("Calculating scenario..."):
                    scenario_results = perform_what_if_analysis(
                        st.session_state.pilt_data,
                        new_rates=new_rates,
                        value_adjustments=value_adjustments,
                        deduction_adjustments=deduction_adjustments if use_scenario_deductions else None
                    )
                    
                    # Aggregate scenario results by district
                    scenario_summary = aggregate_pilt_by_district(scenario_results)
                    
                    # Prepare comparison with original data if calculated
                    if st.session_state.calculated_data is not None:
                        original_summary = aggregate_pilt_by_district(st.session_state.calculated_data)
                        
                        # Merge for comparison
                        comparison = scenario_summary.merge(
                            original_summary,
                            on='District',
                            suffixes=('_scenario', '_original')
                        )
                        
                        # Calculate differences
                        comparison['PILT_Difference'] = comparison['PILT_Due_scenario'] - comparison['PILT_Due_original']
                        comparison['PILT_Pct_Change'] = (comparison['PILT_Difference'] / comparison['PILT_Due_original']) * 100
                        
                        # Display comparison
                        st.subheader("Scenario Comparison")
                        st.dataframe(comparison[[
                            'District', 
                            'PILT_Due_original', 
                            'PILT_Due_scenario', 
                            'PILT_Difference', 
                            'PILT_Pct_Change'
                        ]])
                        
                        # Visualization of comparison
                        fig_comparison = px.bar(
                            comparison,
                            x='District',
                            y=['PILT_Due_original', 'PILT_Due_scenario'],
                            barmode='group',
                            title="Original vs Scenario PILT Comparison",
                            labels={
                                "value": "PILT Amount ($)",
                                "District": "Tax District",
                                "variable": "Scenario"
                            }
                        )
                        st.plotly_chart(fig_comparison, use_container_width=True)
                        
                        # Total impact
                        total_original = comparison['PILT_Due_original'].sum()
                        total_scenario = comparison['PILT_Due_scenario'].sum()
                        total_diff = total_scenario - total_original
                        total_pct = (total_diff / total_original) * 100 if total_original != 0 else 0
                        
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Original Total PILT", f"${total_original:,.2f}")
                        col2.metric("Scenario Total PILT", f"${total_scenario:,.2f}")
                        col3.metric("Difference", f"${total_diff:,.2f} ({total_pct:.2f}%)",
                                delta=f"{total_pct:.2f}%")
                    else:
                        st.warning("Run PILT calculation first to enable comparison")
                        
                        # Still show scenario results
                        st.subheader("Scenario Results")
                        st.dataframe(scenario_summary)
                        st.metric("Scenario Total PILT", f"${scenario_summary['PILT_Due'].sum():,.2f}")
else:
    st.info("Please select a data source and load data to begin.")
    
    # Show example placeholder
    st.subheader("Dashboard Overview")
    st.write("""
    This PILT (Payment in Lieu of Taxes) Dashboard provides:
    
    1. **Data Loading**: Import data from the county's SQL database or upload your own Excel file
    2. **PILT Calculations**: Automatically calculate PILT based on assessed values, levy rates and deductions
    3. **Interactive Visualizations**: View district comparisons and historical trends
    4. **What-If Analysis**: Simulate scenarios by adjusting levy rates, assessed values, and deductions
    5. **Export Reports**: Download detailed PILT reports in Excel, CSV, or PDF formats
    
    Get started by selecting a data source in the sidebar.
    """)

# Footer
st.markdown("---")
st.caption("Benton County PILT Dashboard | Developed for the Property Assessment Division")
