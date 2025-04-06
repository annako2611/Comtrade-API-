import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import comtradeapicall
import time
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Встановлення фіксованої назви файлу
JSON_FILENAME = 'tariff_data.json'


# Set page title and configure layout
st.set_page_config(page_title="UN Comtrade Data Retrieval", layout="wide")

# Add a title and description
st.title("UN Comtrade Tariff Line Data Retriever")
st.markdown("This app allows you to retrieve tariff line data from the UN Comtrade API for Ukraine imports.")

# Function to get tariff line data with error handling
def get_tariff_line_data(comtradeapicall, subscription_key, period_string, commodity_code):
    try:
        # Start measuring time
        start_time = time.time()
        
        with st.spinner(f'Fetching data for commodity code {commodity_code}...'):
            # Execute query
            panDForig = comtradeapicall._getTarifflineData(
                subscription_key, 
                typeCode='C',           # data type 
                freqCode='M',           # monthly data
                clCode='HS',            # Harmonized System classification
                period=period_string,   # time period
                reporterCode=804,       # Ukraine code in UN Comtrade (804)
                cmdCode=commodity_code, # specific commodity code
                flowCode='M',           # trade flow direction (Import)
                partnerCode=None, 
                partner2Code=None, 
                customsCode=None, 
                motCode=None, 
                maxRecords=None,
                format_output='JSON',   # JSON format
                countOnly=None, 
                includeDesc=True        # include descriptions
            )
        
        # End time measurement
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Prepare results
        results = {
            'commodity_code': commodity_code,
            'total_rows': len(panDForig),
            'execution_time': execution_time,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Convert DataFrame to list of dictionaries for serialization
        data_for_json = panDForig.to_dict(orient='records')
        
       
        
        with open(JSON_FILENAME, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': results,
                'data': data_for_json
            }, f, ensure_ascii=False, indent=4)
        
        # Show success message
        st.success(f"Data retrieved successfully for commodity code {commodity_code}")
        st.info(f"Rows retrieved: {results['total_rows']}")
        st.info(f"Execution time: {execution_time:.2f} seconds")
        st.info(f"File saved: {output_filename}")
        
        return panDForig, results
    
    except Exception as e:
        st.error(f"Error retrieving data: {str(e)}")
        return pd.DataFrame(), {'error': str(e)}

# Sidebar for input parameters
st.sidebar.header("Parameters")

# API Key input
subscription_key = "ede51c36a7db4b639bf9f220416e0f1f"


# Commodity code input with examples
commodity_code_examples = {
    '310520': 'Mineral or chemical fertilizers containing N, P and K',
    '870321': 'Passenger vehicles with spark-ignition engine of cylinder capacity <= 1,000 cc',
    '300490': 'Medicaments consisting of mixed or unmixed products for therapeutic or prophylactic purposes',
    '851712': 'Telephones for cellular networks or other wireless networks'
}

selected_example = st.sidebar.selectbox(
    "Select example commodity code",
    list(commodity_code_examples.keys()),
    format_func=lambda x: f"{x} - {commodity_code_examples[x]}"
)

commodity_code = st.sidebar.text_input("Commodity Code (HS Code)", value=selected_example)

# Date range selection
st.sidebar.subheader("Time Period Selection")
min_date = datetime(2015, 1, 1)
max_date = datetime(2025, 4, 1)
default_start = datetime(2019, 1, 1)
default_end = datetime(2023, 12, 31)

start_date = st.sidebar.date_input("Start Date", default_start, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", default_end, min_value=start_date, max_value=max_date)

if start_date >= end_date:
    st.sidebar.error("End date must be greater than start date")

# Generate periods
periods = pd.date_range(start=start_date, end=end_date, freq='MS').strftime("%Y%m").tolist()
period_string = ",".join(periods)

# Show the period string
#st.sidebar.subheader("Generated Period String")
#st.sidebar.code(period_string)

# Button to fetch data
if st.sidebar.button("Fetch Data"):
    if not subscription_key:
        st.sidebar.error("Please enter a valid API Subscription Key")
    elif not commodity_code:
        st.sidebar.error("Please enter a valid Commodity Code")
    else:
        # Create tabs for different views
        tab1, tab2, tab3 = st.tabs(["Data", "Visualization", "JSON"])
        
        with tab1:
            # Fetch data
            panDForig, results = get_tariff_line_data(comtradeapicall, subscription_key, period_string, commodity_code)
            
            if not panDForig.empty:
                # Show data
                st.subheader("Retrieved Data")
                st.dataframe(panDForig)
                
                # Download options
                csv = panDForig.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name=f'tariff_data_{commodity_code}.csv',
                    mime='text/csv',
                )
        
        with tab2:
            if not panDForig.empty:
                st.subheader("Data Visualization")
                
                # Check if we have time period and trade value columns
                if 'statPeriod' in panDForig.columns and 'primaryValue' in panDForig.columns:
                    # Data preparation
                    viz_data = panDForig.copy()
                    viz_data['date'] = pd.to_datetime(viz_data['statPeriod'], format='%Y%m')
                    viz_data = viz_data.sort_values('date')
                    
                    # Create a time series plot
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(viz_data['date'], viz_data['primaryValue'], marker='o', linestyle='-')
                    ax.set_title(f'Import Value Over Time for Commodity Code {commodity_code}')
                    ax.set_xlabel('Date')
                    ax.set_ylabel('Value (USD)')
                    ax.grid(True)
                    
                    # Format x-axis to show dates nicely
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    
                    # Display plot
                    st.pyplot(fig)
                    
                    # Summary statistics
                    st.subheader("Summary Statistics")
                    st.write(viz_data['primaryValue'].describe())
                    
                    # Monthly average
                    monthly_avg = viz_data.groupby(viz_data['date'].dt.strftime('%B'))['primaryValue'].mean()
                    st.subheader("Monthly Average Import Value")
                    
                    # Create a bar chart for monthly average
                    fig2, ax2 = plt.subplots(figsize=(10, 5))
                    monthly_avg.plot(kind='bar', ax=ax2)
                    ax2.set_title('Average Import Value by Month')
                    ax2.set_ylabel('Average Value (USD)')
                    plt.tight_layout()
                    
                    st.pyplot(fig2)
                else:
                    st.warning("Data does not contain expected columns for visualization")
        
        with tab3:
            if not panDForig.empty:
                st.subheader("JSON Data")
                st.json({
                    'metadata': results,
                    'data': panDForig.head(10).to_dict(orient='records')  # Show only first 10 records to keep it manageable
                })

# Add information about the app
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    """
    This app uses the UN Comtrade API to fetch tariff line data for Ukraine imports.
    
    You need a valid subscription key to use this app.
    
    The data is fetched for monthly periods between the selected start and end dates.
    """
)
