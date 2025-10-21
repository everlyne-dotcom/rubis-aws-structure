import streamlit as st
import boto3
import json
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Initialize session state
if 'rag_simulator' not in st.session_state:
    from fuel_rag_simulator import FuelRAGSimulator
    st.session_state.rag_simulator = FuelRAGSimulator()

def get_fuel_stats():
    """Get fuel data statistics from local database"""
    conn = sqlite3.connect('fuel_quality.db')
    
    # Get contamination stats
    contamination_query = """
        SELECT batch_quality, COUNT(*) as count 
        FROM fuel_data 
        GROUP BY batch_quality
    """
    contamination_df = pd.read_sql_query(contamination_query, conn)
    
    # Get recent data
    recent_query = """
        SELECT fuel_id, temperature_c, density_kg_m3, sulfur_ppm, batch_quality
        FROM fuel_data 
        ORDER BY id DESC 
        LIMIT 10
    """
    recent_df = pd.read_sql_query(recent_query, conn)
    
    conn.close()
    return contamination_df, recent_df

def main():
    st.set_page_config(
        page_title="Fuel Quality RAG System",
        page_icon="🛢️",
        layout="wide"
    )
    
    st.title("🛢️ Fuel Quality RAG System")
    st.markdown("AI-powered fuel quality assessment using AWS Bedrock")
    
    # Sidebar
    st.sidebar.header("System Status")
    
    # Check OpenSearch status
    opensearch_ready = st.session_state.rag_simulator.check_opensearch_status()
    if opensearch_ready:
        st.sidebar.success("✅ OpenSearch Ready")
    else:
        st.sidebar.warning("⏳ Using Local Database")
    
    # Load data button
    if st.sidebar.button("🔄 Reload Fuel Data"):
        data_count = st.session_state.rag_simulator.load_sample_data()
        st.sidebar.success(f"Loaded {data_count} samples")
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🤖 Ask Questions", "📊 Data Analytics", "⚙️ System Info"])
    
    with tab1:
        st.header("Ask Fuel Quality Questions")
        
        # Predefined questions
        st.subheader("Quick Questions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("What indicates contaminated fuel?"):
                st.session_state.current_question = "What indicates contaminated fuel?"
            if st.button("Is 45°C temperature normal?"):
                st.session_state.current_question = "Is 45°C temperature normal?"
        
        with col2:
            if st.button("What causes high sulfur content?"):
                st.session_state.current_question = "What causes high sulfur content?"
            if st.button("How to detect contamination?"):
                st.session_state.current_question = "How to detect contamination?"
        
        # Custom question input
        st.subheader("Custom Question")
        user_question = st.text_input("Enter your fuel quality question:")
        
        if st.button("🔍 Ask Question") or user_question:
            question = user_question or st.session_state.get('current_question', '')
            
            if question:
                with st.spinner("🤖 AI is thinking..."):
                    answer = st.session_state.rag_simulator.query_rag(question)
                
                st.subheader("Question:")
                st.write(question)
                
                st.subheader("Answer:")
                st.success(answer)
    
    with tab2:
        st.header("Fuel Data Analytics")
        
        try:
            contamination_df, recent_df = get_fuel_stats()
            
            if not contamination_df.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Contamination Distribution")
                    fig_pie = px.pie(
                        contamination_df, 
                        values='count', 
                        names='batch_quality',
                        color_discrete_map={'CLEAN': 'green', 'CONTAMINATED': 'red'}
                    )
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    st.subheader("Quality Metrics")
                    total_samples = contamination_df['count'].sum()
                    contaminated = contamination_df[contamination_df['batch_quality'] == 'CONTAMINATED']['count'].sum() if 'CONTAMINATED' in contamination_df['batch_quality'].values else 0
                    contamination_rate = (contaminated / total_samples * 100) if total_samples > 0 else 0
                    
                    st.metric("Total Samples", total_samples)
                    st.metric("Contaminated", contaminated)
                    st.metric("Contamination Rate", f"{contamination_rate:.1f}%")
            
            if not recent_df.empty:
                st.subheader("Recent Fuel Data")
                
                # Temperature chart
                fig_temp = px.bar(
                    recent_df, 
                    x='fuel_id', 
                    y='temperature_c',
                    color='batch_quality',
                    color_discrete_map={'CLEAN': 'green', 'CONTAMINATED': 'red'},
                    title="Temperature by Tank"
                )
                fig_temp.add_hline(y=30, line_dash="dash", line_color="orange", annotation_text="Contamination Threshold")
                st.plotly_chart(fig_temp, use_container_width=True)
                
                # Data table
                st.subheader("Recent Samples")
                st.dataframe(recent_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"No data available. Run collect_fuel_data.py first. Error: {e}")
    
    with tab3:
        st.header("System Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔧 Components")
            st.write("✅ AWS Bedrock (Titan)")
            st.write("✅ Local SQLite Database")
            st.write("✅ IoT Core Integration")
            if opensearch_ready:
                st.write("✅ OpenSearch Ready")
            else:
                st.write("⏳ OpenSearch Creating")
        
        with col2:
            st.subheader("📋 Fuel Quality Standards")
            standards = {
                "Temperature": "15-25°C (Normal)",
                "Density": "720-780 kg/m³",
                "Sulfur Content": "5-15 ppm",
                "Moisture": "0.01-0.05%",
                "Octane Rating": "87-95"
            }
            
            for param, value in standards.items():
                st.write(f"**{param}:** {value}")
        
        st.subheader("🚀 Actions")
        if st.button("🔄 Upgrade to OpenSearch"):
            if opensearch_ready:
                st.success("Running upgrade script...")
                # Here you would call the upgrade script
            else:
                st.warning("OpenSearch not ready yet")
        
        if st.button("📊 Generate New Data"):
            st.info("Run: python collect_fuel_data.py")

if __name__ == "__main__":
    main()