
# ⚡ Smart EV Charge Finder

A Flask web application that helps electric vehicle owners in India find nearby charging stations based on their current location and remaining battery level. It uses **KNN + KMeans machine learning** to cluster stations geographically and predict the best options within the vehicle's range.

---

## Features

- **Battery-aware range calculation** — enter your battery percentage and the app computes the maximum distance you can travel before needing a charge
- **KNN nearest-station lookup** — uses a ball-tree KNN model with haversine distance for accurate geo-proximity search
- **KMeans geographic clustering** — groups ~1,500 stations across India into 15 regional zones, colour-coded on the map
- **Random Forest demand scoring** — ranks stations by estimated demand so you can prioritise quieter ones
- **Interactive cluster map** — full-screen map showing all stations coloured by zone with cluster summaries
- **Location autocomplete** — powered by the OpenCage Geocoding API (India only)
- **User authentication** — register, login, and logout with hashed passwords (Werkzeug)
- **Admin panel** — basic admin view for user management

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, Flask |
| ML / Data | scikit-learn (KMeans, KNN, RandomForest), pandas, numpy |
| Database | SQLite (`users.db`) |
| Frontend | Jinja2 templates, vanilla CSS/JS |
| Geocoding | OpenCage API |
| Deployment | Gunicorn, `runtime.txt` for platform configuration |

---

## Project Structure

```
Ev_Station_Founder-main/
├── app.py                          # Main Flask application & all routes
├── knn_clustering.py               # EVStationClusterer class (KMeans + KNN)
├── ml_model.py                     # ML model utilities
├── train_model.py                  # Standalone model training script
├── new_routes_to_add.py            # Helper for adding new station routes
├── database.py                     # Database helpers
├── india_ev_charging_stations.csv  # Dataset (~1,547 stations across India)
├── requirements.txt
├── runtime.txt
├── users.db                        # SQLite database (auto-created)
└── templates/
│   ├── home.html                   # Landing page
│   ├── login.html                  # Login page
│   ├── register.html               # Registration page
│   ├── index.html                  # Search dashboard
│   ├── result.html                 # Search results + map
│   ├── cluster_map.html            # Full cluster map view
│   └── admin.html                  # Admin panel
└── static/
    ├── style.css
    ├── stations.png
    └── forecast.png
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/Ev_Station_Founder.git
   cd Ev_Station_Founder
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the app**
   ```bash
   python app.py
   ```

4. **Open your browser** at `http://127.0.0.1:5000`

The SQLite database and ML models are initialised automatically on first run.

---

## Usage

1. **Register** a new account or **Login** with existing credentials
2. On the dashboard, enter your **location** (type to use autocomplete) and **battery percentage**
3. The app calculates your maximum range and finds all EV stations within reach
4. Results are displayed on an interactive map with distance, demand score, and cluster zone
5. Visit **Cluster Map** from the nav bar to explore all stations grouped by region

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET/POST` | `/register` | User registration |
| `GET/POST` | `/login` | User login |
| `GET` | `/logout` | Logout and clear session |
| `GET` | `/dashboard` | Search dashboard (auth required) |
| `POST` | `/result` | Submit search, get nearby stations |
| `GET` | `/knn?lat=&lon=&k=` | JSON API — K nearest stations |
| `GET` | `/cluster-map` | Interactive full cluster map |
| `GET` | `/autocomplete?q=` | Location autocomplete (OpenCage) |

---

## Dataset

`india_ev_charging_stations.csv` contains ~1,547 EV charging stations across India with the following fields:

| Field | Description |
|---|---|
| `name` | Station name |
| `state` | Indian state |
| `city` | City |
| `address` | Full address |
| `lattitude` | Latitude (decimal degrees) |
| `longitude` | Longitude (decimal degrees) |
| `type` | Charger type code |

---

## ML Models

### KMeans Geographic Clustering
Stations are clustered into **15 regional zones** using KMeans with `k-means++` initialisation. Coordinates are standardised before clustering so latitude and longitude contribute equally.

### KNN Nearest-Station Lookup
A ball-tree KNN model with **haversine metric** finds the K closest stations to any query point. Inputs are converted to radians for accurate spherical distance computation.

### Random Forest Demand Scorer
A `RandomForestRegressor` (50 estimators) trained on station coordinates predicts a relative demand score (20–200). This is used to rank stations of equal distance — lower-demand stations are surfaced first.

---

## Configuration

The secret key and API key are currently hardcoded in `app.py`. For production, move them to environment variables:

```bash
export SECRET_KEY="your-secret-key"
export OPENCAGE_API_KEY="your-opencage-key"
```

Then update `app.py`:
```python
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")
OPENCAGE_API_KEY = os.environ.get("OPENCAGE_API_KEY")
```

---

## Deployment

The app includes a `runtime.txt` specifying Python 3.11.9 and uses **Gunicorn** as the production WSGI server, making it ready to deploy on platforms like Render or Railway.

```bash
gunicorn app:app
```

---

## License

This project is open source. Feel free to use and adapt it.
