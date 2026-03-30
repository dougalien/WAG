st.header("1. Location")

if st.button("📍 Use My Location", use_container_width=True):
    loc = get_geolocation()

    if loc and "lat" in loc:
        st.session_state.lat = loc["lat"]
        st.session_state.lon = loc["lon"]

        st.session_state.location_name = reverse_geocode(
            st.session_state.lat,
            st.session_state.lon
        )

    elif loc and "error" in loc:
        st.error(f"Location error: {loc['error']}")

if st.session_state.location_name:
    st.success(st.session_state.location_name)