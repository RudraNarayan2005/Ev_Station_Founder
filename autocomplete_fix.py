# ==============================
# AUTOCOMPLETE — OpenCage API
# GET /autocomplete?q=bhubaneswar&lat=20.29&lon=85.82
# Returns [{display_name, full_address, lat, lon}, ...]
# ==============================

@app.route('/autocomplete')
def autocomplete():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])

    # Optional proximity bias passed from the JS frontend
    try:
        prox_lat = float(request.args.get('lat', 20.5937))  # default: centre of India
        prox_lon = float(request.args.get('lon', 78.9629))
    except (TypeError, ValueError):
        prox_lat, prox_lon = 20.5937, 78.9629

    try:
        resp = http_requests.get(
            'https://api.opencagedata.com/geocode/v1/json',
            params={
                'q':              query,
                'key':            OPENCAGE_API_KEY,
                'limit':          6,
                'language':       'en',
                'countrycode':    'in',
                'proximity':      f'{prox_lat},{prox_lon}',   # ← now actually sent
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
