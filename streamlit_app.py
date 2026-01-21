import streamlit as st
import pandas as pd
import plotly.express as px
import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# --- CONFIGURATION ---
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID_GOES_HERE' # <--- TRIPLE CHECK THIS ID IS CORRECT
RANGE_NAME = 'Sheet1!A:E' 

def get_creds():
    """
    Tries to load credentials from Streamlit Secrets (Cloud) first,
    then falls back to local file (Development).
    """
    creds = None
    
    # 1. Try Secrets (Cloud Method)
    if "token" in st.secrets and "token_json" in st.secrets["token"]:
        try:
            token_info = json.loads(st.secrets["token"]["token_json"])
            creds = Credentials.from_authorized_user_info(token_info, SCOPES)
            return creds
        except Exception as e:
            st.error(f"Secrets found but failed to load: {e}")

    # 2. Try Local File (Codespaces Method)
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        return creds

    return None

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Alaska Premier | Sales Dashboard",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- BRAND THEME & LAYOUT CSS ---
# Primary: Royal Purple (#33006F) | Accent: Gold (#C5A059)
st.markdown("""
<style>
    /* 1. REMOVE DEFAULT PADDING */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }
    
    /* 2. BACKGROUND */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); /* Dark blue gradient */
    }
    
    /* 3. HERO HEADER (Mimics Website Nav) */
    .hero-header {
        background-color: #33006F;
        padding: 20px 40px;
        border-radius: 0 0 15px 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .hero-title {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 700;
        font-size: 24px;
        margin: 0;
        color: #FFFFFF;
    }
    .hero-subtitle {
        color: #C5A059; /* Gold */
        font-size: 14px;
        font-weight: 500;
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* 4. METRIC CARDS (Bento Style) */
    .metric-container {
        background: linear-gradient(135deg, #33006F 0%, #2d0052 100%);
        padding: 20px;
        border-radius: 15px;
        border-left: 5px solid #C5A059;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
        height: 100%;
        color: white;
    }
    .metric-label {
        color: #C5A059;
        font-size: 12px;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 1px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #FFFFFF;
        margin: 10px 0;
    }
    .metric-sub {
        color: #B0B8D0;
        font-size: 11px;
        margin-top: 8px;
    }
    
    /* 5. CHART CONTAINERS - Individual Card Styling */
    div[data-testid="stContainer"] {
        background-color: #0f3460 !important;
        padding: 25px !important;
        border-radius: 15px !important;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4) !important;
        border: 1px solid #1a5276 !important;
    }
    
    .chart-title {
        color: #FFFFFF;
        font-size: 16px;
        font-weight: 600;
        margin: 0 0 15px 0;
    }
    
    /* 6. SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #0f3460;
        border-right: 2px solid #C5A059;
    }
    section[data-testid="stSidebar"] h1, h2, p, label {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] button {
        background-color: #33006F !important;
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# --- COLORS ---
APA_PURPLE = '#33006F'
APA_GOLD = '#C5A059'
APA_GREY = '#E2E8F0'

# --- DATA PARSING FUNCTIONS ---
def clean_currency(x):
    """Clean currency strings and error codes like #DIV/0!"""
    if isinstance(x, str):
        x = x.replace('$', '').replace(',', '').strip()
        if '#DIV/0!' in x or x == '' or x.lower() == 'nan':
            return 0
    return pd.to_numeric(x, errors='coerce')

def load_from_google_sheets():
    """Load data from Google Sheets - returns dict with month DataFrames or None if unavailable"""
    if not GOOGLE_SHEETS_AVAILABLE:
        return None
    
    try:
        # Your Google Sheet ID
        SHEET_ID = '12WSXjH7gXjKutN9aCCE6bb1Q2poeQHfaU2bClU5-wQU'
        
        # Try to authenticate
        creds = get_creds()
        if not creds:
            return None
        
        st.info("📊 Loading data from Google Sheets...")
        return True  # Placeholder - authentication successful
    except Exception as e:
        st.warning(f"⚠️ Google Sheets unavailable, using local CSV files: {e}")
        return None

@st.cache_data
def load_and_parse_data():
    """Reads all matching CSV files in the directory and consolidates them."""
    leads_dfs = []
    perf_dfs = []
    cat_dfs = []
    
    # 1. Identify Files
    files = [f for f in os.listdir('.') if f.startswith("Sales Metrics Spreadsheet") and f.endswith(".csv")]
    monthly_files = [f for f in files if "Categories" not in f]
    cat_file = next((f for f in files if "Categories" in f), None)
    
    # 2. Parse Monthly Files (August, September, etc.)
    for file_path in monthly_files:
        month = file_path.split(' - ')[-1].replace('.csv', '')
        try:
            df = pd.read_csv(file_path)
            
            # --- A. Lead Sources (Top Table) ---
            # Finds the row with "Total" to slice the top section
            total_mask = df.iloc[:, 0].astype(str).str.contains('Total', case=False, na=False)
            if total_mask.any():
                total_idx = df[total_mask].index[0]
                leads_sub = df.iloc[:total_idx].copy()
                leads_sub.columns = [c.strip() for c in leads_sub.columns]
                leads_sub = leads_sub.dropna(subset=['Date']) # Remove empty rows
                leads_sub['Month'] = month
                leads_dfs.append(leads_sub)
            
            # --- B. Salesperson Performance (Bottom Table) ---
            name_mask = df.iloc[:, 0].astype(str).str.contains('Name', case=False, na=False)
            if name_mask.any():
                header_idx = df[name_mask].index[0]
                perf_sub = df.iloc[header_idx+1:].copy()
                perf_sub.columns = df.iloc[header_idx] # Set headers
                perf_sub.columns = [str(c).strip() for c in perf_sub.columns] # Clean headers
                
                # Cleanup and Forward Fill Names (handle merged cells)
                perf_sub = perf_sub.dropna(subset=['Week']) 
                perf_sub['Name'] = perf_sub['Name'].ffill()
                perf_sub['Month'] = month
                
                # Normalize Columns (Total Contracts vs Closed Contracts)
                contract_col = next((c for c in perf_sub.columns if 'Contract' in c), None)
                leads_col = next((c for c in perf_sub.columns if 'Leads' in c and 'Monthly' not in c), None)
                
                if contract_col:
                    perf_sub['Contracts'] = perf_sub[contract_col].apply(clean_currency).fillna(0)
                else:
                    perf_sub['Contracts'] = 0
                    
                if leads_col:
                    perf_sub['Leads'] = perf_sub[leads_col].apply(clean_currency).fillna(0)
                else:
                    perf_sub['Leads'] = 0
                    
                perf_dfs.append(perf_sub)
                
        except Exception as e:
            st.warning(f"Skipping file {file_path}: {e}")

    # 3. Parse Categories File
    if cat_file:
        try:
            df_cat = pd.read_csv(cat_file)
            # Find all header rows (start of each month block)
            split_indices = df_cat.index[df_cat.iloc[:, 0] == 'Lead Category'].tolist()
            if 0 not in split_indices: split_indices.insert(0, 0)
            
            for i in range(len(split_indices)):
                start = split_indices[i]
                end = split_indices[i+1] if i+1 < len(split_indices) else len(df_cat)
                
                chunk = df_cat.iloc[start+1:end].copy()
                header = df_cat.iloc[start]
                
                # Find which column holds the month name (e.g. "September")
                valid_months = ['January','February','March','April','May','June',
                                'July','August','September','October','November','December']
                month_col_idx = -1
                month_name = "Unknown"
                
                for idx, val in enumerate(header):
                    if str(val) in valid_months:
                        month_name = str(val)
                        month_col_idx = idx
                        break
                
                if month_col_idx != -1:
                    # Extract Category and Count
                    chunk_clean = pd.DataFrame({
                        'Category': chunk.iloc[:, 0],
                        'Count': chunk.iloc[:, month_col_idx].apply(clean_currency),
                        'Month': month_name
                    })
                    cat_dfs.append(chunk_clean)
        except Exception as e:
            st.error(f"Error parsing categories: {e}")

    # 4. Consolidate
    leads_final = pd.concat(leads_dfs, ignore_index=True) if leads_dfs else pd.DataFrame()
    perf_final = pd.concat(perf_dfs, ignore_index=True) if perf_dfs else pd.DataFrame()
    cat_final = pd.concat(cat_dfs, ignore_index=True) if cat_dfs else pd.DataFrame()
    
    # Sort order for months - August through January (fiscal year)
    month_order = ['August', 'September', 'October', 'November', 'December', 'January',
                   'February', 'March', 'April', 'May', 'June', 'July']
    
    for df in [leads_final, perf_final, cat_final]:
        if not df.empty and 'Month' in df.columns:
            df['Month'] = pd.Categorical(df['Month'], categories=month_order, ordered=True)
            df.sort_values('Month', inplace=True)
            
    return leads_final, perf_final, cat_final

# --- LOAD DATA ---
leads_df, perf_df, cat_df = load_and_parse_data()

# --- MAIN DASHBOARD ---
if leads_df.empty and perf_df.empty:
    st.error("⚠️ No data found. Please ensure 'Sales Metrics Spreadsheet' files are in the folder.")
else:
    # --- SIDEBAR CONTENT ---
    with st.sidebar:
        st.markdown(f"<h2 style='text-align: center; color: #33006F; margin-top: 20px;'>ALASKA PREMIER<br><span style='font-size: 14px; color: #C5A059;'>AUCTIONS & APPRAISALS</span></h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        # Google Sheets Option
        st.markdown("### 📊 Data Source")
        creds = get_creds()
        if creds:
            use_google_sheets = st.checkbox("Use Google Sheets (Beta)", value=False, help="Requires authentication")
            
            if use_google_sheets:
                st.info("🔐 Authenticating with Google Sheets...")
                try:
                    creds = get_creds()
                    if creds:
                        st.success("✅ Connected to Google Sheets!")
                except Exception as e:
                    st.error(f"❌ Authentication failed: {e}")
        else:
            st.markdown("**Status:** Using CSV data")
            if not GOOGLE_SHEETS_AVAILABLE:
                st.caption("Google Sheets not configured yet")
        st.markdown("---")
        
        st.markdown("### 📅 FILTER PERIOD")
        all_months = sorted(list(set(leads_df['Month'].dropna().unique()) | set(perf_df['Month'].dropna().unique())))
        selected_months = st.multiselect("Select Month(s)", all_months, default=all_months)
        
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #8D99AE; font-size: 12px;'>© 2024 Alaska Premier<br>System Status: Online</p>", unsafe_allow_html=True)

    # --- HERO HEADER ---
    st.markdown(f"""
    <div class="hero-header">
        <div class="hero-left">
            <div>
                <div class="hero-title">ALASKA PREMIER AUCTIONS & APPRAISALS</div>
                <div class="hero-subtitle">Executive Sales Dashboard</div>
            </div>
            <div class="hero-badges">
                <div class="badge">LIVE DATA</div>
                <div class="badge">EXECUTIVE VIEW</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filter Data based on selection
    if selected_months:
        leads_filtered = leads_df[leads_df['Month'].isin(selected_months)]
        perf_filtered = perf_df[perf_df['Month'].isin(selected_months)]
        cat_filtered = cat_df[cat_df['Month'].isin(selected_months)]
    else:
        leads_filtered, perf_filtered, cat_filtered = leads_df, perf_df, cat_df

    # --- KPI CALCULATIONS ---
    total_leads = leads_filtered[['Jotform', 'Facebook', 'Phone', 'Walk-In', 'Email', 'Other']].apply(pd.to_numeric, errors='coerce').sum().sum()
    total_contracts = perf_filtered['Contracts'].sum()
    conversion_rate = (total_contracts / total_leads * 100) if total_leads > 0 else 0
    
    if not perf_filtered.empty:
        best_rep = perf_filtered.groupby('Name')['Contracts'].sum().idxmax()
        best_rep_val = perf_filtered.groupby('Name')['Contracts'].sum().max()
    else:
        best_rep, best_rep_val = "N/A", 0

    # --- KPI CARDS ROW ---
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    with kpi_col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Total Leads</div>
            <div class="metric-value">{int(total_leads):,}</div>
            <div class="metric-sub">All Sources</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Contracts Signed</div>
            <div class="metric-value">{int(total_contracts)}</div>
            <div class="metric-sub">Closed Deals</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Conversion Rate</div>
            <div class="metric-value">{conversion_rate:.1f}%</div>
            <div class="metric-sub">Lead to Deal</div>
        </div>
        """, unsafe_allow_html=True)
    
    with kpi_col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label">Top Agent</div>
            <div class="metric-value" style="font-size: 28px;">{best_rep}</div>
            <div class="metric-sub">{int(best_rep_val)} Contracts</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)  # Spacer

    # --- MAIN CHARTS GRID (2:1 RATIO) ---
    # Row 1: Lead Trends (2/3) + Source Breakdown (1/3)
    chart_col1, chart_col2 = st.columns([2, 1])
    
    with chart_col1:
        with st.container(border=False):
            st.markdown('<p class="chart-title">📈 Monthly Lead Volume</p>', unsafe_allow_html=True)
            if not leads_filtered.empty:
                sources = ['Jotform', 'Facebook', 'Phone', 'Walk-In', 'Email', 'Other']
                leads_long = leads_filtered.melt(id_vars=['Month'], value_vars=sources, var_name='Source', value_name='Count')
                leads_long['Count'] = pd.to_numeric(leads_long['Count'], errors='coerce')
                
                # Stacked Bar Chart
                fig_area = px.bar(leads_long, x='Month', y='Count', color='Source',
                                  template='plotly_white',
                                  color_discrete_sequence=px.colors.qualitative.Set2)
                fig_area.update_layout(
                    barmode='stack',
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                    font=dict(family="Arial", size=11),
                    showlegend=True,
                    hovermode='x unified'
                )
                fig_area.update_xaxes(showgrid=False)
                fig_area.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
                st.plotly_chart(fig_area, use_container_width=True, config={'displayModeBar': False})
    
    with chart_col2:
        with st.container(border=False):
            st.markdown('<p class="chart-title">🎯 Source Mix</p>', unsafe_allow_html=True)
            if not leads_filtered.empty:
                source_totals = leads_filtered[sources].apply(pd.to_numeric, errors='coerce').sum().reset_index()
                source_totals.columns = ['Source', 'Count']
                source_totals = source_totals[source_totals['Count'] > 0]
                
                fig_donut = px.pie(source_totals, values='Count', names='Source', hole=0.5,
                                  color_discrete_sequence=px.colors.qualitative.Set2)
                fig_donut.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                    font=dict(family="Arial", size=10),
                    showlegend=False,
                    hovermode='closest'
                )
                # Center annotation
                fig_donut.add_annotation(
                    text=f"{int(total_leads)}<br><span style='font-size:12px'>Total</span>",
                    showarrow=False,
                    font=dict(size=20, color=APA_PURPLE)
                )
                st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

    # Row 2: Team Performance (2/3) + Top Categories (1/3)
    chart_col3, chart_col4 = st.columns([2, 1])
    
    with chart_col3:
        with st.container(border=False):
            st.markdown('<p class="chart-title">👥 Team Performance</p>', unsafe_allow_html=True)
            if not perf_filtered.empty:
                rep_stats = perf_filtered.groupby('Name').agg({
                    'Leads': 'sum',
                    'Contracts': 'sum'
                }).reset_index().sort_values('Contracts', ascending=False)
                
                # Dual Bar Chart
                fig_rep = go.Figure()
                fig_rep.add_trace(go.Bar(
                    x=rep_stats['Name'], 
                    y=rep_stats['Leads'], 
                    name='Leads Assigned',
                    marker=dict(color=APA_GREY)
                ))
                fig_rep.add_trace(go.Bar(
                    x=rep_stats['Name'], 
                    y=rep_stats['Contracts'], 
                    name='Contracts Closed',
                    marker=dict(color=APA_PURPLE)
                ))
                
                fig_rep.update_layout(
                    barmode='group',
                    template='plotly_white',
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                    font=dict(family="Arial", size=11),
                    legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, bgcolor="rgba(0,0,0,0)"),
                    hovermode='x unified'
                )
                fig_rep.update_xaxes(showgrid=False)
                fig_rep.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
                st.plotly_chart(fig_rep, use_container_width=True, config={'displayModeBar': False})
    
    with chart_col4:
        with st.container(border=False):
            st.markdown('<p class="chart-title">🏆 Top Categories</p>', unsafe_allow_html=True)
            if not cat_filtered.empty:
                cat_stats = cat_filtered.groupby('Category')['Count'].sum().sort_values(ascending=True).tail(8)
                
                fig_cat = px.bar(
                    x=cat_stats.values, 
                    y=cat_stats.index, 
                    orientation='h',
                    template='plotly_white',
                    color_discrete_sequence=[APA_GOLD]
                )
                
                fig_cat.update_layout(
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=350,
                    font=dict(family="Arial", size=10),
                    xaxis_title="",
                    yaxis_title="",
                    hovermode='closest',
                    showlegend=False
                )
                fig_cat.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(200,200,200,0.2)')
                fig_cat.update_yaxes(showgrid=False)
                st.plotly_chart(fig_cat, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)  # Footer spacer