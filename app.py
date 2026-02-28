from flask import Flask, render_template, request, session, redirect, url_for, flash
import pandas as pd
import json
import math
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# 🔐 FIXED SECRET KEY
app.config['SECRET_KEY'] = "ev_charge_finder_secret_key_2026"

DATABASE = "users.db"
df = None


# ==============================
# DATABASE CONNECTION
# ==============================

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


init_db()


# ==============================
# LOAD CSV DATA
# ==============================

csv_file = "india_ev_charging_stations.csv"

if os.path.exists(csv_file):
    try:
        df = pd.read_csv(csv_file)
        df.columns = df.columns.str.strip()
        print(f"✅ Loaded {len(df)} EV Stations")
    except Exception as e:
        print("CSV Load Error:", e)
        df = pd.DataFrame()
else:
    print("❌ CSV file not found!")
    df = pd.DataFrame()


# ==============================
# DISTANCE CALCULATION
# ==============================

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) *
         math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# ==============================
# PUBLIC ROUTE (Landing Page)
# ==============================

@app.route('/')
def landing():
    return render_template("home.html")


# ==============================
# AUTH ROUTES
# ==============================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = generate_password_hash(request.form['password'])

        try:
            conn = get_db_connection()
            conn.execute(
                "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                (username, email, password)
            )
            conn.commit()
            conn.close()

            flash("Account created successfully! Please login.", "success")
            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash("Username or Email already exists!", "error")

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash("Welcome back!", "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!", "error")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('landing'))


# ==============================
# PROTECTED DASHBOARD
# ==============================

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template("index.html", username=session['username'])


# ==============================
# MAIN EV SEARCH ROUTE
# ==============================

@app.route('/result', methods=['POST'])
def result():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    try:
        user_lat = float(request.form['latitude'])
        user_lon = float(request.form['longitude'])
        battery = float(request.form.get('battery_percent', 50))

        safe_battery = max(0, battery - 5)
        max_range = safe_battery * 2.5

        nearby_stations = []

        for _, row in df.iterrows():
            try:
                s_lat = float(row['lattitude'])
                s_lon = float(row['longitude'])

                dist = calculate_distance(user_lat, user_lon, s_lat, s_lon)

                if dist <= max_range:
                    nearby_stations.append({
                        "name": str(row.get('name', 'N/A')),
                        "lat": s_lat,
                        "lon": s_lon,
                        "distance": round(dist, 2),
                        "address": str(row.get('address', 'N/A')),
                        "city": str(row.get('city', 'N/A')),
                        "state": str(row.get('state', 'N/A'))
                    })
            except:
                continue

        nearby_stations.sort(key=lambda x: x['distance'])

        return render_template(
            "result.html",
            stations=nearby_stations,
            stations_json=json.dumps(nearby_stations),
            count=len(nearby_stations),
            battery=int(battery),
            max_range=round(max_range, 1),
            username=session['username'],
            u_lat=user_lat,
            u_lon=user_lon
        )

    except Exception as e:
        flash(f"Error: {str(e)}", "error")
        return redirect(url_for('dashboard'))


# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True)
