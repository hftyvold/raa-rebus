import streamlit as st

from streamlit_js_eval import get_geolocation
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic

def st_location():
    st.subheader("Show your location (test)")
    if "request_location" not in st.session_state:
        st.session_state.request_location = False
    if "user_location" not in st.session_state:
        st.session_state.user_location = None
    if "geo_request_id" not in st.session_state:
        st.session_state.geo_request_id = 0

    button_label = "Fetch your location" if st.session_state.user_location is None else "Refresh location"

    if st.button(button_label, key="fetch_location"):
        st.session_state.request_location = True
        st.session_state.geo_request_id += 1

    if st.session_state.user_location and st.button("Clear location", key="clear_location"):
        st.session_state.user_location = None
        st.session_state.request_location = False

    if st.session_state.request_location:
        location = get_geolocation(component_key=f"geo_{st.session_state.geo_request_id}")

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
        target_locations = {'Bislet stadion': (59.925020, 10.733377),
                            'Sandvika stasjon': (59.892642, 10.525238),
                            'Oslo Rådhus': (59.912260, 10.733885),
                            'Birkelunden': (59.926771, 10.760136)}
        location_target = target_locations[st.selectbox("Select a target location to compare distance:", options=list(target_locations.keys()))]
        lat = st.session_state.user_location.get("latitude")
        lon = st.session_state.user_location.get("longitude")
        accuracy = st.session_state.user_location.get("accuracy")

        st.write(f"Latitude: {lat}")
        st.write(f"Longitude: {lon}")
        st.write(f"Accuracy: {accuracy} meters")

        if lat is not None and lon is not None:
            distance = geodesic((lat, lon), location_target).meters
            st.info(f"Approximate distance to target: {distance:.2f} meters")
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