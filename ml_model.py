import joblib
import datetime

model = joblib.load("demand_model.pkl")

def predict_demand(station_id):

    now = datetime.datetime.now()
    hour = now.hour
    day = now.weekday()

    demand = model.predict([[station_id, hour, day]])

    return float(demand[0])