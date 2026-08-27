import os

import streamlit as st

st.set_page_config(page_title="ISI Platform", layout="wide")

st.title("ISI Platform")
st.caption("Authenticated application foundation — ISI-00/01")
st.info("Authentication and product entitlement routing will be implemented in ISI-02.")

left, right = st.columns(2)
with left:
    st.subheader("SIMPA")
    st.write("Domain boundary reserved. No fake business functionality in the foundation phase.")
with right:
    st.subheader("ORDO")
    st.write("Domain boundary reserved. No fake business functionality in the foundation phase.")

st.caption(f"API base: {os.getenv('API_BASE_URL', 'http://localhost:8000')}")
