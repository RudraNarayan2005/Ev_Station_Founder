from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
from knn_clustering import EVStationClusterer
import pandas as pd
import json
import math
import os
import sqlite3
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from werkzeug.security import generate_password_hash, check_password_hash
import requests as http_requests

app = Flask(__name__)

# 🔐 SECRET KEY
app.config['SECRET_KEY'] = "ev_charge_finder_secret_key_2026"

DATABASE = "users.db"
df = None
ml_model = None
clusterer = None


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

        # Clean column names
        df.columns = df.columns.str.strip()

        # 🔧 FIX: Clean latitude and longitude values
        df['lattitude'] = (
            df['lattitude']
            .astype(str)
            .str.replace(',', '')
            .str.strip()
            .astype(float)
        )

        df['longitude'] = (
            df['longitude']
            .astype(str)
            .str.replace(',', '')
            .str.strip()
            .astype(float)
        )

        print(f"✅ Loaded {len(df)} EV Stations")

    except Exception as e:
        print("CSV Load Error:", e)
        df = pd.DataFrame()
else:
    print("❌ CSV file not found!")
    df = pd.DataFrame()


# ==============================
# MACHINE LEARNING MODEL
# ==============================

def train_demand_model():
    global ml_model

    if df.empty:
        return

    try:
        X = df[['lattitude', 'longitude']].values

        # Simulated demand values
        y = np.random.randint(20, 200, size=len(df))

        ml_model = RandomForestRegressor(n_estimators=50)
        ml_model.fit(X, y)

        print("✅ ML Demand Model Trained")

    except Exception as e:
        print("ML Training Error:", e)


train_demand_model()


def predict_station_demand(lat, lon):
    if ml_model is None:
        return 0

    try:
        prediction = ml_model.predict([[lat, lon]])
        return int(prediction[0])
    except:
        return 0


# ==============================
# KNN CLUSTERING MODEL
# ==============================

def init_clusterer():
    global clusterer
    if df is not None and not df.empty:
        try:
            clusterer = EVStationClusterer(df)
            clusterer.fit(n_clusters=15, n_neighbors=5)
            print("✅ KNN Clusterer Ready")
        except Exception as e:
            print("KNN Clustering Error:", e)


init_clusterer()


# ==============================
# DISTANCE CALCULATION
# ==============================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2 +
        math.cos(math.radians(lat1)) *
        math.cos(math.radians(lat2)) *
        math.sin(dlon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


# ==============================
# LANDING PAGE
# ==============================

@app.route('/')
def landing():
    return render_template("home.html")


# ==============================
# REGISTER
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
                "INSERT INTO users (username,email,password) VALUES (?,?,?)",
                (username, email, password)
            )

            conn.commit()
            conn.close()

            flash("Account created successfully!", "success")

            return redirect(url_for('login'))

        except sqlite3.IntegrityError:
            flash("Username or Email already exists!", "error")

    return render_template("register.html")


# ==============================
# LOGIN
# ==============================

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_db_connection()

        user = conn.execute(
            "SELECT * FROM users WHERE username=?",
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


# ==============================
# LOGOUT
# ==============================

@app.route('/logout')
def logout():

    session.clear()

    flash("Logged out successfully!", "success")

    return redirect(url_for('landing'))


# ==============================
# DASHBOARD
# ==============================

@app.route('/dashboard')
def dashboard():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    return render_template(
        "index.html",
        username=session['username']
    )


# ==============================
# EV SEARCH RESULT
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

                dist = calculate_distance(
                    user_lat,
                    user_lon,
                    s_lat,
                    s_lon
                )

                if dist <= max_range:

                    demand = predict_station_demand(s_lat, s_lon)

                    nearby_stations.append({

                        "name": str(row.get('name', 'N/A')),

                        "lat": s_lat,
                        "lon": s_lon,

                        "distance": round(dist, 2),

                        "demand_score": demand,

                        "address": str(row.get('address', 'N/A')),

                        "city": str(row.get('city', 'N/A')),

                        "state": str(row.get('state', 'N/A')),

                        # KNN cluster defaults (overwritten below if clusterer is ready)
                        "cluster_id": -1,
                        "cluster_color": "#888888"

                    })

            except:
                continue

        # ── KNN: attach cluster zone info to each nearby station ──────────────
        if clusterer is not None and nearby_stations:
            try:
                knn_results = clusterer.find_nearest(user_lat, user_lon, k=min(20, len(nearby_stations)))
                # Build lookup by (lat, lon)
                knn_lookup = {(r['lat'], r['lon']): r for r in knn_results}
                for s in nearby_stations:
                    key = (s['lat'], s['lon'])
                    if key in knn_lookup:
                        s['cluster_id']    = knn_lookup[key]['cluster_id']
                        s['cluster_color'] = knn_lookup[key]['cluster_color']
            except Exception as e:
                print("KNN lookup error:", e)

        # Smart ranking
        nearby_stations.sort(
            key=lambda x: (x['distance'], -x['demand_score'])
        )

        # User's cluster zone info
        user_cluster = None
        if clusterer is not None:
            try:
                user_cluster = clusterer.predict_cluster(user_lat, user_lon)
            except:
                pass

        # All stations for background cluster map display
        all_stations_json = json.dumps(
            clusterer.get_all_clustered() if clusterer is not None else []
        )

        return render_template(

            "result.html",

            stations=nearby_stations,

            stations_json=json.dumps(nearby_stations),

            count=len(nearby_stations),

            battery=int(battery),

            max_range=round(max_range, 1),

            username=session['username'],

            u_lat=user_lat,
            u_lon=user_lon,

            user_cluster=user_cluster,

            all_stations_json=all_stations_json

        )

    except Exception as e:

        flash(f"Error: {str(e)}", "error")

        return redirect(url_for('dashboard'))


# ==============================
# KNN NEAREST STATIONS (JSON API)
# GET /knn?lat=12.97&lon=77.59&k=5
# ==============================

@app.route('/knn')
def knn_nearest():

    if 'user_id' not in session:
        return {"error": "Login required"}, 401

    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        k   = min(int(request.args.get('k', 5)), 20)
    except (TypeError, ValueError):
        return {"error": "Invalid lat/lon parameters"}, 400

    if clusterer is None:
        return {"error": "Clustering model not initialised"}, 500

    nearest      = clusterer.find_nearest(lat, lon, k=k)
    user_cluster = clusterer.predict_cluster(lat, lon)

    return {
        "user_cluster": user_cluster,
        "nearest":      nearest,
        "count":        len(nearest),
    }


# ==============================
# CLUSTER MAP PAGE
# GET /cluster-map
# ==============================

@app.route('/cluster-map')
def cluster_map():

    if 'user_id' not in session:
        return redirect(url_for('login'))

    if clusterer is None:
        flash("Clustering model not ready.", "error")
        return redirect(url_for('dashboard'))

    stations_data = clusterer.get_all_clustered()
    cluster_data  = clusterer.cluster_summary()

    return render_template(
        "cluster_map.html",
        username       = session['username'],
        stations_json  = json.dumps(stations_data),
        clusters_json  = json.dumps(cluster_data),
        total_stations = len(stations_data),
        total_clusters = len(cluster_data),
    )



# ==============================
# OPENCAGE API KEY
# ==============================

OPENCAGE_API_KEY = "4da581d65658457e9ebc72841754dc48"


# ==============================
# AUTOCOMPLETE — OpenCage API
# GET /autocomplete?q=bhubaneswar
# Returns [{display_name, full_address, lat, lon}, ...]
# ==============================

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    try:
        resp = http_requests.get(
            'https://api.opencagedata.com/geocode/v1/json',
            params={
                'q':              query,
                'key':            OPENCAGE_API_KEY,
                'limit':          6,
                'language':       'en',
                'countrycode':    'in',       # India only
                'no_annotations': 1,
                'no_record':      1,
            },
            timeout=5
        )
        data = resp.json()
        results = []
        for item in data.get('results', []):
            comp     = item.get('components', {})
            geometry = item.get('geometry', {})
            # Build clean short label: neighbourhood → city → state (max 3 parts)
            name_parts = []
            for field in ['neighbourhood', 'suburb', 'village', 'town',
                          'city', 'county', 'state_district', 'state']:
                val = comp.get(field, '')
                if val and val not in name_parts:
                    name_parts.append(val)
                if len(name_parts) == 3:
                    break
            short_name   = ', '.join(name_parts) if name_parts else item.get('formatted', '')
            full_address = item.get('formatted', short_name)
            results.append({
                'display_name': short_name,
                'full_address': full_address,
                'lat':          geometry.get('lat', 0),
                'lon':          geometry.get('lng', 0),
            })
        return jsonify(results)
    except Exception as e:
        print("Autocomplete error:", e)
        return jsonify([])


# ==============================
# RUN APP
# ==============================

if __name__ == "__main__":
    app.run(debug=True)
