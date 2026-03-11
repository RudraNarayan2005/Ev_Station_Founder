import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load your dataset
data = pd.read_csv("india_ev_charging_stations.csv")

# Create station_id
data["station_id"] = range(1, len(data)+1)

# Generate synthetic time data
data["hour"] = np.random.randint(0,24,size=len(data))
data["day"] = np.random.randint(0,7,size=len(data))

# Generate synthetic demand
data["demand"] = np.random.randint(1,50,size=len(data))

# Training data
X = data[['station_id','hour','day']]
y = data['demand']

model = RandomForestRegressor()
model.fit(X,y)

joblib.dump(model,"demand_model.pkl")

print("Model trained successfully")