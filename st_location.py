import streamlit as st

from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium

def st_location():
    st.subheader("Show your location (test)")
    if "request_location" not in st.session_state:
        st.session_state.request_location = False

    if "user_location" not in st.session_state:
        st.session_state.user_location = None

    if st.button("Show your location"):
        st.session_state.request_location = True

    if st.session_state.request_location:
        location = get_geolocation()

        if location and "error" in location:
            st.error(f"Location error: {location['error']['message']}")
            st.session_state.request_location = False

        elif location and "coords" in location:
            st.session_state.user_location = location["coords"]
            st.session_state.request_location = False
            st.success("Location received.")

        else:
            st.info("Waiting for browser location permission or response...")

    if st.session_state.user_location:
        lat = st.session_state.user_location.get("latitude")
        lon = st.session_state.user_location.get("longitude")
        accuracy = st.session_state.user_location.get("accuracy")

        st.write(f"Latitude: {lat}")
        st.write(f"Longitude: {lon}")
        st.write(f"Accuracy: {accuracy} meters")

        if lat is not None and lon is not None:
            user_map = folium.Map(
                location=[float(lat), float(lon)],
                zoom_start=17,
                control_scale=True,
            )

            popup_text = (
                f"Your location (accuracy: {round(float(accuracy))} m)"
                if accuracy is not None
                else "Your location"
            )

            # Solid vector dot (no external icon images)
            folium.CircleMarker(
                location=[float(lat), float(lon)],
                radius=8,
                color="#1f77b4",
                weight=2,
                fill=True,
                fill_color="#1f77b4",
                fill_opacity=0.9,
                tooltip="You are here",
                popup=popup_text,
            ).add_to(user_map)

            # Optional: visualize GPS uncertainty if accuracy is available
            if accuracy is not None:
                folium.Circle(
                    location=[float(lat), float(lon)],
                    radius=float(accuracy),  # meters
                    color="#1f77b4",
                    weight=1,
                    fill=True,
                    fill_color="#1f77b4",
                    fill_opacity=0.12,
                ).add_to(user_map)

            st_folium(user_map, width=700, height=420, returned_objects=[])