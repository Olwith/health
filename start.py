import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Set up SQLite database connection
conn = sqlite3.connect('health_tracker.db')
c = conn.cursor()

# Create tables (if not exist)
c.execute('''CREATE TABLE IF NOT EXISTS facilities (id INTEGER PRIMARY KEY, name TEXT, address TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS issues (id INTEGER PRIMARY KEY, type TEXT, location TEXT, description TEXT, lat REAL, lon REAL)''')
conn.commit()

# Geocoder
geolocator = Nominatim(user_agent="health_tracker")

# Streamlit app layout
st.title("Community Health Tracker")

# User input form for reporting health issues
with st.form(key='issue_form'):
    st.header("Report a Health Issue")
    issue_type = st.selectbox("Select Health Issue Type", ["Flu", "Malaria", "Diarrhea", "Other"])
    location = st.text_input("Location")
    description = st.text_area("Description")
    submit_button = st.form_submit_button("Report Issue")

    if submit_button:
        # Geocode location
        location_data = geolocator.geocode(location)
        if location_data:
            # Save issue to database with coordinates
            lat, lon = location_data.latitude, location_data.longitude
            c.execute("INSERT INTO issues (type, location, description, lat, lon) VALUES (?, ?, ?, ?, ?)",
                      (issue_type, location, description, lat, lon))
            conn.commit()
            st.success("Issue reported successfully!")
        else:
            st.error("Location not found.")

# Create a Folium map
m = folium.Map(location=[-1.286389, 36.817223], zoom_start=12)  # Example: Nairobi

# Retrieve and plot issues on the map
c.execute("SELECT * FROM issues")
issues = c.fetchall()

for issue in issues:
    issue_id, issue_type, location, description, lat, lon = issue
    folium.Marker(
        location=[lat, lon],
        popup=f"<strong>{issue_type}</strong><br>{description}<br>{location}",
        icon=folium.Icon(color="red")
    ).add_to(m)

# Display the map using Streamlit
st_data = st_folium(m, width=725)

# Display metrics dashboard with filtering options
st.header("Metrics Dashboard")
filter_type = st.selectbox("Filter by Health Issue Type", ["All"] + ["Flu", "Malaria", "Diarrhea", "Other"])

# Query to retrieve issues based on the filter
if filter_type == "All":
    query = "SELECT * FROM issues"
else:
    query = "SELECT * FROM issues WHERE type = ?"
    issues_filtered = c.execute(query, (filter_type,)).fetchall()
    issues = issues_filtered

# Get total reported issues for the selected type
if filter_type == "All":
    c.execute("SELECT COUNT(*) FROM issues")
else:
    c.execute("SELECT COUNT(*) FROM issues WHERE type = ?", (filter_type,))
total_issues = c.fetchone()[0]
st.metric("Total Reported Health Issues", total_issues)

# Convert issues to a DataFrame for table display
issues_df = pd.DataFrame(issues, columns=["ID", "Type", "Location", "Description", "Latitude", "Longitude"])

# Display issues in a table
st.subheader("Reported Health Issues")
st.dataframe(issues_df)

# Visualization with Matplotlib
st.subheader("Health Issue Distribution")
issue_counts = issues_df['Type'].value_counts()

# Bar chart
plt.figure(figsize=(10, 5))
plt.bar(issue_counts.index, issue_counts.values, color='skyblue')
plt.title("Reported Health Issues by Type")
plt.xlabel("Health Issue Type")
plt.ylabel("Count")
st.pyplot(plt)

# Pie chart
plt.figure(figsize=(8, 8))
plt.pie(issue_counts, labels=issue_counts.index, autopct='%1.1f%%', startangle=140)
plt.title("Distribution of Reported Health Issues")
st.pyplot(plt)

# Close database connection
conn.close()


