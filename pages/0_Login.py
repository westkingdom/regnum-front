import streamlit as st
from utils.google_oauth import (
    get_authorization_url,
    exchange_code_for_user_info,
    check_group_membership,
    login_user,
    logout_user,
    is_authenticated,
    get_current_user,
)
from utils.logger import app_logger as logger

st.set_page_config(page_title="Login - WKRegnum", page_icon="🔐")


def _handle_oauth_callback(code: str, state: str) -> None:
    with st.spinner("Signing you in…"):
        user_info = exchange_code_for_user_info(code, state)

    if not user_info:
        st.error("Sign-in failed. The session may have expired — please try again.")
        st.query_params.clear()
        st.rerun()
        return

    email = user_info.get("email", "")
    if not check_group_membership(email):
        logger.warning(f"Access denied — not in required group: {email}")
        st.error(
            f"Access denied. **{email}** is not a member of "
            f"`regnum-site@westkingdom.org`."
        )
        st.query_params.clear()
        return

    login_user(user_info)
    logger.info(f"User signed in via Google OAuth: {email}")
    st.query_params.clear()
    st.switch_page("Home.py")


def main():
    params = st.query_params

    # OAuth callback: Google redirects here with ?code=...&state=...
    if "code" in params and "state" in params:
        _handle_oauth_callback(params["code"], params["state"])
        return

    # Already authenticated
    if is_authenticated():
        user = get_current_user()
        st.success(f"Signed in as **{user['name']}** ({user['email']})")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Go to Home Page"):
                st.switch_page("Home.py")
        with col2:
            if st.button("Sign Out"):
                logout_user()
                st.rerun()
        return

    # Sign-in page
    st.title("WKRegnum Login")
    st.markdown(
        "Sign in with your West Kingdom Google account. "
        "Access is restricted to members of **regnum-site@westkingdom.org**."
    )
    st.link_button(
        "Sign in with Google",
        get_authorization_url(),
        use_container_width=True,
    )

    st.markdown("---")
    st.markdown("### Public Access")
    st.info("The Duty Request form is available without login.")
    if st.button("Access Duty Request Form"):
        st.switch_page("pages/5_Duty_Request.py")


main()
