def render_location():
    st.markdown('<div class="section-label">2. Location</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="main-card">
        <div class="small-note">
            This app is designed for phone use. You can use phone location or enter a city and state.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Use My Location", use_container_width=True):
        pos = current_position()
        st.session_state.raw_location_result = pos

        if isinstance(pos, dict):
            lat = pos.get("latitude")
            lon = pos.get("longitude")

            if lat is not None and lon is not None:
                st.session_state.lat = lat
                st.session_state.lon = lon
                st.session_state.location_error = ""
                try:
                    st.session_state.location_name = reverse_geocode(lat, lon)
                except Exception as e:
                    st.session_state.location_error = f"Reverse geocode error: {e}"
            else:
                st.session_state.location_error = "Location returned, but coordinates were missing."
        else:
            st.session_state.location_error = "No location returned. You can enter a city and state below."

    st.session_state.manual_place = st.text_input(
        "Or enter city and state",
        value=st.session_state.manual_place,
        placeholder="Boston, MA"
    )

    if st.button("Use Entered Place", use_container_width=True):
        if not st.session_state.manual_place.strip():
            st.warning("Enter a city and state first.")
        else:
            try:
                result = geocode_place(st.session_state.manual_place.strip())
                if result:
                    st.session_state.lat = result["lat"]
                    st.session_state.lon = result["lon"]
                    st.session_state.location_name = result["place_name"]
                    st.session_state.location_error = ""
                else:
                    st.session_state.location_error = "Place not found."
            except Exception as e:
                st.session_state.location_error = f"Place lookup error: {e}"

    if st.session_state.location_name:
        st.success(st.session_state.location_name)

    if st.session_state.location_error:
        st.error(st.session_state.location_error)