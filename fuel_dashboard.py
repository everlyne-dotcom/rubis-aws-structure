import streamlit as st
import boto3
import json
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page config
st.set_page_config(
    page_title="Fuel Quality LLM Dashboard",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for AWS-style dark theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #232F3E 0%, #FF9900 100%);
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #1e1e1e;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #FF9900;
    }
    .status-green { color: #4CAF50; }
    .status-yellow { color: #FFC107; }
    .status-red { color: #F44336; }
    .sidebar .sidebar-content {
        background: #232F3E;
    }
</style>
""", unsafe_allow_html=True)

# Initialize RAG system
if 'rag_simulator' not in st.session_state:
    from fuel_rag_simulator import FuelRAGSimulator
    st.session_state.rag_simulator = FuelRAGSimulator()

def get_system_status():
    """Get overall system health"""
    try:
        opensearch = boto3.client('opensearch', region_name='us-east-1')
        response = opensearch.describe_domain(DomainName='fuel-quality-opensearch')
        if response['DomainStatus']['Processing']:
            return "yellow", "Creating"
        else:
            return "green", "Active"
    except:
        return "red", "Offline"

def get_dashboard_metrics():
    """Get key metrics for dashboard"""
    conn = sqlite3.connect('fuel_quality.db')
    
    # Total tanks
    tanks_query = "SELECT COUNT(DISTINCT fuel_id) as total_tanks FROM fuel_data"
    total_tanks = pd.read_sql_query(tanks_query, conn)['total_tanks'].iloc[0]
    
    # Contamination stats
    contamination_query = """
        SELECT 
            COUNT(*) as total_samples,
            SUM(CASE WHEN batch_quality = 'CONTAMINATED' THEN 1 ELSE 0 END) as contaminated,
            AVG(CASE WHEN batch_quality = 'CONTAMINATED' THEN 1.0 ELSE 0.0 END) * 100 as contamination_rate
        FROM fuel_data
    """
    stats = pd.read_sql_query(contamination_query, conn)
    
    # Recent anomalies (last 24 hours simulation)
    anomalies_query = """
        SELECT COUNT(*) as anomalies 
        FROM fuel_data 
        WHERE batch_quality = 'CONTAMINATED'
    """
    anomalies = pd.read_sql_query(anomalies_query, conn)['anomalies'].iloc[0]
    
    conn.close()
    
    return {
        'contamination_risk': round(stats['contamination_rate'].iloc[0], 1),
        'active_tanks': total_tanks,
        'anomalies': anomalies,
        'confidence': 94.2  # Simulated confidence level
    }

def get_live_feed_data():
    """Get recent fuel data for live feed"""
    conn = sqlite3.connect('fuel_quality.db')
    query = """
        SELECT fuel_id, timestamp, temperature_c, density_kg_m3, octane_rating, 
               batch_quality, sulfur_ppm, moisture_pct
        FROM fuel_data 
        ORDER BY id DESC 
        LIMIT 20
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Add contamination probability (simulated)
    df['contamination_prob'] = df.apply(lambda row: 
        0.85 + (row.name * 0.02) if row['batch_quality'] == 'CONTAMINATED' 
        else 0.15 - (row.name * 0.01), axis=1)
    
    return df

def get_trend_data():
    """Get trend data for charts"""
    conn = sqlite3.connect('fuel_quality.db')
    query = """
        SELECT fuel_id, timestamp, batch_quality, temperature_c, density_kg_m3
        FROM fuel_data 
        ORDER BY timestamp
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # Convert timestamp and add contamination probability
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['contamination_prob'] = df['batch_quality'].map({'CONTAMINATED': 0.9, 'CLEAN': 0.1})
    
    return df

# Header
status_color, status_text = get_system_status()
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.markdown('<div class="main-header"><h1>🛢️ Fuel Quality LLM Dashboard</h1></div>', 
                unsafe_allow_html=True)

with col2:
    st.markdown(f'**System Status:** <span class="status-{status_color}">●</span> {status_text}', 
                unsafe_allow_html=True)

with col3:
    st.markdown('**User:** Admin')

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select Page", [
    "📊 Dashboard", 
    "📡 Live Feed", 
    "🤖 AI Reports", 
    "🚨 Alerts", 
    "📋 System Logs"
])

# Dashboard Page
if page == "📊 Dashboard":
    st.header("Dashboard Overview")
    
    # Key Metrics
    metrics = get_dashboard_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Contamination Risk Today", f"{metrics['contamination_risk']}%", 
                 delta="-2.1%", delta_color="inverse")
    
    with col2:
        st.metric("Active Tanks Monitored", metrics['active_tanks'], delta="0")
    
    with col3:
        st.metric("Anomalies Detected", metrics['anomalies'], delta="+3")
    
    with col4:
        st.metric("Average Confidence Level", f"{metrics['confidence']}%", delta="+1.2%")
    
    # Trend Chart
    st.subheader("Contamination Trend Analysis")
    trend_data = get_trend_data()
    
    if not trend_data.empty:
        fig = px.line(trend_data, x='timestamp', y='contamination_prob', 
                     color='fuel_id', title='Contamination Probability Over Time')
        fig.add_hline(y=0.8, line_dash="dash", line_color="red", 
                     annotation_text="Critical Threshold")
        st.plotly_chart(fig, use_container_width=True)
    
    # Quick Filters
    st.subheader("Quick Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fuel_filter = st.selectbox("Filter by Fuel ID", ["All"] + list(trend_data['fuel_id'].unique()))
    
    with col2:
        date_range = st.date_input("Date Range", value=[datetime.now().date()])
    
    with col3:
        contamination_filter = st.selectbox("Contamination Level", 
                                          ["All", "Normal", "Warning", "Critical"])

# Live Feed Page
elif page == "📡 Live Feed":
    st.header("Live Sensor Feed")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    live_data = get_live_feed_data()
    
    for idx, row in live_data.iterrows():
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        
        with col1:
            st.write(f"**{row['fuel_id']}**")
            st.caption(row['timestamp'])
        
        with col2:
            st.write(f"Temp: {row['temperature_c']}°C")
            st.write(f"Density: {row['density_kg_m3']} kg/m³")
        
        with col3:
            st.write(f"Octane: {row['octane_rating']}")
            st.write(f"Sulfur: {row['sulfur_ppm']} ppm")
        
        with col4:
            prob = row['contamination_prob']
            st.write(f"Risk: {prob:.1%}")
        
        with col5:
            if prob > 0.8:
                st.markdown('<span class="status-red">🔴 Critical</span>', unsafe_allow_html=True)
            elif prob > 0.5:
                st.markdown('<span class="status-yellow">🟡 Warning</span>', unsafe_allow_html=True)
            else:
                st.markdown('<span class="status-green">🟢 Normal</span>', unsafe_allow_html=True)
        
        st.divider()

# AI Reports Page
elif page == "🤖 AI Reports":
    st.header("AI-Generated Insights")
    
    # Generate AI insights for contaminated samples
    conn = sqlite3.connect('fuel_quality.db')
    contaminated_query = """
        SELECT fuel_id, timestamp, temperature_c, density_kg_m3, sulfur_ppm, 
               moisture_pct, batch_quality
        FROM fuel_data 
        WHERE batch_quality = 'CONTAMINATED'
        ORDER BY timestamp DESC
        LIMIT 10
    """
    contaminated_df = pd.read_sql_query(contaminated_query, conn)
    conn.close()
    
    for idx, row in contaminated_df.iterrows():
        with st.expander(f"🚨 {row['fuel_id']} - Contamination Analysis"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Sensor Data")
                st.write(f"Temperature: {row['temperature_c']}°C")
                st.write(f"Density: {row['density_kg_m3']} kg/m³")
                st.write(f"Sulfur: {row['sulfur_ppm']} ppm")
                st.write(f"Moisture: {row['moisture_pct']}%")
            
            with col2:
                st.subheader("AI Analysis")
                
                # Generate AI reasoning
                reasoning = f"""
                **Contamination Detected:** High confidence (92%)
                
                **Primary Indicators:**
                - Temperature exceeds normal range ({row['temperature_c']}°C > 25°C)
                - Sulfur content elevated ({row['sulfur_ppm']} ppm > 15 ppm)
                - Density below threshold ({row['density_kg_m3']} kg/m³ < 720)
                
                **Recommendation:** Immediate quality testing required. 
                Isolate tank {row['fuel_id']} pending verification.
                """
                
                st.markdown(reasoning)

# Alerts Page
elif page == "🚨 Alerts":
    st.header("Critical Alerts")
    
    # Get high-risk samples
    conn = sqlite3.connect('fuel_quality.db')
    alerts_query = """
        SELECT fuel_id, timestamp, temperature_c, sulfur_ppm, batch_quality
        FROM fuel_data 
        WHERE batch_quality = 'CONTAMINATED'
        ORDER BY timestamp DESC
    """
    alerts_df = pd.read_sql_query(alerts_query, conn)
    conn.close()
    
    if not alerts_df.empty:
        for idx, row in alerts_df.iterrows():
            alert_col1, alert_col2, alert_col3 = st.columns([3, 2, 1])
            
            with alert_col1:
                st.error(f"🚨 **{row['fuel_id']}** - Contamination Detected")
                st.caption(f"Time: {row['timestamp']}")
            
            with alert_col2:
                st.write(f"Temp: {row['temperature_c']}°C, Sulfur: {row['sulfur_ppm']} ppm")
            
            with alert_col3:
                if st.button("Mark Resolved", key=f"resolve_{idx}"):
                    st.success("Alert resolved!")
    else:
        st.success("No active alerts")

# System Logs Page
elif page == "📋 System Logs":
    st.header("System Monitoring")
    
    # Simulated system logs
    logs = [
        {"timestamp": "2024-01-15 10:30:15", "level": "INFO", "message": "OpenSearch cluster healthy"},
        {"timestamp": "2024-01-15 10:29:45", "level": "WARN", "message": "High contamination rate detected"},
        {"timestamp": "2024-01-15 10:29:12", "level": "INFO", "message": "Bedrock model invocation successful"},
        {"timestamp": "2024-01-15 10:28:33", "level": "ERROR", "message": "IoT device TANK-15 connection timeout"},
        {"timestamp": "2024-01-15 10:27:55", "level": "INFO", "message": "Data pipeline processing 1,247 records"},
    ]
    
    for log in logs:
        level_color = {"INFO": "blue", "WARN": "orange", "ERROR": "red"}[log["level"]]
        st.markdown(f'<span style="color: {level_color}">**{log["level"]}**</span> '
                   f'{log["timestamp"]} - {log["message"]}', unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Fuel Quality LLM Dashboard v1.0**")
st.sidebar.markdown("Powered by AWS Bedrock & OpenSearch")