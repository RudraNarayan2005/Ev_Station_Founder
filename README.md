# ⚡ EV Station Finder

A smart **Electric Vehicle Charging Station Finder** web application built with **Python (Flask)** and **Machine Learning**. It helps EV users in India locate the nearest charging stations using KNN-based clustering and a trained ML model.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Training the Model](#training-the-model)
  - [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [Dataset](#dataset)
- [Contributing](#contributing)
- [License](#license)

---

## 📖 About the Project

With the rapid growth of electric vehicles in India, finding a nearby charging station remains a challenge. **EV Station Finder** solves this by allowing users to enter their location and instantly discover the closest EV charging stations — powered by a KNN-based machine learning model trained on real India EV station data.

---

## ✨ Features

- 📍 Find nearest EV charging stations based on user location
- 🤖 ML-powered recommendations using K-Nearest Neighbors (KNN) clustering
- 🗺️ India-wide EV station dataset (`india_ev_charging_stations.csv`)
- 👤 User authentication (register/login) with SQLite database
- 🌐 Clean web interface built with HTML, CSS & Flask templates
- 🔌 Easily extensible with new station routes

---

## 🛠 Tech Stack

| Layer         | Technology                        |
|---------------|-----------------------------------|
| Backend       | Python, Flask                     |
| ML / AI       | Scikit-learn, KNN Clustering      |
| Database      | SQLite (`users.db`)               |
| Frontend      | HTML5, CSS3 (Jinja2 Templates)    |
| Dataset       | India EV Charging Stations CSV    |
| Data Handling | Pandas, NumPy                     |

---

## 📁 Project Structure

```
Ev_Station_Founder/
├── static/                        # CSS, JS, and static assets
├── templates/                     # HTML templates (Jinja2)
├── app.py                         # Main Flask application
├── database.py                    # Database setup and user management
├── ml_model.py                    # ML model definition and prediction logic
├── knn_clustering.py              # KNN clustering implementation
├── train_model.py                 # Script to train and save the ML model
├── new_routes_to_add.py           # Utility for adding new station routes
├── india_ev_charging_stations.csv # Dataset of EV stations across India
├── users.db                       # SQLite database for user accounts
├── requirements.txt               # Python dependencies
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/RudraNarayan2005/Ev_Station_Founder.git

# Navigate into the project directory
cd Ev_Station_Founder

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate      # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Training the Model

Before running the app for the first time, train the ML model:

```bash
python train_model.py
```

### Running the Application

```bash
python app.py
```

The app will be available at `http://localhost:5000`.

---

## 🧠 How It Works

1. **Data** — The app uses `india_ev_charging_stations.csv`, which contains station names, locations (latitude/longitude), charger types, and availability.
2. **Model Training** — `train_model.py` processes the dataset and trains a KNN model using geographic coordinates to cluster stations.
3. **Prediction** — When a user submits their location, `ml_model.py` queries the KNN model to return the *k* nearest charging stations.
4. **Auth** — Users can register and log in via `database.py`, which manages a local SQLite database.
5. **Web UI** — Flask serves HTML templates from the `templates/` folder for a seamless user experience.

---

## 📊 Dataset

The project uses `india_ev_charging_stations.csv`, a dataset of EV charging stations across India. It includes:

| Column        | Description                     |
|---------------|---------------------------------|
| Station Name  | Name of the charging station    |
| City / State  | Location details                |
| Latitude      | Geographic latitude             |
| Longitude     | Geographic longitude            |
| Charger Type  | AC / DC / Fast Charger          |
| Availability  | Operational status              |

*You can expand the dataset by adding new entries or using `new_routes_to_add.py`.*

---

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add your feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

> Made with ⚡ by [RudraNarayan2005](https://github.com/RudraNarayan2005)
