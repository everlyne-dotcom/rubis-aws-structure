import streamlit as st
import boto3
import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="Fuel Quality LLM Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced database setup
def setup_enhanced_db():
    conn = sqlite3.connect('enhanced_fuel_quality.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS enhanced_fuel_data (
            id INTEGER PRIMARY KEY,
            sensor_id TEXT,
            timestamp TEXT,
            temperature_c REAL,
            density_kg_per_m3 REAL,
            water_ppm REAL,
            carbon_ppm REAL,
            sediment_ppm REAL,
            fuel_level_liters INTEGER,
            batch_quality TEXT,
            comments TEXT,
            content TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def load_enhanced_data():
    """Load enhanced fuel data into database"""
    try:
        with open('enhanced_fuel_data.json', 'r') as f:
            data = json.load(f)
        
        conn = sqlite3.connect('enhanced_fuel_quality.db')
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM enhanced_fuel_data')
        
        for item in data:
            cursor.execute('''
                INSERT INTO enhanced_fuel_data 
                (sensor_id, timestamp, temperature_c, density_kg_per_m3, water_ppm, 
                 carbon_ppm, sediment_ppm, fuel_level_liters, batch_quality, comments, content)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item['sensor_id'], item['timestamp'], item['temperature_c'],
                item['density_kg_per_m3'], item['water_ppm'], item['carbon_ppm'],
                item['sediment_ppm'], item['fuel_level_liters'], item['batch_quality'],
                item['comments'], item['content']
            ))
        
        conn.commit()
        conn.close()
        return len(data)
    except FileNotFoundError:
        return 0

# Initialize enhanced database
setup_enhanced_db()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #232F3E 0%, #FF9900 100%);
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 2rem;
    }
    .sensor-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9900;
        margin-bottom: 1rem;
    }
    .status-normal { background-color: #d4edda; border-left-color: #28a745; }
    .status-warning { background-color: #fff3cd; border-left-color: #ffc107; }
    .status-critical { background-color: #f8d7da; border-left-color: #dc3545; }
    .comment-box {
        background: #e9ecef;
        padding: 0.5rem;
        border-radius: 4px;
        font-style: italic;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header"><h1>🛢️ Enhanced Fuel Quality Dashboard</h1></div>', 
            unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", [
    "📊 Dashboard", 
    "📡 Live Feed", 
    "🔍 Detailed Records",
    "🤖 AI Analysis"
])

# Load data button
if st.sidebar.button("🔄 Load Enhanced Data"):
    count = load_enhanced_data()
    if count > 0:
        st.sidebar.success(f"Loaded {count} enhanced records")
    else:
        st.sidebar.error("No enhanced data found. Run enhanced_fuel_generator.py first")

# Dashboard Page
if page == "📊 Dashboard":
    st.header("Enhanced Dashboard Overview")
    
    conn = sqlite3.connect('enhanced_fuel_quality.db')
    
    # Key metrics
    metrics_query = """
        SELECT 
            COUNT(DISTINCT sensor_id) as total_sensors,
            COUNT(*) as total_readings,
            AVG(temperature_c) as avg_temp,
            AVG(density_kg_per_m3) as avg_density,
            AVG(water_ppm) as avg_water,
            SUM(CASE WHEN batch_quality = 'CONTAMINATED' THEN 1 ELSE 0 END) as contaminated_count
        FROM enhanced_fuel_data
    """
    metrics = pd.read_sql_query(metrics_query, conn)
    
    if not metrics.empty and metrics['total_readings'].iloc[0] > 0:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            contamination_rate = (metrics['contaminated_count'].iloc[0] / metrics['total_readings'].iloc[0]) * 100
            st.metric("Contamination Rate", f"{contamination_rate:.1f}%")
        
        with col2:
            st.metric("Active Sensors", int(metrics['total_sensors'].iloc[0]))
        
        with col3:
            st.metric("Avg Temperature", f"{metrics['avg_temp'].iloc[0]:.1f}°C")
        
        with col4:
            st.metric("Avg Water Content", f"{metrics['avg_water'].iloc[0]:.1f} ppm")
        
        # Charts
        chart_data = pd.read_sql_query("""
            SELECT sensor_id, temperature_c, density_kg_per_m3, water_ppm, batch_quality
            FROM enhanced_fuel_data
        """, conn)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.scatter(chart_data, x='temperature_c', y='density_kg_per_m3', 
                            color='batch_quality', title='Temperature vs Density',
                            color_discrete_map={'CLEAN': 'green', 'CONTAMINATED': 'red'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.box(chart_data, x='batch_quality', y='water_ppm', 
                         title='Water Content Distribution')
            st.plotly_chart(fig2, use_container_width=True)
    
    conn.close()

# Live Feed Page
elif page == "📡 Live Feed":
    st.header("Live Sensor Feed")
    
    conn = sqlite3.connect('enhanced_fuel_quality.db')
    live_data = pd.read_sql_query("""
        SELECT * FROM enhanced_fuel_data 
        ORDER BY id DESC 
        LIMIT 10
    """, conn)
    conn.close()
    
    for idx, row in live_data.iterrows():
        # Determine status class
        status_class = "status-critical" if row['batch_quality'] == 'CONTAMINATED' else "status-normal"
        
        st.markdown(f'''
        <div class="sensor-card {status_class}">
            <h4>🔧 {row['sensor_id']} - {row['batch_quality']}</h4>
            <p><strong>Timestamp:</strong> {row['timestamp']}</p>
            
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem;">
                <div>
                    <strong>Temperature:</strong> {row['temperature_c']}°C<br>
                    <strong>Density:</strong> {row['density_kg_per_m3']} kg/m³
                </div>
                <div>
                    <strong>Water:</strong> {row['water_ppm']} ppm<br>
                    <strong>Carbon:</strong> {row['carbon_ppm']} ppm
                </div>
                <div>
                    <strong>Sediment:</strong> {row['sediment_ppm']} ppm<br>
                    <strong>Fuel Level:</strong> {row['fuel_level_liters']:,} L
                </div>
            </div>
            
            <div class="comment-box">
                <strong>Analysis:</strong> {row['comments']}
            </div>
        </div>
        ''', unsafe_allow_html=True)

# Detailed Records Page
elif page == "🔍 Detailed Records":
    st.header("Detailed Sensor Records")
    
    conn = sqlite3.connect('enhanced_fuel_quality.db')
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        sensors = pd.read_sql_query("SELECT DISTINCT sensor_id FROM enhanced_fuel_data", conn)['sensor_id'].tolist()
        selected_sensor = st.selectbox("Filter by Sensor", ["All"] + sensors)
    
    with col2:
        quality_filter = st.selectbox("Quality Status", ["All", "CLEAN", "CONTAMINATED"])
    
    with col3:
        sort_by = st.selectbox("Sort by", ["timestamp", "temperature_c", "water_ppm"])
    
    # Build query
    query = "SELECT * FROM enhanced_fuel_data WHERE 1=1"
    if selected_sensor != "All":
        query += f" AND sensor_id = '{selected_sensor}'"
    if quality_filter != "All":
        query += f" AND batch_quality = '{quality_filter}'"
    query += f" ORDER BY {sort_by} DESC"
    
    detailed_data = pd.read_sql_query(query, conn)
    conn.close()
    
    # Display detailed records
    for idx, row in detailed_data.iterrows():
        with st.expander(f"📊 {row['sensor_id']} - {row['timestamp']} ({row['batch_quality']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Sensor Readings")
                st.write(f"**Temperature:** {row['temperature_c']}°C")
                st.write(f"**Density:** {row['density_kg_per_m3']} kg/m³")
                st.write(f"**Water Content:** {row['water_ppm']} ppm")
                st.write(f"**Carbon Residue:** {row['carbon_ppm']} ppm")
                st.write(f"**Sediment:** {row['sediment_ppm']} ppm")
                st.write(f"**Fuel Level:** {row['fuel_level_liters']:,} liters")
            
            with col2:
                st.subheader("Analysis & Comments")
                st.write(f"**Quality Status:** {row['batch_quality']}")
                st.text_area("Detailed Analysis:", value=row['comments'], height=150, disabled=True)
                
                # Quality indicators
                if row['batch_quality'] == 'CONTAMINATED':
                    st.error("⚠️ CONTAMINATION DETECTED - Immediate action required")
                else:
                    st.success("✅ Quality parameters within acceptable range")

# AI Analysis Page
elif page == "🤖 AI Analysis":
    st.header("AI-Powered Fuel Analysis")
    
    # RAG Query Interface
    st.subheader("Ask Questions About Fuel Quality")
    
    user_question = st.text_input("Enter your question:", 
                                 placeholder="e.g., What sensors show high water content?")
    
    if st.button("🔍 Analyze") and user_question:
        with st.spinner("AI is analyzing fuel data..."):
            # Simple analysis based on enhanced data
            conn = sqlite3.connect('enhanced_fuel_quality.db')
            
            if "water" in user_question.lower():
                high_water = pd.read_sql_query("""
                    SELECT sensor_id, water_ppm, comments 
                    FROM enhanced_fuel_data 
                    WHERE water_ppm > 50 
                    ORDER BY water_ppm DESC
                """, conn)
                
                st.subheader("High Water Content Analysis")
                for _, row in high_water.iterrows():
                    st.warning(f"**{row['sensor_id']}**: {row['water_ppm']} ppm - {row['comments']}")
            
            elif "contaminated" in user_question.lower():
                contaminated = pd.read_sql_query("""
                    SELECT sensor_id, batch_quality, comments 
                    FROM enhanced_fuel_data 
                    WHERE batch_quality = 'CONTAMINATED'
                """, conn)
                
                st.subheader("Contaminated Fuel Analysis")
                for _, row in contaminated.iterrows():
                    st.error(f"**{row['sensor_id']}**: {row['comments']}")
            
            else:
                st.info("Try asking about 'water content', 'contaminated fuel', or specific sensor readings")
            
            conn.close()

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Enhanced Fuel Quality Dashboard**")
st.sidebar.markdown("Detailed sensor readings with AI analysis")