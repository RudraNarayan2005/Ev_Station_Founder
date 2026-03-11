# ============================================================
# HOW TO INTEGRATE knn_clustering.py INTO YOUR app.py
# ============================================================
# Step 1: Copy knn_clustering.py into your project folder.
#
# Step 2: Add this import at the TOP of app.py (after existing imports):
#
#     from knn_clustering import EVStationClusterer
#
# Step 3: After your existing `train_demand_model()` call, add this block:
#
#     clusterer = None
#     def init_clusterer():
#         global clusterer
#         if not df.empty:
#             clusterer = EVStationClusterer(df)
#             clusterer.fit(n_clusters=15, n_neighbors=5)
#     init_clusterer()
#
# Step 4: Paste the two routes below into app.py.
#         They are completely self-contained — zero changes to existing routes.
# ============================================================


# ==============================
# ROUTE 1: KNN NEAREST STATIONS (API-style)
# GET  /knn?lat=12.97&lon=77.59&k=5
# Returns JSON list of K nearest stations with cluster info.
# Use this to power a "Find Nearest" AJAX button on your frontend.
# ==============================

@app.route('/knn')
def knn_nearest():
    """
    Returns K nearest stations to the given coordinates as JSON.
    Also returns the user's cluster zone info.

    Query params:
        lat  (float) : user latitude
        lon  (float) : user longitude
        k    (int)   : number of results (default 5, max 20)
    """
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
        "user_cluster" : user_cluster,
        "nearest"      : nearest,
        "count"        : len(nearest),
    }


# ==============================
# ROUTE 2: CLUSTER MAP PAGE
# GET  /cluster-map
# Renders a full-page Leaflet map with all stations colour-coded by cluster.
# Each cluster zone gets a summary popup at its centroid.
# ==============================

@app.route('/cluster-map')
def cluster_map():
    """
    Full-page interactive cluster map.
    - Every station is plotted, colour-coded by its KMeans cluster zone.
    - Cluster centroids show a summary popup (zone name, station count, top state).
    - Requires: templates/cluster_map.html  (see cluster_map_template.html)
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if clusterer is None:
        flash("Clustering model not ready.", "error")
        return redirect(url_for('dashboard'))

    import json as _json

    stations_data = clusterer.get_all_clustered()
    cluster_data  = clusterer.cluster_summary()

    return render_template(
        "cluster_map.html",
        username        = session['username'],
        stations_json   = _json.dumps(stations_data),
        clusters_json   = _json.dumps(cluster_data),
        total_stations  = len(stations_data),
        total_clusters  = len(cluster_data),
    )


# ==============================
# ENHANCED RESULT ROUTE PATCH
# ==============================
# In your EXISTING /result route, after building `nearby_stations`,
# add this block to also attach KNN cluster info to each result:
#
#   if clusterer is not None:
#       knn_results = clusterer.find_nearest(user_lat, user_lon, k=10)
#       knn_lookup  = {(r['lat'], r['lon']): r for r in knn_results}
#       for s in nearby_stations:
#           key = (s['lat'], s['lon'])
#           knn_data = knn_lookup.get(key, {})
#           s['cluster_id']    = knn_data.get('cluster_id', -1)
#           s['cluster_color'] = knn_data.get('cluster_color', '#888888')
#
# Then in result.html you can colour-code markers by cluster_color.
