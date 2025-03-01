import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_data_from_mongodb
import pycountry
from datetime import datetime
import numpy as np

# Load data from MongoDB
clients, memberships, transactions = load_data_from_mongodb()

# =====================
# Data Preprocessing
# =====================
# Convert dates to datetime
clients['date_joined'] = pd.to_datetime(clients['date_joined'])
clients['birthdate'] = pd.to_datetime(clients['birthdate'])
memberships['start_date'] = pd.to_datetime(memberships['start_date'])
memberships['end_date'] = pd.to_datetime(memberships['end_date'])
transactions['date'] = pd.to_datetime(transactions['date'])

# Clean and convert IDs to integers
for df in [clients, memberships, transactions]:
    df['client_id'] = df['client_id'].astype(str).str.replace(',', '').astype(int)

# Merge data
merged_data = pd.merge(clients, memberships, on='client_id', how='inner')

# =====================
# Helper Functions
# =====================
def get_iso_alpha3(country_name):
    try:
        return pycountry.countries.search_fuzzy(country_name)[0].alpha_3
    except:
        return None

# Add country codes
clients['country_code'] = clients['nationality'].apply(get_iso_alpha3)

# =====================
# Dashboard Layout
# =====================
st.set_page_config(layout="wide")
st.title("🌍 Global Client Analytics Dashboard")

# =====================
# Quick Statistics (Updated with Total Transaction Amount)
# =====================
st.markdown("---")
st.subheader("🚀 Quick Statistics")

# First row: Total Clients, Active Memberships, Total Transactions, and Total Transaction Amount
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="Total Clients", value=clients['client_id'].nunique())

with col2: 
    active_memberships = merged_data[merged_data['status'] == 'ACTIVE']['membership_id'].nunique()
    st.metric(label="Active Memberships", value=active_memberships)

with col3:
    total_transactions = transactions['transaction_id'].nunique()
    st.metric(label="Total Transactions", value=total_transactions)

with col4:
    total_amount = transactions['amount'].sum()
    st.metric(label="Total Transaction Amount", value=f"${total_amount:,.2f}")

# =====================
# Second row: Month/Year Selector and Filtered Metrics
# =====================
st.markdown("---")
st.subheader("📅 Monthly Statistics")

# Create columns for side-by-side selectors
col_month, col_year = st.columns(2)

# Month selector with names
month_names = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
with col_month:
    selected_month = st.selectbox(
        "Select Month",
        options=range(1, 13),  # Values: 1-12
        format_func=lambda x: month_names[x - 1],  # Display month names
        index=9  # Default to October (index 9)
    )

# Year selector
with col_year:
    selected_year = st.selectbox(
        "Select Year",
        options=range(2020, 2026),  # Values: 2020-2025
        index=4  # Default to 2024 (index 4)
    )

# Format selected month and year for filtering
selected_month_year = f"{selected_year}-{selected_month:02d}"

# Create columns for filtered metrics
col1, col2 = st.columns(2)

with col1:
    # Filter clients for selected month and year
    filtered_clients = clients[
        (clients['date_joined'].dt.year == selected_year) & 
        (clients['date_joined'].dt.month == selected_month)
    ]
    st.metric(label=f"Signups in {selected_month_year}", value=len(filtered_clients))

with col2:
    # Filter memberships for selected month and year
    filtered_memberships = memberships[
        (memberships['start_date'].dt.year == selected_year) & 
        (memberships['start_date'].dt.month == selected_month)
    ]
    st.metric(label=f"Memberships in {selected_month_year}", value=len(filtered_memberships))

# =====================
# KPI Section
# =====================
st.markdown("---")
st.subheader("📊 Key Performance Indicators")
col1, col2 = st.columns(2)

with col1:
    # Merge clients with memberships (left join)
    membership_status = clients.merge(
        memberships[['client_id', 'tier']].drop_duplicates(subset='client_id'),
        on='client_id',
        how='left'
    )
    
    # Create membership classification
    membership_status['membership_status'] = np.where(
        membership_status['tier'] == 'No Membership',
        'No Membership',
        'Has Membership'
    )
    
    # Create pie chart
    fig = px.pie(membership_status, 
                 names='membership_status', 
                 title='Membership Distribution',
                 hole=0.4,
                 color='membership_status',
                 color_discrete_map={
                     'Has Membership': '#2CA02C',
                     'No Membership': '#FF7F0E'
                 })
    
    # Format labels and tooltips
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Count: %{value}</br>Percentage: %{percent}"
    )
    
    fig.update_layout(
        showlegend=True,
        margin=dict(l=20, r=20, t=40, b=20),
        uniformtext_minsize=12
    )
    
    st.plotly_chart(fig, use_container_width=True, key="membership_distribution_pie_chart")

with col2:
    # Membership Tier Breakdown
    tier_counts = memberships['tier'].value_counts()
    fig = px.bar(tier_counts, 
                orientation='v', 
                title='Membership Tier Distribution',
                labels={'index':'Tier', 'value':'Count'},
                color=tier_counts.index,
                color_discrete_sequence=['#1F77B4', '#2CA02C'],
                text_auto=True)
    fig.update_layout(showlegend=False, xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True, key="membership_tier_bar_chart")

# =====================
# Global Distribution
# =====================
st.markdown("---")
st.subheader("🌐 Client World Distribution")

country_counts = clients['country_code'].value_counts().reset_index()
country_counts.columns = ['country_code', 'count']

fig = px.choropleth(country_counts,
                    locations="country_code",
                    color="count",
                    hover_name="country_code",
                    color_continuous_scale=['#2CA02C', '#1F77B4'],
                    projection="natural earth",
                    height=600)

fig.update_layout(
    margin=dict(l=0, r=0, t=40, b=0),
    geo=dict(
        showframe=True,
        showcoastlines=True,
        showcountries=True,
        countrycolor="#404040",
        countrywidth=1.5,
        landcolor="white",
        bgcolor="rgba(0,0,0,0)",
        subunitcolor="white"
    ),
    coloraxis_colorbar=dict(
        title="Client Count",
        thickness=20,
        len=0.75
    )
)

fig.update_geos(
    coastlinecolor="#404040",
    coastlinewidth=1.5,
    oceancolor="white",
    lakecolor="white"
)

st.plotly_chart(fig, use_container_width=True, key="world_distribution_choropleth")

# =====================
# Demographic Insights (Fixed Age Calculation)
# =====================
st.markdown("---")
st.subheader("📈 Demographic Insights")

# Corrected Age Calculation
clients['age'] = (pd.Timestamp.now() - clients['birthdate']).dt.days // 365.25
age_groups = pd.cut(clients['age'], 
                   bins=[0, 18, 25, 35, 45, 55, 65, 100],
                   labels=['0-18', '19-25', '26-35', '36-45', '46-55', '56-65', '65+'])

# Ensure age groups are sorted in ascending order
age_groups = pd.Categorical(age_groups, categories=[
    '0-18', '19-25', '26-35', '36-45', '46-55', '56-65', '65+'
], ordered=True)

# Create histogram
fig = px.histogram(x=age_groups, 
                  title="Age Group Distribution",
                  color_discrete_sequence=['#1F77B4'],
                  category_orders={'x': ['0-18', '19-25', '26-35', '36-45', '46-55', '56-65', '65+']})

# Update layout
fig.update_layout(
    xaxis_title="Age Group",
    yaxis_title="Count",
    xaxis={'categoryorder': 'array', 'categoryarray': ['0-18', '19-25', '26-35', '36-45', '46-55', '56-65', '65+']}
)

st.plotly_chart(fig, use_container_width=True, key="age_group_histogram")

# =====================
# Drop Unnecessary Columns
# =====================
# List of columns to drop
columns_to_drop = ['_id', 'Unnamed: 5', 'country_code', 'date_joined']

# Drop columns if they exist
clients = clients.drop(columns=[col for col in columns_to_drop if col in clients.columns])

# =====================
# List of Member Birthdays (Updated with Highlighting and Black Font)
# =====================
st.markdown("---")
st.subheader("🎂 Upcoming Member Birthdays")

# Calculate days until next birthday
def days_until_birthday(birthdate):
    today = pd.Timestamp.now().normalize()
    next_birthday = birthdate.replace(year=today.year)
    
    # If birthday has already passed this year, set it to next year
    if next_birthday < today:
        next_birthday = next_birthday.replace(year=today.year + 1)
    
    return (next_birthday - today).days

# Add days until next birthday to clients
clients['days_until_birthday'] = clients['birthdate'].apply(days_until_birthday)

# Sort by days until birthday (ascending)
upcoming_birthdays = clients.sort_values(by='days_until_birthday')

# Highlight rows where birthday is today
def highlight_birthday_today(row):
    today = pd.Timestamp.now().normalize()
    birthday = row['birthdate'].replace(year=today.year)
    
    if birthday == today:
        return ['background-color: #FFD700; color: black'] * len(row)  # Gold background with black font
    else:
        return [''] * len(row)

# Apply highlighting
highlighted_birthdays = upcoming_birthdays.style.apply(highlight_birthday_today, axis=1)

# Display the list
st.dataframe(
    highlighted_birthdays,
    column_config={
        "client_id": "Client ID",
        "name": "Name",
        "birthdate": "Birthdate",
        "days_until_birthday": "Days Until Birthday"
    },
    hide_index=True,
    use_container_width=True
)

# =====================
# Top 5 Spenders (with Time Frame Selector)
# =====================
st.markdown("---")
st.subheader("🏆 Top 5 Spenders")

# Add time frame selector
col_start, col_end = st.columns(2)

with col_start:
    start_date = st.date_input("Start Date", value=pd.Timestamp.now() - pd.Timedelta(days=365))

with col_end:
    end_date = st.date_input("End Date", value=pd.Timestamp.now())

# Filter transactions within the selected time frame
filtered_transactions = transactions[
    (transactions['date'] >= pd.Timestamp(start_date)) &
    (transactions['date'] <= pd.Timestamp(end_date))
]

# Calculate total spending per client
total_spent = filtered_transactions.groupby('client_id')['amount'].sum().reset_index()

# Merge with clients to get names
top_spenders = pd.merge(total_spent, clients, on='client_id').nlargest(5, 'amount')

# Display the list
st.dataframe(
    top_spenders[['client_id', 'name', 'amount']],
    column_config={
        "client_id": "Client ID",
        "name": "Client Name",
        "amount": "Total Spent ($)"
    },
    hide_index=True,
    use_container_width=True
)


# Membership Retention Rate
st.markdown("---")
st.subheader("📊 Membership Retention Rate")

# Calculate retention rate
active_memberships = merged_data[merged_data['status'] == 'ACTIVE']['membership_id'].nunique()
total_memberships = memberships['membership_id'].nunique()
retention_rate = (active_memberships / total_memberships) * 100

st.metric(label="Retention Rate", value=f"{retention_rate:.2f}%")

# =====================
# Membership Loyalty Program Insights (Updated with Tier Order)
# =====================
st.markdown("---")
st.subheader("🏅 Membership Loyalty Program Insights")

# Merge transactions and memberships data
merged_data = pd.merge(transactions, memberships, on='client_id')

# Define the order of tiers
tier_order = ['No Membership', 'Bronze', 'Silver', 'Gold', 'Platinum']

# Ensure the 'tier' column is categorical with the specified order
merged_data['tier'] = pd.Categorical(merged_data['tier'], categories=tier_order, ordered=True)

# Box and Whisker Plots for Spending by Membership Tier
fig = px.box(merged_data, 
             x='tier', 
             y='amount', 
             title='Spending Distribution by Membership Tier',
             color='tier',
             color_discrete_sequence=px.colors.qualitative.Pastel,
             labels={'tier': 'Membership Tier', 'amount': 'Amount Spent ($)'},
             category_orders={'tier': tier_order})  # Enforce tier order

# Update layout
fig.update_layout(
    xaxis_title="Membership Tier",
    yaxis_title="Amount Spent ($)",
    showlegend=False
)

# Display the plot
st.plotly_chart(fig, use_container_width=True, key="spending_distribution_box_plot")


# =====================
# Scatter Plot of Transactions within a Timeframe
# =====================
st.markdown("---")
st.subheader("📊 Transaction Scatter Plot")

# Add time frame selector for scatter plot
col_start_scatter, col_end_scatter = st.columns(2)

with col_start_scatter:
    start_date_scatter = st.date_input("Start Date for Scatter Plot", value=pd.Timestamp.now() - pd.Timedelta(days=365))

with col_end_scatter:
    end_date_scatter = st.date_input("End Date for Scatter Plot", value=pd.Timestamp.now())

# Filter transactions within the selected time frame
filtered_transactions_scatter = transactions[
    (transactions['date'] >= pd.Timestamp(start_date_scatter)) &
    (transactions['date'] <= pd.Timestamp(end_date_scatter))
]

# Create scatter plot
fig = px.scatter(filtered_transactions_scatter, 
                 x='date', 
                 y='amount', 
                 title='Transaction Scatter Plot',
                 labels={'date': 'Date', 'amount': 'Amount ($)'},
                 color='amount',
                 color_continuous_scale=px.colors.sequential.Viridis)

# Update layout
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Amount ($)",
    coloraxis_colorbar=dict(title="Amount ($)")
)

st.plotly_chart(fig, use_container_width=True, key="transaction_scatter_plot")

# =====================
# Line Graph: Total Transaction Amount Over Time
# =====================
st.markdown("---")
st.subheader("💰 Total Transaction Amount Over Time")

# Aggregate transaction amounts by day
daily_transactions = transactions.groupby(transactions['date'].dt.date)['amount'].sum().reset_index()
daily_transactions.columns = ['date', 'total_amount']

# Create line graph
fig = px.line(daily_transactions, 
              x='date', 
              y='total_amount', 
              title='Total Transaction Amount Over Time',
              labels={'date': 'Date', 'total_amount': 'Total Amount ($)'},
              line_shape='linear')

# Update layout
fig.update_layout(
    xaxis_title="Date",
    yaxis_title="Total Amount ($)",
    hovermode='x unified'
)

# Display the graph
st.plotly_chart(fig, use_container_width=True, key="transaction_amount_line_graph")