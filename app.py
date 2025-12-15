import streamlit as st
import random
import time

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Stock Broker Dashboard",
    layout="centered"
)

SUPPORTED_STOCKS = ["GOOG", "TSLA", "AMZN", "META", "NVDA"]

# ------------------ SESSION STATE INIT ------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "email" not in st.session_state:
    st.session_state.email = ""

if "subscriptions" not in st.session_state:
    st.session_state.subscriptions = []

if "prices" not in st.session_state:
    st.session_state.prices = {}

# ------------------ LOGIN PAGE ------------------
def login_page():
    st.title("📈 Stock Broker Client Dashboard")
    st.subheader("Login")

    email = st.text_input("Enter your email")

    if st.button("Login"):
        if email:
            st.session_state.logged_in = True
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Please enter an email")

# ------------------ DASHBOARD PAGE ------------------
def dashboard_page():
    st.title("📊 Stock Dashboard")
    st.write(f"👤 User: **{st.session_state.email}**")

    # ---- LOGOUT ----
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    st.divider()

    # ---- SUBSCRIPTION ----
    st.subheader("Subscribe to Stocks")
    selected_stock = st.selectbox("Select Stock", SUPPORTED_STOCKS)

    if st.button("Subscribe"):
        if selected_stock not in st.session_state.subscriptions:
            st.session_state.subscriptions.append(selected_stock)
            st.session_state.prices[selected_stock] = random.randint(100, 500)
            st.success(f"Subscribed to {selected_stock}")
        else:
            st.warning("Already subscribed")

    st.divider()

    # ---- LIVE STOCK PRICES ----
    st.subheader("📈 Live Stock Prices")

    if not st.session_state.subscriptions:
        st.info("No stocks subscribed yet")
    else:
        for stock in st.session_state.subscriptions:
            # update price
            st.session_state.prices[stock] += random.randint(-5, 5)

            st.metric(
                label=stock,
                value=f"${st.session_state.prices[stock]}"
            )

    # ---- CLOUD SAFE AUTO REFRESH ----
    time.sleep(1)
    st.rerun()

# ------------------ MAIN ------------------
if not st.session_state.logged_in:
    login_page()
else:
    dashboard_page()
