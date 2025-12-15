import streamlit as st
import random
from streamlit_autorefresh import st_autorefresh

# ------------------ CONFIG ------------------
st.set_page_config(
    page_title="Stock Broker Dashboard",
    layout="centered"
)

SUPPORTED_STOCKS = ["GOOG", "TSLA", "AMZN", "META", "NVDA"]

# ------------------ AUTO REFRESH ------------------
# Refresh every 1 second (1000 ms)
st_autorefresh(interval=1000, key="stock_refresh")

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
            st.success("Login successful")
        else:
            st.error("Please enter an email")

# ------------------ DASHBOARD PAGE ------------------
def dashboard_page():
    st.title("📊 Live Stock Dashboard")
    st.write(f"👤 User: **{st.session_state.email}**")

    # ---- LOGOUT ----
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.stop()

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
            # Random price update
            st.session_state.prices[stock] += random.randint(-5, 5)

            st.metric(
                label=stock,
                value=f"${st.session_state.prices[stock]}"
            )

# ------------------ MAIN ------------------
if not st.session_state.logged_in:
    login_page()
else:
    dashboard_page()
