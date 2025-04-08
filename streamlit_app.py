import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import comtradeapicall
import time
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import io


# Встановлення фіксованої назви файлу
JSON_FILENAME = 'tariff_data.json'


def display_phosphate_imports(data_df):
    st.subheader("Щомісячна візуалізація даних")
    
    # Перетворення періоду в дату та додавання колонки року
    data_df['date'] = pd.to_datetime(data_df['period'].astype(str), format='%Y%m')
    data_df['year'] = data_df['date'].dt.year
    
    # Визначаємо топ-3 країни-партнерів за вартістю імпорту
    partner_value = data_df.groupby('partnerDesc')['primaryValue'].sum().sort_values(ascending=False)
    top3_countries = partner_value.head(3).index.tolist()
    
    # Створюємо новий DataFrame для аналізу за роками
    yearly_data = data_df.groupby(['year', 'partnerDesc'])['netWgt'].sum().reset_index()
    
    # Конвертуємо кг в тис. тонн
    yearly_data['netWgt_thousand_tons'] = yearly_data['netWgt'] / 1000
    
    # Фільтруємо дані лише для топ-3 країн
    yearly_data_filtered = yearly_data[yearly_data['partnerDesc'].isin(top3_countries)]
    
    # Отримуємо унікальні роки для осі X
    years = sorted(data_df['year'].unique())
    
    # Створюємо фігуру для графіка
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    
    # Налаштування фону графіка
    ax.set_facecolor('white')
    
    # Параметри сітки
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    
    # Створюємо мапінг для типів НПК (замість країн)
    npk_types = {
        top3_countries[0]: 'DAP',  # Перша країна відповідає DAP
        top3_countries[1]: 'MAP',  # Друга країна відповідає MAP
        top3_countries[2]: 'NP'    # Третя країна відповідає NP
    }
    
  
    # Створюємо словник з кольорами для країн
    colors = {
        top3_countries[0]: 'red',
        top3_countries[1]: 'blue',
        top3_countries[2]: 'green'
    }
    
    
    # Налаштування осей
    max_value = yearly_data_filtered['netWgt_thousand_tons'].max() * 1.2
    ax.set_ylim(0, max_value)
    
    # Додаємо лінії для кожного типу НПК (замість країн)
    #for country, npk_type in npk_types.items():
    # Додаємо лінії для кожної країни
    for country in top3_countries:
        country_data = yearly_data_filtered[yearly_data_filtered['partnerDesc'] == country]
        data_by_year = country_data.set_index('year')['netWgt_thousand_tons']
        
        # Додаємо дані для всіх років (навіть тих, де немає імпорту)
        all_years_data = pd.Series(index=years, dtype=float)
        all_years_data.update(data_by_year)
        all_years_data = all_years_data.fillna(0)
        
        # Побудова лінії
        ax.plot(
            years, 
            all_years_data.values, 
            color=colors[country], 
            linewidth=2, 
            marker='o',
            markersize=6,
            label=country  # Використовуємо назви країни
        )
    
    # Налаштування розмітки осі X (роки)
    ax.set_xticks(years)
    
    # Додавання заголовка українською
    ax.set_title('ІМПОРТ ФОСФАТНИХ ДОБРИВ ДО  УКРАЇНА', fontsize=14, fontweight='bold', color='black')
    
    # Додавання підписів осей українською
    ax.set_ylabel('тис. тонн', fontsize=12, color='black')
    ax.set_xlabel('Рік', fontsize=12, color='black')
    
    # Прибираємо рамку навколо графіка для мінімалістичного дизайну
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    # Додавання легенди
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    
    # Налаштування макету для кращого відображення
    plt.tight_layout()
    
    # Показ графіка у Streamlit
    st.pyplot(fig)
    
    # Додаємо опцію завантаження графіка
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight', facecolor='white')
    buf.seek(0)
    
    st.download_button(
        label="Завантажити графік",
        data=buf,
        file_name="імпорт_фосфатних_добрив_за_типами.png",
        mime="image/png"
    )

    # Відображення таблиці з даними
    if st.checkbox("Показати дані у табличному форматі"):
        st.write("Дані про імпорт фосфатних добрив (тис. тонн):")
        pivot_table = yearly_data_filtered.pivot(index='year', columns='partnerDesc', values='netWgt_thousand_tons').fillna(0)
        # Перейменовуємо колонки з назв країн на типи добрив
        pivot_table = pivot_table.rename(columns=npk_types)
        st.dataframe(pivot_table)


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
        
        # Save to JSON file
        with open(JSON_FILENAME, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': results,
                'data': data_for_json
            }, f, ensure_ascii=False, indent=4)
        
        # Show success message
        st.success(f"Data retrieved successfully for commodity code {commodity_code}")
        st.info(f"Rows retrieved: {results['total_rows']}")
        st.info(f"Execution time: {execution_time:.2f} seconds")
        st.info(f"File saved: {JSON_FILENAME}")
        
        return panDForig, results
    
    except Exception as e:
        st.error(f"Error retrieving data: {str(e)}")
        return pd.DataFrame(), {'error': str(e)}

# Function to analyze NPK fertilizer data by year
def analyze_npk_import_by_year(data_df):
    # Check if we have the required columns
    if 'statPeriod' in data_df.columns and 'primaryValue' in data_df.columns:
        # Convert statPeriod to datetime
        data_df['date'] = pd.to_datetime(data_df['statPeriod'], format='%Y%m')
        
        # Extract year
        data_df['year'] = data_df['date'].dt.year
        
        # Group by year and sum the primaryValue
        yearly_data = data_df.groupby('year')['primaryValue'].sum().reset_index()
        
        return yearly_data
    else:
        return pd.DataFrame()

# Function to create NPK import trend line chart by year
def plot_npk_yearly_trend(yearly_data):
    if not yearly_data.empty:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot the line
        ax.plot(yearly_data['year'], yearly_data['primaryValue'], marker='o', linestyle='-', linewidth=2, color='#3366cc')
        
        # Add data points and values
        for x, y in zip(yearly_data['year'], yearly_data['primaryValue']):
            ax.annotate(f"{y/1000000:.1f}M", 
                        (x, y),
                        textcoords="offset points", 
                        xytext=(0, 10), 
                        ha='center')
        
        # Set title and labels
        ax.set_title('Річний імпорт НПК добрив в Україну', fontsize=16)
        ax.set_xlabel('Рік', fontsize=12)
        ax.set_ylabel('Вартість (USD)', fontsize=12)
        
        # Format y-axis to show in millions
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'{x/1000000:.1f}M'))
        
        # Set grid
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Make sure years are integers on x-axis
        ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
        
        # Tight layout
        plt.tight_layout()
        
        return fig
    else:
        return None

# Function to load existing data from JSON file
def load_json_data():
    try:
        with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
            data_df = pd.DataFrame(json_data['data'])
            return data_df
    except Exception as e:
        st.warning(f"Could not load data from {JSON_FILENAME}: {str(e)}")
        return pd.DataFrame()

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

# Button to fetch data
if st.sidebar.button("Fetch Data"):
    if not subscription_key:
        st.sidebar.error("Please enter a valid API Subscription Key")
    elif not commodity_code:
        st.sidebar.error("Please enter a valid Commodity Code")
    else:
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Data", "Monthly Visualization", "Yearly NPK Import", "JSON"])
        
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
                st.subheader("Monthly Data Visualization")
                
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
            st.subheader("Річний розподіл імпорту НПК")
            
            # Check if we fetched NPK data (310520 code)
            if commodity_code == '310520' and not panDForig.empty:
                # Analyze NPK data by year
                yearly_data = analyze_npk_import_by_year(panDForig)
                
                if not yearly_data.empty:
                    # Display yearly data table
                    st.subheader("Річні дані імпорту НПК")
                    
                    # Format yearly data for display
                    display_data = yearly_data.copy()
                    display_data['primaryValue (USD)'] = display_data['primaryValue'].apply(lambda x: f"${x:,.2f}")
                    display_data['primaryValue (Million USD)'] = display_data['primaryValue'].apply(lambda x: f"${x/1000000:.2f}M")
                    display_data = display_data.rename(columns={'year': 'Рік', 'primaryValue': 'Вартість (USD)'})
                    
                    st.dataframe(display_data[['Рік', 'primaryValue (USD)', 'primaryValue (Million USD)']])
                    
                    # Create and display yearly trend plot
                    fig_yearly = plot_npk_yearly_trend(yearly_data)
                    if fig_yearly:
                        st.pyplot(fig_yearly)
                    
                    # Download yearly data as CSV
                    csv_yearly = yearly_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download yearly NPK data as CSV",
                        data=csv_yearly,
                        file_name='npk_yearly_import_data.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning("Could not process yearly NPK import data")
            else:
                # Try to load existing NPK data from JSON file
                if commodity_code != '310520':
                    st.info("This tab shows yearly NPK fertilizer import data. Please select commodity code 310520 and fetch data to see NPK analysis.")
                    
                    # Try to load existing NPK data from JSON file
                    try:
                        with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
                            json_data = json.load(f)
                            # Check if the loaded data is for NPK fertilizers
                            if json_data.get('metadata', {}).get('commodity_code') == '310520':
                                data_df = pd.DataFrame(json_data['data'])
                                yearly_data = analyze_npk_import_by_year(data_df)
                                
                                if not yearly_data.empty:
                                    st.success("Showing previously loaded NPK data from JSON file")
                                    
                                    # Display yearly data table
                                    st.subheader("Річні дані імпорту НПК")
                                    
                                    # Format yearly data for display
                                    display_data = yearly_data.copy()
                                    display_data['primaryValue (USD)'] = display_data['primaryValue'].apply(lambda x: f"${x:,.2f}")
                                    display_data['primaryValue (Million USD)'] = display_data['primaryValue'].apply(lambda x: f"${x/1000000:.2f}M")
                                    display_data = display_data.rename(columns={'year': 'Рік', 'primaryValue': 'Вартість (USD)'})
                                    
                                    st.dataframe(display_data[['Рік', 'primaryValue (USD)', 'primaryValue (Million USD)']])
                                    
                                    # Create and display yearly trend plot
                                    fig_yearly = plot_npk_yearly_trend(yearly_data)
                                    if fig_yearly:
                                        st.pyplot(fig_yearly)
                            else:
                                st.warning("No NPK data found in the JSON file. Please fetch data for commodity code 310520.")
                    except Exception as e:
                        st.warning(f"Could not load NPK data from JSON file: {str(e)}")
        
        with tab4:
            if not panDForig.empty:
                st.subheader("JSON Data")
                st.json({
                    'metadata': results,
                    'data': panDForig.head(10).to_dict(orient='records')  # Show only first 10 records to keep it manageable
                })
            else:
                # Try to load existing data from JSON file
                try:
                    with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                        st.json({
                            'metadata': json_data.get('metadata', {}),
                            'data': json_data.get('data', [])[:10]  # Show only first 10 records
                        })
                except Exception as e:
                    st.warning(f"Could not load data from JSON file: {str(e)}")

# Add button to load existing data from JSON without API call
if st.sidebar.button("Load Data From JSON"):
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["Data", "Monthly Visualization", "Yearly NPK Import", "JSON"])
    
    # Load data from JSON file
    data_df = load_json_data()
    
    if not data_df.empty:
        # Get commodity code from loaded data
        loaded_commodity_code = data_df['cmdCode'].iloc[0] if 'cmdCode' in data_df.columns else "Unknown"
        
        with tab1:
            # Show data
            st.subheader(f"Loaded Data for Commodity Code {loaded_commodity_code}")
            st.dataframe(data_df)
            
            # Download options
            csv = data_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download data as CSV",
                data=csv,
                file_name=f'tariff_data_{loaded_commodity_code}.csv',
                mime='text/csv',
            )
        
        with tab2:
            st.subheader("Monthly Data Visualization")

            # Відображаємо візуалізацію
            display_phosphate_imports(data_df)

            
             
            

                    
            
        
        with tab3:
            st.subheader("Річний розподіл імпорту НПК")
            
            # Check if loaded data is NPK data (310520 code)
            if loaded_commodity_code == '310520':
                # Analyze NPK data by year
                yearly_data = analyze_npk_import_by_year(data_df)
                
                if not yearly_data.empty:
                    # Display yearly data table
                    st.subheader("Річні дані імпорту НПК")
                    
                    # Format yearly data for display
                    display_data = yearly_data.copy()
                    display_data['primaryValue (USD)'] = display_data['primaryValue'].apply(lambda x: f"${x:,.2f}")
                    display_data['primaryValue (Million USD)'] = display_data['primaryValue'].apply(lambda x: f"${x/1000000:.2f}M")
                    display_data = display_data.rename(columns={'year': 'Рік', 'primaryValue': 'Вартість (USD)'})
                    
                    st.dataframe(display_data[['Рік', 'primaryValue (USD)', 'primaryValue (Million USD)']])
                    
                    # Create and display yearly trend plot
                    fig_yearly = plot_npk_yearly_trend(yearly_data)
                    if fig_yearly:
                        st.pyplot(fig_yearly)
                    
                    # Download yearly data as CSV
                    csv_yearly = yearly_data.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Download yearly NPK data as CSV",
                        data=csv_yearly,
                        file_name='npk_yearly_import_data.csv',
                        mime='text/csv',
                    )
                else:
                    st.warning("Could not process yearly NPK import data")
            else:
                st.info("This tab shows yearly NPK fertilizer import data. Please load data for commodity code 310520 to see NPK analysis.")
        
        with tab4:
            st.subheader("JSON Data")
            
            try:
                with open(JSON_FILENAME, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    st.json({
                        'metadata': json_data.get('metadata', {}),
                        'data': json_data.get('data', [])[:10]  # Show only first 10 records
                    })
            except Exception as e:
                st.warning(f"Could not load JSON data: {str(e)}")
    else:
        st.warning(f"No data found in {JSON_FILENAME}")

# Add information about the app
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    """
    This app uses the UN Comtrade API to fetch tariff line data for Ukraine imports.
    
    You need a valid subscription key to use this app.
    
    The data is fetched for monthly periods between the selected start and end dates.
    
    The NPK Import tab shows yearly analysis for NPK fertilizers (commodity code 310520).
    """
)