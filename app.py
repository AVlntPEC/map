from flask import Flask, render_template, request, jsonify
import requests
import folium
import json

app = Flask(__name__)

# Define block coordinates with lowercase keys
block_coordinates = {
    "admin block": (13.04926, 80.07527),
    "mess block": (13.05091, 80.07445),
    "cse block 3": (13.05042, 80.07534),
    "eee block": (13.05083, 80.07679),
    "csbs block": (13.05173, 80.07600),
    "cse block 1": (13.04969, 80.07531),
    "cse block 2": (13.05003, 80.07518),
    "boys hostel": (13.04985, 80.07475),
    "girls hostel": (13.05164, 80.07706),
    "idea lab": (13.05083, 80.07666),
    "lab block 1": (13.04948, 80.07608),
    "lab block 2": (13.05014, 80.07625),
    "lab block 3": (13.05086, 80.07629),
    "ece block 1": (13.05092, 80.07528),
    "ece block 2": (13.05125, 80.07535),
    "aids block": (13.04980, 80.07643),
    "coe block": (13.05100, 80.07648)
}

def get_route(start_coord, end_coord):
    service_url = 'https://router.project-osrm.org/route/v1/driving/'
    start = f"{start_coord[1]},{start_coord[0]}"
    end = f"{end_coord[1]},{end_coord[0]}"
    url = f"{service_url}{start};{end}?overview=full&geometries=geojson&alternatives=true"
    
    response = requests.get(url)
    data = response.json()

    if 'routes' in data and data['routes']:
        routes = data['routes']
        route_data = []
        for route in routes:
            if 'geometry' in route:
                route_info = {
                    'geometry': route['geometry'],
                    'distance': route['distance'],
                    'duration': route['duration']
                }
                route_data.append(route_info)
        return route_data
    else:
        return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/route', methods=['POST'])
def route():
    start_block = request.form.get('startBlock', '').lower()
    end_block = request.form.get('endBlock', '').lower()
    
    if not end_block or end_block not in block_coordinates:
        return jsonify({"error": "Invalid end block name"}), 400

    if start_block == "my location":
        user_location = request.form.get('userLocation')
        if user_location:
            start_coord = tuple(map(float, user_location.split(',')))
        else:
            return jsonify({"error": "User location not provided"}), 400
    elif start_block in block_coordinates:
        start_coord = block_coordinates[start_block]
    else:
        return jsonify({"error": "Invalid start block name"}), 400

    end_coord = block_coordinates[end_block]
    
    routes = get_route(start_coord, end_coord)
    
    if routes:
        # Create a map with the route
        m = folium.Map(location=[(start_coord[0] + end_coord[0]) / 2, (start_coord[1] + end_coord[1]) / 2], zoom_start=15)
        folium.Marker(start_coord, tooltip='Start').add_to(m)
        folium.Marker(end_coord, tooltip='End').add_to(m)
        
        main_route = routes[0]
        alternative_routes = routes[1:]
        
        # Add main route in blue
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in main_route['geometry']['coordinates']],
            color='blue',
            weight=2.5,
            opacity=0.8
        ).add_to(m)
        
        # Add alternative routes in dark gray
        for route in alternative_routes:
            folium.PolyLine(
                locations=[(lat, lon) for lon, lat in route['geometry']['coordinates']],
                color='darkgray',
                weight=2.5,
                opacity=0.8
            ).add_to(m)
        
        # Adding distance and duration information
        distance_km = main_route['distance'] / 1000
        duration_min = main_route['duration'] / 60
        folium.Marker(
            location=[(start_coord[0] + end_coord[0]) / 2, (start_coord[1] + end_coord[1]) / 2],
            icon=folium.DivIcon(html=f'<div><b>Distance:</b> {distance_km:.2f} km<br><b>Duration:</b> {duration_min:.2f} min</div>')
        ).add_to(m)
        
        # Save the map to an HTML file
        map_html = m._repr_html_()
        return jsonify({"map": map_html})
    
    return jsonify({"error": "Route not found"}), 404


if __name__ == '__main__':
    app.run(debug=True)
