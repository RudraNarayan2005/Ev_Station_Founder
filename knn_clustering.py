import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import joblib
import os
import math

# ── Cluster colour palette (for map rendering) ────────────────────────────────
CLUSTER_COLORS = [
    "#00e5ff", "#39ff14", "#ff6b35", "#ff3d5a", "#b44fff",
    "#ffee00", "#00ffaa", "#ff9f43", "#54a0ff", "#1dd1a1",
    "#ffeaa7", "#fd79a8", "#a29bfe", "#00cec9", "#e17055",
]

# ── File paths for persisted models ───────────────────────────────────────────
KMEANS_MODEL_PATH  = "kmeans_model.pkl"
KNN_MODEL_PATH     = "knn_model.pkl"
CLUSTER_DATA_PATH  = "clustered_stations.pkl"


# ==============================================================================
# CORE CLASS
# ==============================================================================

class EVStationClusterer:
    """
    Encapsulates KMeans zone clustering + KNN nearest-station lookup.

    Usage
    -----
    clusterer = EVStationClusterer(df)           # df = your stations DataFrame
    clusterer.fit(n_clusters=15)                 # train both models
    result   = clusterer.find_nearest(lat, lon)  # KNN lookup
    summary  = clusterer.cluster_summary()       # zone overview
    """

    def __init__(self, df: pd.DataFrame):
        """
        Parameters
        ----------
        df : DataFrame with at least columns: lattitude, longitude, name, city, state
        """
        self.df        = df.copy().reset_index(drop=True)
        self.scaler    = StandardScaler()
        self.kmeans    = None
        self.knn       = None
        self.n_clusters = None
        self._fitted   = False

        # Validate required columns
        required = {"lattitude", "longitude"}
        missing  = required - set(df.columns)
        if missing:
            raise ValueError(f"DataFrame missing columns: {missing}")

    # ── Training ───────────────────────────────────────────────────────────────

    def fit(self, n_clusters: int = 15, n_neighbors: int = 5):
        """
        Train KMeans clustering + KNN on the station coordinates.

        Parameters
        ----------
        n_clusters  : number of geographic zones
        n_neighbors : default K for nearest-neighbour queries
        """
        self.n_clusters  = n_clusters
        self.n_neighbors = n_neighbors

        # ── 0. Drop rows with missing coordinates ─────────────────────────────
        self.df = self.df.dropna(subset=["lattitude", "longitude"]).reset_index(drop=True)
        print(f"   → {len(self.df)} stations after dropping NaN coordinates")

        coords = self.df[["lattitude", "longitude"]].values

        # ── 1. Scale coordinates for equal-weight clustering ──────────────────
        coords_scaled = self.scaler.fit_transform(coords)

        # ── 2. KMeans geographic zone clustering ──────────────────────────────
        self.kmeans = KMeans(
            n_clusters=n_clusters,
            init="k-means++",        # smarter initialisation → better clusters
            n_init=10,
            random_state=42
        )
        self.kmeans.fit(coords_scaled)

        # Attach cluster labels to the DataFrame
        self.df["cluster_id"]    = self.kmeans.labels_
        self.df["cluster_color"] = self.df["cluster_id"].apply(
            lambda c: CLUSTER_COLORS[c % len(CLUSTER_COLORS)]
        )

        # ── 3. KNN for fast nearest-station lookup ────────────────────────────
        self.knn = NearestNeighbors(
            n_neighbors=n_neighbors,
            algorithm="ball_tree",   # efficient for geo-coordinates
            metric="haversine"       # true spherical distance
        )
        # haversine expects radians
        coords_rad = np.radians(coords)
        self.knn.fit(coords_rad)

        self._fitted = True
        print(f"✅ KMeans: {n_clusters} clusters  |  KNN: k={n_neighbors}  |  "
              f"{len(self.df)} stations indexed")
        return self

    # ── KNN Lookup ─────────────────────────────────────────────────────────────

    def find_nearest(self, lat: float, lon: float, k: int = None) -> list[dict]:
        """
        Return the K nearest stations to (lat, lon).

        Parameters
        ----------
        lat, lon : user's position in decimal degrees
        k        : override default n_neighbors

        Returns
        -------
        List of dicts with station info + distance_km + cluster_id
        """
        if not self._fitted:
            raise RuntimeError("Call .fit() before find_nearest()")

        k = k or self.n_neighbors

        # haversine needs radians
        query = np.radians([[lat, lon]])
        distances, indices = self.knn.kneighbors(query, n_neighbors=k)

        results = []
        for dist_rad, idx in zip(distances[0], indices[0]):
            dist_km = dist_rad * 6371          # Earth radius in km
            row     = self.df.iloc[idx]
            results.append({
                "name"         : str(row.get("name",    "N/A")),
                "address"      : str(row.get("address", "N/A")),
                "city"         : str(row.get("city",    "N/A")),
                "state"        : str(row.get("state",   "N/A")),
                "lat"          : float(row["lattitude"]),
                "lon"          : float(row["longitude"]),
                "distance_km"  : round(dist_km, 2),
                "cluster_id"   : int(row["cluster_id"]),
                "cluster_color": str(row["cluster_color"]),
                "station_type" : str(row.get("type", "N/A")),
            })
        return results

    # ── Cluster Summary ────────────────────────────────────────────────────────

    def cluster_summary(self) -> list[dict]:
        """
        Return one summary dict per cluster zone.
        Includes centroid, station count, dominant state, and colour.
        """
        if not self._fitted:
            raise RuntimeError("Call .fit() before cluster_summary()")

        summaries = []
        for cid in range(self.n_clusters):
            group = self.df[self.df["cluster_id"] == cid]
            if group.empty:
                continue

            dominant_state = (
                group["state"].value_counts().idxmax()
                if "state" in group.columns else "N/A"
            )
            top_city = (
                group["city"].value_counts().idxmax()
                if "city" in group.columns else "N/A"
            )

            summaries.append({
                "cluster_id"     : cid,
                "color"          : CLUSTER_COLORS[cid % len(CLUSTER_COLORS)],
                "station_count"  : len(group),
                "centroid_lat"   : round(group["lattitude"].mean(), 4),
                "centroid_lon"   : round(group["longitude"].mean(), 4),
                "dominant_state" : dominant_state,
                "top_city"       : top_city,
                "avg_lat"        : round(group["lattitude"].mean(), 4),
                "avg_lon"        : round(group["longitude"].mean(), 4),
            })

        # Sort by station count descending
        summaries.sort(key=lambda x: -x["station_count"])
        return summaries

    # ── Cluster for a single point ─────────────────────────────────────────────

    def predict_cluster(self, lat: float, lon: float) -> dict:
        """
        Predict which cluster zone a given (lat, lon) falls into.
        Returns cluster info dict.
        """
        if not self._fitted:
            raise RuntimeError("Call .fit() before predict_cluster()")

        coords_scaled = self.scaler.transform([[lat, lon]])
        cid           = int(self.kmeans.predict(coords_scaled)[0])
        group         = self.df[self.df["cluster_id"] == cid]

        return {
            "cluster_id"    : cid,
            "color"         : CLUSTER_COLORS[cid % len(CLUSTER_COLORS)],
            "station_count" : len(group),
            "dominant_state": (
                group["state"].value_counts().idxmax()
                if not group.empty and "state" in group.columns else "N/A"
            ),
        }

    # ── All clustered stations (for map rendering) ─────────────────────────────

    def get_all_clustered(self) -> list[dict]:
        """Return all stations with their cluster_id and color — for map rendering."""
        if not self._fitted:
            raise RuntimeError("Call .fit() before get_all_clustered()")

        records = []
        for _, row in self.df.iterrows():
            records.append({
                "name"         : str(row.get("name",    "N/A")),
                "city"         : str(row.get("city",    "N/A")),
                "state"        : str(row.get("state",   "N/A")),
                "lat"          : float(row["lattitude"]),
                "lon"          : float(row["longitude"]),
                "cluster_id"   : int(row["cluster_id"]),
                "cluster_color": str(row["cluster_color"]),
            })
        return records

    # ── Persist / Load ─────────────────────────────────────────────────────────

    def save(self):
        """Persist trained models to disk."""
        joblib.dump(self.kmeans,   KMEANS_MODEL_PATH)
        joblib.dump(self.knn,      KNN_MODEL_PATH)
        joblib.dump(self.df,       CLUSTER_DATA_PATH)
        print(f"💾 Models saved → {KMEANS_MODEL_PATH}, {KNN_MODEL_PATH}")

    @classmethod
    def load(cls, df: pd.DataFrame) -> "EVStationClusterer":
        """Load pre-trained models from disk."""
        if not all(os.path.exists(p) for p in
                   [KMEANS_MODEL_PATH, KNN_MODEL_PATH, CLUSTER_DATA_PATH]):
            raise FileNotFoundError("Saved models not found. Run .fit() first.")

        instance        = cls.__new__(cls)
        instance.df     = joblib.load(CLUSTER_DATA_PATH)
        instance.kmeans = joblib.load(KMEANS_MODEL_PATH)
        instance.knn    = joblib.load(KNN_MODEL_PATH)
        instance.scaler = StandardScaler()

        coords = df[["lattitude", "longitude"]].values
        instance.scaler.fit(coords)         # refit scaler on same data
        instance.n_clusters  = instance.kmeans.n_clusters
        instance.n_neighbors = instance.knn.n_neighbors
        instance._fitted     = True
        print("✅ KNN/KMeans models loaded from disk")
        return instance


# ==============================================================================
# STANDALONE TEST
# ==============================================================================

if __name__ == "__main__":
    df = pd.read_csv("india_ev_charging_stations.csv")
    df.columns = df.columns.str.strip()
    df["lattitude"] = df["lattitude"].astype(str).str.replace(",","").astype(float)
    df["longitude"] = df["longitude"].astype(str).str.replace(",","").astype(float)

    clusterer = EVStationClusterer(df)
    clusterer.fit(n_clusters=15, n_neighbors=5)
    clusterer.save()

    # Test: nearest stations to Bengaluru
    print("\n📍 5 Nearest to Bengaluru (12.97, 77.59):")
    for s in clusterer.find_nearest(12.97, 77.59, k=5):
        print(f"  {s['name']} | {s['city']} | {s['distance_km']} km | Cluster {s['cluster_id']}")

    print("\n📊 Cluster Summary:")
    for c in clusterer.cluster_summary()[:5]:
        print(f"  Cluster {c['cluster_id']}: {c['station_count']} stations | "
              f"{c['dominant_state']} | centroid ({c['centroid_lat']}, {c['centroid_lon']})")
