import streamlit as st
import time

# Configure the page
st.set_page_config(
    page_title="WKRegnum - Redirecting",
    page_icon="🔄",
    layout="centered"
)

# Set the new service URL
new_service_url = "https://wkregnum-njxuammdla-uw.a.run.app"

# Display redirect message
st.title("WKRegnum Service Update")
st.write("The WKRegnum service has moved to a new location.")
st.write(f"You will be redirected to {new_service_url} in 5 seconds...")

# Countdown progress bar
progress_bar = st.progress(0)
for i in range(5):
    progress_bar.progress((i+1)/5)
    time.sleep(1)

# JavaScript for automatic redirect
redirect_js = f"""
<script>
    window.location.href = "{new_service_url}";
</script>
"""
st.markdown(redirect_js, unsafe_allow_html=True)

# Manual redirect link
st.write("If you are not redirected automatically, please click the link below:")
st.markdown(f"[Go to WKRegnum]({new_service_url})", unsafe_allow_html=False) 