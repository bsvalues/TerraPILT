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
if 'chart_theme' not in st.session_state:
    st.session_state.chart_theme = "default"

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

# Sidebar with improved styling
st.sidebar.markdown("""
<div style="background-color:#f0f2f6; padding:10px; border-radius:5px">
    <h2 style="color:#0077b6; text-align:center">PILT Dashboard Controls</h2>
</div>
""", unsafe_allow_html=True)

# Add County logo/info section
st.sidebar.markdown("""
<div style="text-align:center; margin-bottom:20px">
    <h4>Benton County</h4>
    <p>Property Assessment Division</p>
</div>
""", unsafe_allow_html=True)

# Data source selection with better styling
st.sidebar.markdown("### Data Source")
st.sidebar.markdown("Select the source of property data for PILT calculations:")
data_source = st.sidebar.radio("Select data source", ("SQL Database", "Excel File"))

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
        st.markdown("""
        <div style="background-color:#f0f8ff; padding:10px; border-radius:5px; margin-bottom:20px">
            <h2 style="color:#0077b6; text-align:center">PILT Visualizations</h2>
            <p style="text-align:center">Interactive charts and visual analysis of PILT data</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.calculated_data is not None:
            # Controls for chart customization
            st.markdown("### Chart Customization")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                chart_theme = st.selectbox(
                    "Chart Color Theme",
                    options=["default", "blues", "sunburst", "viridis", "plasma", "cividis"],
                    index=0
                )
                
            with chart_col2:
                chart_type = st.selectbox(
                    "District Comparison Chart Type",
                    options=["Bar Chart", "Pie Chart", "Donut Chart"],
                    index=0
                )
            
            # District comparison chart
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:10px; border-radius:5px; margin:15px 0px">
                <h3 style="color:#0077b6;">PILT by District</h3>
            </div>
            """, unsafe_allow_html=True)
            
            district_summary = aggregate_pilt_by_district(st.session_state.calculated_data)
            
            if chart_type == "Bar Chart":
                fig_district = px.bar(
                    district_summary, 
                    x='District', 
                    y='PILT_Due',
                    title="PILT Due by District",
                    labels={"PILT_Due": "PILT Amount ($)", "District": "Tax District"},
                    color='District',
                    color_discrete_sequence=px.colors.sequential.Blues if chart_theme == "blues" 
                                        else (px.colors.sequential.Viridis if chart_theme == "viridis"
                                            else (px.colors.sequential.Plasma if chart_theme == "plasma"
                                                else (px.colors.sequential.Cividis if chart_theme == "cividis"
                                                    else (px.colors.qualitative.Set3 if chart_theme == "sunburst"
                                                        else px.colors.qualitative.Plotly))))
                )
                # Customize layout
                fig_district.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=20,
                    hoverlabel=dict(bgcolor="white", font_size=16),
                    xaxis=dict(tickangle=-45)
                )
            elif chart_type == "Pie Chart":
                fig_district = px.pie(
                    district_summary,
                    values='PILT_Due',
                    names='District',
                    title="PILT Due by District",
                    color='District',
                    color_discrete_sequence=px.colors.sequential.Blues if chart_theme == "blues" 
                                        else (px.colors.sequential.Viridis if chart_theme == "viridis"
                                            else (px.colors.sequential.Plasma if chart_theme == "plasma"
                                                else (px.colors.sequential.Cividis if chart_theme == "cividis"
                                                    else (px.colors.qualitative.Set3 if chart_theme == "sunburst"
                                                        else px.colors.qualitative.Plotly))))
                )
                fig_district.update_traces(textposition='inside', textinfo='percent+label')
            else:  # Donut Chart
                fig_district = px.pie(
                    district_summary,
                    values='PILT_Due',
                    names='District',
                    title="PILT Due by District",
                    color='District',
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Blues if chart_theme == "blues" 
                                        else (px.colors.sequential.Viridis if chart_theme == "viridis"
                                            else (px.colors.sequential.Plasma if chart_theme == "plasma"
                                                else (px.colors.sequential.Cividis if chart_theme == "cividis"
                                                    else (px.colors.qualitative.Set3 if chart_theme == "sunburst"
                                                        else px.colors.qualitative.Plotly))))
                )
                fig_district.update_traces(textposition='inside', textinfo='percent+label')
                fig_district.update_layout(
                    annotations=[dict(text='PILT Due', x=0.5, y=0.5, font_size=20, showarrow=False)]
                )
                
            st.plotly_chart(fig_district, use_container_width=True)
            
            # Chart data download option
            st.markdown("**Export chart data:**")
            if st.button("Export Chart Data to CSV", key="district_csv"):
                csv_data = io.StringIO()
                district_summary.to_csv(csv_data, index=False)
                csv_data.seek(0)
                st.download_button(
                    label="Download CSV",
                    data=csv_data.getvalue(),
                    file_name=f"pilt_by_district_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            # Assessed Value vs PILT chart with enhancements
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:10px; border-radius:5px; margin:25px 0px 15px 0px">
                <h3 style="color:#0077b6;">Assessed Value vs PILT Relationship</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Add interactive controls
            show_trendline = st.checkbox("Show Trendline", value=True)
            
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
                hover_data=['Levy_Rate'],
                trendline="ols" if show_trendline else None,
                color_discrete_sequence=px.colors.sequential.Blues if chart_theme == "blues" 
                                    else (px.colors.sequential.Viridis if chart_theme == "viridis"
                                        else (px.colors.sequential.Plasma if chart_theme == "plasma"
                                            else (px.colors.sequential.Cividis if chart_theme == "cividis"
                                                else (px.colors.qualitative.Set3 if chart_theme == "sunburst"
                                                    else px.colors.qualitative.Plotly))))
            )
            
            # Enhance layout
            fig_comparison.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                title_font_size=20,
                hoverlabel=dict(bgcolor="white", font_size=16),
                xaxis=dict(
                    title_font=dict(size=16),
                    tickformat="$,.0f"
                ),
                yaxis=dict(
                    title_font=dict(size=16),
                    tickformat="$,.0f"
                )
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Chart data download option
            st.markdown("**Export chart data:**")
            if st.button("Export Chart Data to CSV", key="comparison_csv"):
                csv_data = io.StringIO()
                district_summary.to_csv(csv_data, index=False)
                csv_data.seek(0)
                st.download_button(
                    label="Download CSV",
                    data=csv_data.getvalue(),
                    file_name=f"pilt_vs_value_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # Historical trend visualization if data is available
        if st.session_state.historical_data is not None and not st.session_state.historical_data.empty:
            st.markdown("""
            <div style="background-color:#f8f9fa; padding:10px; border-radius:5px; margin:25px 0px 15px 0px">
                <h3 style="color:#0077b6;">Historical PILT Trends</h3>
                <p>Year-over-year changes in PILT values</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Process historical data
            trend_data = generate_historical_pilt_trend(st.session_state.historical_data)
            
            # Create trend chart
            if 'year' in trend_data.columns and 'estimated_pilt' in trend_data.columns:
                # Add year-over-year change calculation
                if len(trend_data) > 1:
                    trend_data['previous_pilt'] = trend_data['estimated_pilt'].shift(1)
                    trend_data['yoy_change'] = (trend_data['estimated_pilt'] - trend_data['previous_pilt']) / trend_data['previous_pilt'] * 100
                    trend_data['yoy_change'] = trend_data['yoy_change'].fillna(0)
                    
                    # Display YoY change as a table
                    st.markdown("#### Year-over-Year Change")
                    yoy_df = trend_data[['year', 'estimated_pilt', 'yoy_change']].copy()
                    yoy_df.columns = ['Year', 'PILT Amount ($)', 'YoY Change (%)']
                    yoy_df['PILT Amount ($)'] = yoy_df['PILT Amount ($)'].map('${:,.2f}'.format)
                    yoy_df['YoY Change (%)'] = yoy_df['YoY Change (%)'].map('{:+.2f}%'.format)
                    st.dataframe(yoy_df)
                
                # Get chart theme if available, otherwise use default
                trend_chart_theme = "default"
                if 'chart_theme' in locals():
                    trend_chart_theme = chart_theme
                
                # Enhanced styling for the trend chart
                fig_trend = px.line(
                    trend_data,
                    x='year',
                    y='estimated_pilt',
                    title="Year-over-Year PILT Trend",
                    labels={"year": "Year", "estimated_pilt": "Estimated PILT ($)"},
                    markers=True,
                    color_discrete_sequence=px.colors.sequential.Blues if trend_chart_theme == "blues" 
                                    else (px.colors.sequential.Viridis if trend_chart_theme == "viridis"
                                        else (px.colors.sequential.Plasma if trend_chart_theme == "plasma"
                                            else (px.colors.sequential.Cividis if trend_chart_theme == "cividis"
                                                else (px.colors.qualitative.Set3 if trend_chart_theme == "sunburst"
                                                    else px.colors.qualitative.Plotly))))
                )
                
                # Enhance layout
                fig_trend.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    title_font_size=20,
                    hoverlabel=dict(bgcolor="white", font_size=16),
                    xaxis=dict(
                        title_font=dict(size=16),
                        tickangle=0
                    ),
                    yaxis=dict(
                        title_font=dict(size=16),
                        tickformat="$,.0f"
                    ),
                    hovermode="x unified"
                )
                
                # Customize line and markers
                fig_trend.update_traces(
                    line=dict(width=3),
                    marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')),
                    hovertemplate='<b>Year:</b> %{x}<br><b>PILT:</b> $%{y:,.2f}<extra></extra>'
                )
                
                st.plotly_chart(fig_trend, use_container_width=True)
                
                # Chart data download option
                st.markdown("**Export historical trend data:**")
                if st.button("Export Trend Data to CSV", key="trend_csv"):
                    csv_data = io.StringIO()
                    trend_data.to_csv(csv_data, index=False)
                    csv_data.seek(0)
                    st.download_button(
                        label="Download CSV",
                        data=csv_data.getvalue(),
                        file_name=f"pilt_trend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("Historical data does not contain required columns for trend visualization")

    with tab4:
        st.markdown("""
        <div style="background-color:#f0f8ff; padding:10px; border-radius:5px; margin-bottom:20px">
            <h2 style="color:#0077b6; text-align:center">What-If Scenario Analysis</h2>
            <p style="text-align:center">Simulate different scenarios to see how changes would affect PILT calculations</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.pilt_data is not None:
            st.markdown("""
            <div style="background-color:#e6f2ff; padding:15px; border-radius:5px; margin:10px 0px 20px 0px">
                <p style="font-size:16px">
                    Use the controls below to adjust key parameters and see how they would affect PILT calculations.
                    This tool allows you to:
                </p>
                <ul>
                    <li>Modify levy rates for each district</li>
                    <li>Adjust assessed values by a percentage</li>
                    <li>Apply custom deductions to specific districts</li>
                </ul>
                <p style="font-style:italic">
                    Once you've set your parameters, click "Run Scenario Analysis" to calculate the results.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
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
