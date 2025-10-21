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
    page_title="Fuel Quality LLM System",
    page_icon="🛢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# AWS Console-inspired dark theme
st.markdown("""
<style>
    .main {
        background-color: #1b1f23;
        color: #ffffff;
    }
    .stApp {
        background-color: #1b1f23;
    }
    .main-header {
        background: linear-gradient(90deg, #232F3E 0%, #FF9900 100%);
        padding: 1.5rem;
        border-radius: 8px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .metric-card {
        background: #2d3748;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #FF9900;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    .status-safe { 
        background: #2d5a3d; 
        border-left-color: #48bb78; 
        color: #68d391;
    }
    .status-moderate { 
        background: #5a4d2d; 
        border-left-color: #ed8936; 
        color: #fbb040;
    }
    .status-critical { 
        background: #5a2d2d; 
        border-left-color: #f56565; 
        color: #fc8181;
    }
    .alert-card {
        background: #2d3748;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 4px solid #f56565;
    }
    .ai-insight-card {
        background: #2a4365;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #4299e1;
        margin-bottom: 1rem;
    }
    .log-entry {
        font-family: 'Courier New', monospace;
        background: #1a202c;
        padding: 0.5rem;
        border-radius: 4px;
        margin-bottom: 0.5rem;
    }
    .log-info { color: #4299e1; }
    .log-warning { color: #ed8936; }
    .log-error { color: #f56565; }
    .sidebar .sidebar-content {
        background: #2d3748;
    }
    .stSelectbox > div > div {
        background-color: #2d3748;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced database
def setup_enhanced_db():
    conn = sqlite3.connect('fuel_quality_llm.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fuel_readings (
            id INTEGER PRIMARY KEY,
            fuel_id TEXT,
            timestamp TEXT,
            temperature_c REAL,
            density_kg_m3 REAL,
            octane_rating REAL,
            sulfur_ppm REAL,
            moisture_pct REAL,
            contamination_prob REAL,
            ai_confidence REAL,
            status TEXT,
            ai_reasoning TEXT,
            recommendation TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def generate_sample_data():
    """Generate sample data for demonstration"""
    import random
    
    conn = sqlite3.connect('fuel_quality_llm.db')
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute('DELETE FROM fuel_readings')
    
    fuel_ids = [f"T-{str(i).zfill(3)}" for i in range(1, 19)]
    
    for i in range(100):
        fuel_id = random.choice(fuel_ids)
        is_contaminated = random.random() < 0.15
        
        if is_contaminated:
            temp = round(random.uniform(35, 50), 1)
            density = round(random.uniform(650, 700), 1)
            octane = round(random.uniform(75, 85), 1)
            sulfur = round(random.uniform(50, 150), 1)
            moisture = round(random.uniform(0.15, 0.30), 3)
            contam_prob = round(random.uniform(0.7, 0.95), 2)
            status = "Critical" if contam_prob > 0.8 else "Moderate"
            reasoning = f"Detected excess moisture ({moisture}%) and elevated sulfur ({sulfur} ppm). Temperature anomaly at {temp}°C indicates thermal stress."
            recommendation = "Immediate tank isolation required. Schedule filtration and quality testing."
        else:
            temp = round(random.uniform(15, 25), 1)
            density = round(random.uniform(720, 780), 1)
            octane = round(random.uniform(87, 95), 1)
            sulfur = round(random.uniform(5, 15), 1)
            moisture = round(random.uniform(0.01, 0.05), 3)
            contam_prob = round(random.uniform(0.05, 0.25), 2)
            status = "Safe"
            reasoning = f"All parameters within specification. Density {density} kg/m³ and sulfur {sulfur} ppm are optimal."
            recommendation = "Continue normal operations. Next scheduled inspection in 24 hours."
        
        cursor.execute('''
            INSERT INTO fuel_readings 
            (fuel_id, timestamp, temperature_c, density_kg_m3, octane_rating, 
             sulfur_ppm, moisture_pct, contamination_prob, ai_confidence, 
             status, ai_reasoning, recommendation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fuel_id, datetime.now().isoformat(),
            temp, density, octane, sulfur, moisture, contam_prob,
            round(random.uniform(88, 98), 1), status, reasoning, recommendation
        ))
    
    conn.commit()
    conn.close()

# Initialize database and generate sample data if empty
setup_enhanced_db()

# Auto-generate sample data if database is empty
conn = sqlite3.connect('fuel_quality_llm.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM fuel_readings')
count = cursor.fetchone()[0]
conn.close()

if count == 0:
    generate_sample_data()

# Header
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    st.markdown('''
    <div class="main-header">
        <h1>🛢️ Fuel Quality LLM System</h1>
        <p>Autonomous LLM-powered monitoring of refinery and transport fuel quality</p>
    </div>
    ''', unsafe_allow_html=True)

with col2:
    # System health indicator
    health_status = "🟢 Active"
    st.markdown(f"**System Status:** {health_status}")

with col3:
    st.markdown("**User:** Admin ⚙️")

# Sidebar Navigation
st.sidebar.markdown("### 🧭 Navigation")
page = st.sidebar.selectbox("", [
    "📊 Dashboard",
    "📡 Live Feed", 
    "🤖 AI Reports",
    "🚨 Alerts",
    "📋 System Logs"
], label_visibility="collapsed")

# Generate sample data button
if st.sidebar.button("🔄 Generate Sample Data"):
    generate_sample_data()
    st.sidebar.success("Sample data generated!")

# Dashboard Page
if page == "📊 Dashboard":
    st.markdown("## Fuel Quality Intelligence Overview")
    st.markdown("*Autonomous LLM-powered monitoring of refinery and transport fuel quality*")
    
    conn = sqlite3.connect('fuel_quality_llm.db')
    
    # Key Metrics Cards
    metrics_query = """
        SELECT 
            AVG(contamination_prob) * 100 as avg_contamination,
            COUNT(DISTINCT fuel_id) as active_tanks,
            SUM(CASE WHEN status = 'Critical' THEN 1 ELSE 0 END) as anomalies,
            AVG(ai_confidence) as avg_confidence
        FROM fuel_readings
    """
    metrics = pd.read_sql_query(metrics_query, conn)
    
    if not metrics.empty:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_contamination = metrics["avg_contamination"].iloc[0] or 0
            st.markdown(f'''
            <div class="metric-card">
                <h3>Contamination Risk Index</h3>
                <h2>{avg_contamination:.1f}%</h2>
                <p>Average contamination probability</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col2:
            active_tanks = metrics["active_tanks"].iloc[0] or 0
            st.markdown(f'''
            <div class="metric-card">
                <h3>Active Tanks Monitored</h3>
                <h2>{int(active_tanks)}</h2>
                <p>Total tanks streaming data</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col3:
            anomalies = metrics["anomalies"].iloc[0] or 0
            st.markdown(f'''
            <div class="metric-card">
                <h3>Anomalies Detected (24h)</h3>
                <h2>{int(anomalies)}</h2>
                <p>Critical readings identified</p>
            </div>
            ''', unsafe_allow_html=True)
        
        with col4:
            avg_confidence = metrics["avg_confidence"].iloc[0] or 0
            st.markdown(f'''
            <div class="metric-card">
                <h3>AI Confidence Level</h3>
                <h2>{avg_confidence:.0f}%</h2>
                <p>Average reasoning confidence</p>
            </div>
            ''', unsafe_allow_html=True)
    
    # Trend Visualization
    st.markdown("### 📈 Contamination Trend Analysis")
    
    # Quick Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        fuel_ids = pd.read_sql_query("SELECT DISTINCT fuel_id FROM fuel_readings", conn)['fuel_id'].tolist()
        selected_fuel = st.selectbox("Fuel ID", ["All"] + fuel_ids)
    
    with col2:
        contamination_level = st.selectbox("Contamination Level", ["All", "Safe", "Moderate", "Critical"])
    
    with col3:
        time_range = st.selectbox("Time Range", ["Last 1h", "Last 24h", "Last 7d"])
    
    # Trend Chart
    chart_data = pd.read_sql_query("""
        SELECT fuel_id, contamination_prob, timestamp, status
        FROM fuel_readings 
        ORDER BY timestamp
    """, conn)
    
    if not chart_data.empty:
        fig = px.line(chart_data, x='timestamp', y='contamination_prob', 
                     color='fuel_id', title='Contamination Probability Over Time')
        fig.add_hline(y=0.7, line_dash="dash", line_color="orange", 
                     annotation_text="Warning Threshold")
        fig.add_hline(y=0.8, line_dash="dash", line_color="red", 
                     annotation_text="Critical Threshold")
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # AI Insight Panel
    st.markdown("### 🧠 AI Insights Summary")
    insights = pd.read_sql_query("""
        SELECT fuel_id, ai_reasoning, ai_confidence
        FROM fuel_readings 
        WHERE status = 'Critical'
        ORDER BY contamination_prob DESC
        LIMIT 3
    """, conn)
    
    for _, insight in insights.iterrows():
        st.markdown(f'''
        <div class="ai-insight-card">
            <h4>Tank {insight['fuel_id']} Analysis (Confidence: {insight['ai_confidence']:.0f}%)</h4>
            <p>{insight['ai_reasoning']}</p>
        </div>
        ''', unsafe_allow_html=True)
    
    conn.close()

# Live Feed Page
elif page == "📡 Live Feed":
    st.markdown("## 📡 Real-Time Sensor Stream")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (5s)")
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    conn = sqlite3.connect('fuel_quality_llm.db')
    live_data = pd.read_sql_query("""
        SELECT * FROM fuel_readings 
        ORDER BY id DESC 
        LIMIT 15
    """, conn)
    conn.close()
    
    # Live Feed Table
    st.markdown("### Latest Readings")
    
    for _, row in live_data.iterrows():
        status_class = f"status-{row['status'].lower()}"
        status_emoji = {"Safe": "🟢", "Moderate": "🟡", "Critical": "🔴"}[row['status']]
        
        col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
        
        with col1:
            st.markdown(f"**{row['fuel_id']}**")
            st.caption(f"Temp: {row['temperature_c']}°C")
        
        with col2:
            st.write(f"Density: {row['density_kg_m3']} kg/m³")
            st.caption(f"Octane: {row['octane_rating']}")
        
        with col3:
            st.write(f"Sulfur: {row['sulfur_ppm']} ppm")
            st.caption(f"Moisture: {row['moisture_pct']}%")
        
        with col4:
            st.write(f"Contamination: {row['contamination_prob']:.2f}")
            st.caption(f"Confidence: {row['ai_confidence']:.0f}%")
        
        with col5:
            st.markdown(f"{status_emoji} {row['status']}")
        
        st.divider()

# AI Reports Page
elif page == "🤖 AI Reports":
    st.markdown("## 🤖 LLM Analysis Reports")
    
    # Download options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        report_format = st.selectbox("Format", ["CSV", "JSON", "PDF Summary"])
    with col3:
        if st.button("📥 Download Reports"):
            conn = sqlite3.connect('fuel_quality_llm.db')
            all_reports = pd.read_sql_query("SELECT * FROM fuel_readings ORDER BY contamination_prob DESC", conn)
            conn.close()
            
            if report_format == "CSV":
                csv = all_reports.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"fuel_quality_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            elif report_format == "JSON":
                json_data = all_reports.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name=f"fuel_quality_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            elif report_format == "PDF Summary":
                # Generate PDF summary text
                critical_count = len(all_reports[all_reports['status'] == 'Critical'])
                avg_contamination = all_reports['contamination_prob'].mean() * 100
                
                pdf_content = f"""FUEL QUALITY ANALYSIS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

EXECUTIVE SUMMARY:
- Total Readings: {len(all_reports)}
- Critical Alerts: {critical_count}
- Average Contamination Risk: {avg_contamination:.1f}%

CRITICAL FINDINGS:
"""
                
                critical_reports = all_reports[all_reports['status'] == 'Critical'].head(5)
                for _, report in critical_reports.iterrows():
                    pdf_content += f"\nTank {report['fuel_id']}:\n- Contamination Probability: {report['contamination_prob']:.2f}\n- AI Analysis: {report['ai_reasoning'][:100]}...\n- Recommendation: {report['recommendation'][:100]}...\n"
                
                st.download_button(
                    label="Download PDF Summary",
                    data=pdf_content,
                    file_name=f"fuel_quality_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    conn = sqlite3.connect('fuel_quality_llm.db')
    reports = pd.read_sql_query("""
        SELECT * FROM fuel_readings 
        ORDER BY contamination_prob DESC
        LIMIT 10
    """, conn)
    conn.close()
    
    for _, report in reports.iterrows():
        with st.expander(f"Tank {report['fuel_id']} · Contamination: {report['contamination_prob']:.2f} · AI Confidence: {report['ai_confidence']:.0f}%"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Sensor Snapshot**")
                st.json({
                    "temperature_c": report['temperature_c'],
                    "density_kg_m3": report['density_kg_m3'],
                    "octane_rating": report['octane_rating'],
                    "sulfur_ppm": report['sulfur_ppm'],
                    "moisture_pct": report['moisture_pct']
                })
                
                st.markdown("**SageMaker Inference**")
                st.write(f"Contamination Probability: {report['contamination_prob']:.2f}")
                st.write(f"Status: {report['status']}")
            
            with col2:
                st.markdown("**Bedrock Reasoning Summary**")
                st.write(report['ai_reasoning'])
                
                st.markdown("**Recommendation**")
                st.info(report['recommendation'])
                
                st.caption(f"Generated on {report['timestamp']} via Bedrock AgentCore v2.1")

# Alerts Page
elif page == "🚨 Alerts":
    st.markdown("## 🚨 Active Alerts")
    
    conn = sqlite3.connect('fuel_quality_llm.db')
    
    # Alert Summary
    alert_summary = pd.read_sql_query("""
        SELECT 
            SUM(CASE WHEN status = 'Critical' THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN status = 'Moderate' THEN 1 ELSE 0 END) as moderate,
            COUNT(*) as total
        FROM fuel_readings
    """, conn)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔴 Critical Alerts", int(alert_summary['critical'].iloc[0]))
    with col2:
        st.metric("🟡 Moderate Alerts", int(alert_summary['moderate'].iloc[0]))
    with col3:
        st.metric("📊 Total Readings", int(alert_summary['total'].iloc[0]))
    
    # Critical Alerts
    critical_alerts = pd.read_sql_query("""
        SELECT * FROM fuel_readings 
        WHERE status = 'Critical'
        ORDER BY contamination_prob DESC
    """, conn)
    
    for _, alert in critical_alerts.iterrows():
        st.markdown(f'''
        <div class="alert-card">
            <h4>🔴 High Contamination Risk (Critical)</h4>
            <p><strong>Tank:</strong> {alert['fuel_id']} | <strong>Probability:</strong> {alert['contamination_prob']:.2f} | <strong>Confidence:</strong> {alert['ai_confidence']:.0f}%</p>
            <p>"{alert['ai_reasoning'][:100]}..."</p>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button(f"Mark as Resolved", key=f"resolve_{alert['id']}"):
            st.success("Alert marked as resolved!")
    
    conn.close()

# System Logs Page
elif page == "📋 System Logs":
    st.markdown("## 📋 System Event Logs")
    
    # Filter Options
    col1, col2, col3 = st.columns(3)
    with col1:
        log_source = st.selectbox("Source", ["All", "IoT Core", "SageMaker", "Bedrock", "StepFunctions"])
    with col2:
        log_level = st.selectbox("Level", ["All", "INFO", "WARNING", "ERROR"])
    with col3:
        time_filter = st.selectbox("Time Range", ["Last 1h", "Last 24h", "Last 7d"])
    
    # Sample Log Entries
    logs = [
        {"timestamp": "2025-10-20T12:41:07Z", "source": "SageMaker", "event": "Model inference latency: 1.4s", "level": "INFO"},
        {"timestamp": "2025-10-20T12:40:33Z", "source": "Bedrock", "event": "LLM reasoning generated for Tank T-014", "level": "INFO"},
        {"timestamp": "2025-10-20T12:39:15Z", "source": "IoT Core", "event": "High contamination alert triggered", "level": "WARNING"},
        {"timestamp": "2025-10-20T12:38:42Z", "source": "StepFunctions", "event": "Pipeline execution completed successfully", "level": "INFO"},
        {"timestamp": "2025-10-20T12:37:28Z", "source": "SageMaker", "event": "Model endpoint timeout", "level": "ERROR"},
        {"timestamp": "2025-10-20T12:36:55Z", "source": "IoT Core", "event": "Sensor T-021 data received", "level": "INFO"},
    ]
    
    for log in logs:
        level_class = f"log-{log['level'].lower()}"
        st.markdown(f'''
        <div class="log-entry">
            <span class="{level_class}">[{log['timestamp']}] [{log['source']}] {log['event']} ({log['level']})</span>
        </div>
        ''', unsafe_allow_html=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Fuel Quality LLM System v2.1**")
st.sidebar.markdown("*Powered by AWS Bedrock & SageMaker*")