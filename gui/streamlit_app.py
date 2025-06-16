import streamlit as st
import pandas as pd
import plotly.express as px
from typing import Dict, List, Optional
import sys
import os
import requests
import json
from io import BytesIO
import base64

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sql_generator import get_generator
from app.services.schema_reader import SchemaReader
from app.services.voice_service import get_voice_service

# Initialize services
sql_generator = get_generator()
schema_reader = SchemaReader()
voice_service = get_voice_service()

# Page config
st.set_page_config(
    page_title="Natural Language to SQL Assistant",
    page_icon="🤖",
    layout="wide"
)

# Custom CSS
st.markdown("""
    <style>
    .stTextInput>div>div>input {
        font-size: 1.2em;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
    }
    .mic-button {
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        font-size: 1.5em;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .mic-button:hover {
        background-color: #ff6b6b;
        transform: scale(1.1);
    }
    .mic-button.recording {
        background-color: #ff0000;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    </style>
""", unsafe_allow_html=True)

# Title and description
st.title("🤖 Natural Language to SQL Assistant")
st.markdown("""
    Ask questions about your data in natural language, and get instant SQL queries and results!
    The assistant uses an open-source LLM to convert your questions into SQL.
    You can type your question or use voice commands by clicking the microphone button.
""")

# Initialize session state for voice recording
if 'is_recording' not in st.session_state:
    st.session_state.is_recording = False
if 'voice_query' not in st.session_state:
    st.session_state.voice_query = None

# Create a container for the input area
input_container = st.container()

with input_container:
    # Create two columns for text input and voice button
    input_col, mic_col = st.columns([6, 1])
    
    with input_col:
        query = st.text_input(
            "Enter your question:",
            placeholder="e.g., 'Show total sales by city' or 'What are the top 3 products by revenue?'",
            value=st.session_state.voice_query if st.session_state.voice_query else ""
        )
    
    with mic_col:
        st.markdown("<br>", unsafe_allow_html=True)  # Add some vertical spacing
        mic_button = st.button(
            "🎤",
            key="mic_button",
            help="Click to start/stop voice recording"
        )

# Handle voice recording
if mic_button:
    if not st.session_state.is_recording:
        st.session_state.is_recording = True
        st.session_state.voice_query = None
        
        # Start recording
        with st.spinner("Listening..."):
            try:
                # Process voice input
                query = voice_service.process_voice_query()
                if query:
                    st.session_state.voice_query = query
                    st.experimental_rerun()
            except Exception as e:
                st.error(f"Error processing voice input: {str(e)}")
            finally:
                st.session_state.is_recording = False

# Sidebar with schema information
with st.sidebar:
    st.header("📊 Database Schema")
    schema_summary = schema_reader.get_schema_summary()
    
    for table_name, columns in schema_summary.items():
        with st.expander(f"Table: {table_name}"):
            for column in columns:
                st.text(f"• {column}")

# Main content
# Initialize session state for storing results
if 'last_query' not in st.session_state:
    st.session_state.last_query = None
if 'last_sql' not in st.session_state:
    st.session_state.last_sql = None
if 'last_results' not in st.session_state:
    st.session_state.last_results = None

# Process query when submitted
if query and query != st.session_state.last_query:
    try:
        with st.spinner("Generating SQL and executing query..."):
            # Generate and execute SQL
            sql, results = sql_generator.generate_and_execute(query)
            
            # Store results in session state
            st.session_state.last_query = query
            st.session_state.last_sql = sql
            st.session_state.last_results = results
            
            # Clear voice query after processing
            st.session_state.voice_query = None
            
    except Exception as e:
        st.error(f"Error: {str(e)}")
        st.session_state.last_query = None
        st.session_state.last_sql = None
        st.session_state.last_results = None

# Display results if available
if st.session_state.last_sql and st.session_state.last_results:
    # Create two columns for SQL and results
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Generated SQL")
        st.markdown(f'<div class="sql-box">{st.session_state.last_sql}</div>', 
                   unsafe_allow_html=True)
    
    with col2:
        st.subheader("Query Results")
        if st.session_state.last_results:
            # Convert results to DataFrame
            df = pd.DataFrame(st.session_state.last_results)
            
            # Display as table
            st.dataframe(df, use_container_width=True)
            
            # Try to create appropriate visualizations
            if len(df.columns) >= 2:
                try:
                    # Determine if we should create a chart
                    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns
                    if len(numeric_cols) > 0:
                        # If we have numeric columns, try to create a chart
                        x_col = df.columns[0]  # First column as x-axis
                        y_col = numeric_cols[0]  # First numeric column as y-axis
                        
                        # Create appropriate chart based on data
                        if len(df) <= 10:  # For small datasets, use bar chart
                            fig = px.bar(df, x=x_col, y=y_col, title=f"{y_col} by {x_col}")
                        else:  # For larger datasets, use line chart
                            fig = px.line(df, x=x_col, y=y_col, title=f"{y_col} over {x_col}")
                        
                        st.plotly_chart(fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Could not create visualization: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center'>
        <p>Built with ❤️ using Streamlit, Mistral-7B, SQLAlchemy, and Speech Recognition</p>
    </div>
""", unsafe_allow_html=True) 