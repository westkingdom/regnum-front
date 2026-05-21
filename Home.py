from dotenv import load_dotenv
load_dotenv(".env.local", override=False)

import streamlit as st

st.set_page_config(page_title="WKRegnum - West Kingdom Regnum Portal")

pg = st.navigation(
    {
        "Portal": [
            st.Page("pages/home.py", title="Home", default=True),
            st.Page("pages/0_Login.py", title="Login", url_path="login"),
            st.Page("pages/1_Groups.py", title="Groups"),
            st.Page("pages/2_Regnum.py", title="Regnum"),
        ],
        "Forms": [
            st.Page("pages/5_Duty_Request.py", title="Duty Request"),
            st.Page(
                "pages/6_West_Email_Account_Request.py",
                title="West Email Account Request",
                url_path="wk-email",
            ),
        ],
    }
)
pg.run()
