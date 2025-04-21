import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import folium_static
import geopandas as gpd

st.set_page_config(page_title="Live Multi-Disaster Map", layout="wide")
st.title("🌐 Live Multi-Disaster Tracker")
st.caption("Earthquakes, Tsunami Alerts, Floods & Drought-Prone Areas")

# Initialize Folium map
m = folium.Map(location=[10, 20], zoom_start=2)

# --------------------------
# 1. Live Earthquakes (USGS)
# --------------------------
st.subheader("📍 Earthquakes & Tsunami Alerts")

usgs_url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
eq_data = requests.get(usgs_url).json()

earthquakes = []
for feature in eq_data["features"]:
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]
    is_tsunami = "Yes" if props.get("tsunami") == 1 else "No"

    earthquakes.append({
        "Place": props["place"],
        "Magnitude": props["mag"],
        "Time": pd.to_datetime(props["time"], unit='ms'),
        "Longitude": coords[0],
        "Latitude": coords[1],
        "URL": props["url"],
        "Tsunami": is_tsunami
    })

df_eq = pd.DataFrame(earthquakes)

for _, row in df_eq.iterrows():
    color = "blue" if row["Tsunami"] == "Yes" else "red" if row["Magnitude"] >= 5 else "orange" if row["Magnitude"] >= 3 else "green"
    popup_info = f"""
    <b>Place:</b> {row['Place']}<br>
    <b>Magnitude:</b> {row['Magnitude']}<br>
    <b>Time:</b> {row['Time']}<br>
    <b>Tsunami:</b> {row['Tsunami']}<br>
    <a href="{row['URL']}" target="_blank">More info</a>
    """
    folium.CircleMarker(
        location=[row["Latitude"], row["Longitude"]],
        radius=max(2, row["Magnitude"] * 2),
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=folium.Popup(popup_info, max_width=300),
        tooltip=row["Place"]
    ).add_to(m)

# --------------------------
# 2. Live Flood Alerts (GDACS)
# --------------------------
st.subheader("🌊 Flood Alerts (GDACS)")

try:
    gdacs_url = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/FL"
    gdacs_data = requests.get(gdacs_url).json()

    for event in gdacs_data.get("features", []):
        coords = event["geometry"]["coordinates"]
        props = event["properties"]
        popup = f"""
        <b>Flood Alert:</b> {props.get('eventname', 'N/A')}<br>
        <b>Country:</b> {props.get('country', 'N/A')}<br>
        <b>Alert Level:</b> {props.get('alertlevel', 'N/A')}
        """
        folium.Marker(
            location=[coords[1], coords[0]],
            icon=folium.Icon(color='blue', icon='tint', prefix='fa'),
            popup=folium.Popup(popup, max_width=300)
        ).add_to(m)
except Exception as e:
    st.warning("⚠️ Unable to fetch flood data from GDACS.")

# --------------------------
# 3. Drought-Prone Areas (Static)
# --------------------------
st.subheader("🌵 Drought-Prone Areas")

try:
    drought_data = gpd.read_file("drought_prone_areas.geojson")

    folium.GeoJson(
        drought_data,
        name="Drought Zones",
        style_function=lambda x: {
            'fillColor': 'brown',
            'color': 'brown',
            'weight': 1,
            'fillOpacity': 0.2,
        },
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["Region"])
    ).add_to(m)
except Exception as e:
    st.warning("⚠️ Please upload a valid drought_prone_areas.geojson file.")

# --------------------------
# Final Map Display
# --------------------------
folium.LayerControl().add_to(m)
folium_static(m, width=1200, height=700)

# Expandable raw data
with st.expander("📊 View Earthquake Data"):
    st.dataframe(df_eq)
