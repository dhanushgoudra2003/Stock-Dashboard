# app.py

from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, emit
import random
import threading
import time
from collections import deque
import numpy as np
import pandas as pd 
import pandas_ta as ta 

# --- Configuration ---
app = Flask(__name__)
# IMPORTANT: Set a secret key for session management
app.config['SECRET_KEY'] = 'your_super_secret_key_change_me' 
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Global State ---
SUPPORTED_STOCKS = ['GOOG', 'TSLA', 'AMZN', 'META', 'NVDA']
user_subscriptions = {} 
current_prices = {stock: round(random.uniform(100, 1000), 2) for stock in SUPPORTED_STOCKS}

# Store the last 60 price points for charting
stock_history = {stock: deque([current_prices[stock]] * 60, maxlen=60) for stock in SUPPORTED_STOCKS}

# Simulate the user database: {'email': {'password': '...', 'holdings': {'GOOG': 10, ...}, 'cash_balance': 10000.0}}
USER_DB = {
    'user1@example.com': {
        'password': 'password123', # Stronger password simulation
        'holdings': {'GOOG': 10, 'TSLA': 5}, 
        'cash_balance': 50000.0
    },
    'user2@example.com': {
        'password': 'securepass', 
        'holdings': {'META': 15, 'NVDA': 3}, 
        'cash_balance': 75000.0
    }
}

# --- Stock Price Generator Thread ---
def price_updater():
    """Generates random price updates, calculates analysis, and portfolio metrics."""
    while True:
        # Update prices and history
        for stock in SUPPORTED_STOCKS:
            movement = random.uniform(-1, 1) 
            new_price = current_prices[stock] * (1 + movement / 1000.0)
            current_prices[stock] = round(max(1.0, new_price), 2) 
            stock_history[stock].append(current_prices[stock])
            
        # --- 1. Calculate Technical Analysis (SMA) using pandas-ta ---
        analysis_data = {}
        for stock in SUPPORTED_STOCKS:
            prices_array = np.array(stock_history[stock])
            
            if len(prices_array) >= 20:
                price_series = pd.Series(prices_array)
                sma_series = ta.sma(price_series, length=20)
                sma_20 = sma_series.iloc[-1]
                
                analysis_data[stock] = {'sma_20': round(sma_20, 2) if not pd.isna(sma_20) else 'N/A'}
            else:
                analysis_data[stock] = {'sma_20': 'N/A'}
            
        # --- 2. Calculate Portfolio Metrics for all users ---
        portfolio_distribution = {}
        for email, user_data in USER_DB.items():
            holdings = user_data['holdings']
            cash_balance = user_data['cash_balance']
            
            stock_value = sum(
                (holdings.get(ticker, 0) * current_prices.get(ticker, 0)) 
                for ticker in SUPPORTED_STOCKS
            )
            total_portfolio_value = stock_value + cash_balance
            
            # Simplified cost basis for P/L simulation (assuming an average cost of 400 per stock)
            # In a real app, cost basis would be tracked per transaction.
            simplified_cost_basis = sum(
                (holdings.get(ticker, 0) * 400.0) for ticker in SUPPORTED_STOCKS
            )
            
            portfolio_distribution[email] = {
                'cash_balance': round(cash_balance, 2),
                'stock_value': round(stock_value, 2),
                'total_value': round(total_portfolio_value, 2),
                'total_pl': round(stock_value - simplified_cost_basis, 2),
                'holdings': {
                    ticker: {
                        'quantity': holdings.get(ticker, 0),
                        'current_value': round(holdings.get(ticker, 0) * current_prices.get(ticker, 0), 2),
                        'current_price': current_prices.get(ticker, 0),
                        'percent': round(holdings.get(ticker, 0) * current_prices.get(ticker, 0) / total_portfolio_value * 100, 2) if total_portfolio_value else 0
                    }
                    for ticker in SUPPORTED_STOCKS if holdings.get(ticker, 0) > 0
                }
            }

        # --- 3. Emit All Real-Time Data ---
        socketio.emit('real_time_data', {
            'prices': current_prices,
            'analysis': analysis_data,
            'portfolio': portfolio_distribution
        })
        
        time.sleep(1) 

# Start the price updater thread when the application starts
price_thread = threading.Thread(target=price_updater)
price_thread.daemon = True 
price_thread.start()

# --- Routes ---
@app.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('login'))
    
    user_email = session['email']
    user_subscriptions.setdefault(user_email, [])

    user_holdings = USER_DB.get(user_email, {}).get('holdings', {}) 
    
    return render_template(
        'index.html', 
        user_email=user_email, 
        subscribed_stocks=user_subscriptions[user_email],
        available_stocks=SUPPORTED_STOCKS,
        user_holdings=user_holdings
    )

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        
        if email in USER_DB:
            return render_template('signup.html', error="Email already registered. Try logging in.")
        
        if len(password) < 8: # Added strong password simulation
            return render_template('signup.html', error="Password must be at least 8 characters long.")
        
        if not email or not password:
            return render_template('signup.html', error="Please fill in all fields.")

        USER_DB[email] = {
            'password': password,
            'holdings': {},
            'cash_balance': 100000.0 # Starting cash balance
        }
        session['email'] = email
        user_subscriptions[email] = []
        return redirect(url_for('index'))
        
    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'email' in session: 
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email').lower()
        password = request.form.get('password')
        
        user_data = USER_DB.get(email)
        
        if user_data and user_data['password'] == password:
            session['email'] = email
            user_subscriptions.setdefault(email, []) 
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid email or password. Please try again.")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect(url_for('login'))

@app.route('/subscribe/<ticker>')
def subscribe(ticker):
    user_email = session.get('email')
    if not user_email or ticker not in SUPPORTED_STOCKS:
        return redirect(url_for('index'))

    if ticker not in user_subscriptions.get(user_email, []):
        user_subscriptions.setdefault(user_email, []).append(ticker)
        user_subscriptions[user_email].sort() 
        
    return redirect(url_for('index'))

@app.route('/trade', methods=['POST'])
def trade():
    user_email = session.get('email')
    if not user_email or user_email not in USER_DB:
        return redirect(url_for('login'))

    ticker = request.form.get('ticker')
    action = request.form.get('action') 
    
    try:
        quantity = int(request.form.get('quantity'))
    except (ValueError, TypeError):
        return redirect(url_for('index'))

    if ticker not in SUPPORTED_STOCKS or quantity <= 0:
        return redirect(url_for('index'))

    current_price = current_prices[ticker]
    cost = current_price * quantity
    user_data = USER_DB[user_email]
    
    if action == 'BUY':
        if user_data['cash_balance'] >= cost:
            user_data['cash_balance'] -= cost
            user_data['holdings'][ticker] = user_data['holdings'].get(ticker, 0) + quantity
            if ticker not in user_subscriptions.get(user_email, []):
                 user_subscriptions.setdefault(user_email, []).append(ticker)
        
    elif action == 'SELL':
        current_holding = user_data['holdings'].get(ticker, 0)
        if current_holding >= quantity:
            user_data['cash_balance'] += cost
            user_data['holdings'][ticker] = current_holding - quantity
            
            if user_data['holdings'][ticker] == 0:
                del user_data['holdings'][ticker]
                
    return redirect(url_for('index'))

@socketio.on('connect')
def handle_connect():
    if 'email' not in session:
        return False

if __name__ == '__main__':
    socketio.run(app, debug=True)
