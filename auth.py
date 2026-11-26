import streamlit as st
import db


def login_gate():
    """Shows login/signup until the user is logged in, then returns the user."""
    if "user" in st.session_state:
        return st.session_state["user"]

    st.title("📚 Study Notes Assistant")
    st.caption("Log in to see your saved notes, or create an account.")
    tab_login, tab_signup = st.tabs(["Log in", "Sign up"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            go = st.form_submit_button("Log in")
        if go:
            user = db.verify_user(username.strip(), password)
            if user:
                st.session_state["user"] = user
                st.rerun()
            else:
                st.error("Wrong username or password.")

    with tab_signup:
        with st.form("signup_form"):
            new_user = st.text_input("Choose a username")
            new_pass = st.text_input("Choose a password (6+ characters)", type="password")
            confirm = st.text_input("Confirm password", type="password")
            go = st.form_submit_button("Create account")
        if go:
            if len(new_user.strip()) < 3:
                st.error("Username must be at least 3 characters.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters.")
            elif new_pass != confirm:
                st.error("Passwords do not match.")
            elif db.create_user(new_user.strip(), new_pass):
                st.success("Account created. Now log in from the first tab.")
            else:
                st.error("That username is taken.")

    st.stop()   # nothing below this runs until the user logs in