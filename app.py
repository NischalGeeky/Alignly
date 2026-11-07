import config
import streamlit as st
from sqlalchemy import text
from database.connection import engine
from utils.logging_config import configure_logging

configure_logging()

# Set Streamlit page configuration
st.set_page_config(
    page_title="Alignly — Executive Operations",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom corporate CSS styling
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1E293B;
            margin-bottom: 0.2rem;
        }
        .tagline {
            font-size: 1.1rem;
            color: #64748B;
            margin-bottom: 2rem;
        }
        .status-box {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1.2rem;
            margin-bottom: 1.5rem;
        }
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.6rem;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .status-success {
            background-color: #DCFCE7;
            color: #166534;
        }
        .status-danger {
            background-color: #FEE2E2;
            color: #991B1B;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar Navigation Placeholder
with st.sidebar:
    st.title("🧭 Alignly")
    st.caption("Business Operations & Executive Intelligence")
    st.divider()
    st.markdown("**Navigation**")
    st.info("System Initialization & Dataset (Tasks 1–2)")
    st.caption(f"Demo As-Of Date: {config.DEMO_AS_OF_DATE.isoformat()}")
    st.caption("Operational modules will be enabled in subsequent releases.")

# Main Application Header
st.markdown('<div class="main-header">Alignly</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="tagline">Bringing strategy, teams, and execution into alignment.</div>',
    unsafe_allow_html=True,
)

# Check Database Connectivity
db_status_connected = False
db_error_message = None

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
        db_status_connected = True
except Exception as e:
    db_status_connected = False
    db_error_message = str(e)

# Database Connection Status Banner
if db_status_connected:
    dialect_name = engine.dialect.name.upper()
    st.markdown(
        f"""
        <div class="status-box">
            <strong>Database Connectivity:</strong> 
            <span class="status-badge status-success">CONNECTED ({dialect_name})</span>
            <p style="margin: 0.5rem 0 0 0; color: #475569; font-size: 0.9rem;">
                Database connection established and responding normally.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        f"""
        <div class="status-box">
            <strong>Database Connectivity:</strong> 
            <span class="status-badge status-danger">DISCONNECTED</span>
            <p style="margin: 0.5rem 0 0 0; color: #991B1B; font-size: 0.9rem;">
                Unable to connect to database: {db_error_message}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Welcome Section
st.subheader("Platform Overview")
st.write(
    """
    Alignly provides a disciplined operational command layer to track strategic execution,
    surface cross-departmental delivery risks, maintain leadership accountability,
    and prepare executive reviews.
    """
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Core Pillars")
    st.markdown(
        """
        - **Strategic Tracking:** Initiatives, milestones, and cross-team dependencies.
        - **Execution Intelligence:** Deterministic heuristic scoring of delivery risks and bottlenecks.
        - **Leadership Cadence:** Direct traceability from decisions to accountable actions.
        """
    )

with col2:
    st.markdown("### System Architecture")
    st.markdown(
        """
        - **Relational Integrity:** Strict schemas with PostgreSQL & SQLite compatibility.
        - **Deterministic Rule Engine:** Transparent metric calculations without hidden heuristics.
        - **Executive Interface:** Streamlined workflows designed for operational leaders.
        """
    )
