# trip_planner_app.py
from flask import Flask, render_template, request, url_for, send_from_directory
import os
import math
import folium
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta
import requests
from folium.plugins import AntPath
from geopy.distance import geodesic
# ===============================
# OpenRouteService API Key
# ===============================
from dotenv import load_dotenv

load_dotenv()
# ===============================
# OpenRouteService API Key
# ===============================
ORS_API_KEY = os.getenv("ORS_API_KEY")

# PDF imports
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# ===============================================================
# 1️⃣ PROJECT PATHS & APP CONFIG
# ===============================================================
project_root = os.path.dirname(os.path.abspath(__file__))
# templates_dir = os.path.join(project_root, "templates") # REMOVED: Now using root as template folder
static_dir = os.path.join(project_root, "static")

app = Flask(
    __name__,
    template_folder=project_root, # CHANGED: Look for templates in root (index.html is here)
    static_folder=static_dir
)


# ===============================================================
# 2️⃣ OSRM ROUTING FUNCTION (REAL ROAD ROUTES) - single segment helper
# ===============================================================
def osrm_route(lat1, lon1, lat2, lon2):

    # 🚫 Prevent impossible routes (too far)
    if geodesic((lat1, lon1), (lat2, lon2)).km > 3000:
        print("❌ Too far for OSRM routing, skipping...")
        return None, None

# ===============================================================
# ORS MULTI-STOP ROUTING (MAP ONLY)
# ===============================================================
def ors_segment(start, end, profile="driving-car"):
    url = f"https://api.openrouteservice.org/v2/directions/{profile}/geojson"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    body = {
        "coordinates": [
            [start["lng"], start["lat"]],
            [end["lng"], end["lat"]]
        ],
        "instructions": False
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    except:
        return None


def ors_multistop_route(start, points):
    url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

    headers = {
        "Authorization": ORS_API_KEY,
        "Content-Type": "application/json"
    }

    coords = [[start[1], start[0]]]  # [lon, lat]
    for p in points:
        coords.append([p['lng'], p['lat']])

    body = {
        "coordinates": coords,
        "instructions": False
    }

    try:
        r = requests.post(url, json=body, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("ORS ERROR:", e)
        return None




# ===============================================================
# 3️⃣ PDF GENERATION (NO CHANGE)
# ===============================================================
def generate_trip_pdf(selected_df, total_trip_days, total_trip_hours, trip_date, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Heading1'],
        fontSize=24, textColor=colors.HexColor('#4c1d95'),
        alignment=1, spaceAfter=20
    )

    subtitle_style = ParagraphStyle(
        'Subtitle', parent=styles['Heading2'],
        fontSize=14, textColor=colors.HexColor('#6b21a8'),
        alignment=1, spaceAfter=16
    )

    heading_style = ParagraphStyle(
        'SectionHeading', parent=styles['Heading2'],
        fontSize=16, textColor=colors.HexColor('#1d4ed8'),
        spaceBefore=12, spaceAfter=8
    )

    elements.append(Paragraph("Trip Itinerary", title_style))
    elements.append(Paragraph("Powered by Geo Intel Lab", subtitle_style))
    elements.append(Spacer(1, 0.2 * inch))

    summary_data = [
        ["Total Days", str(total_trip_days)],
        ["Total Hour", f"{total_trip_hours:.2f}"],
        ["Trip Start Date", trip_date or "Not provided"],
        ["Total Places", str(len(selected_df))]
    ]

    summary_table = Table(summary_data, colWidths=[2 * inch, 4 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e5e7eb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#111827')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#4b5563')),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    elements.append(Paragraph("Selected Places", heading_style))

    for idx, row in selected_df.iterrows():
        name = str(row.get('name of the place', 'Unknown'))
        category = row.get('category', 'N/A')
        vstart, vend = row.get('visit_start', ''), row.get('visit_end', '')
        time_str = f"{vstart} - {vend}" if vstart and vend else "N/A"
        spend = str(row.get('spend_time_minutes', "N/A"))
        try:
            dist = float(row.get('distance_from_previous_km', 0.0))
        except:
            dist = 0.0
        desc = str(row.get('description', 'No description')).replace('\n', ' ')

        place_title = Paragraph(f"{idx+1}. {name}",
                                ParagraphStyle('PlaceTitle',
                                               parent=styles['Heading3'],
                                               fontSize=13,
                                               textColor=colors.HexColor('#7c2d12')))
        elements.append(place_title)

        place_table = Table([
            ["Name", name],
            ["Category", category],
            ["Time", time_str],
            ["Spend", f"{spend} minutes"],
            ["Distance", f"{dist:.2f} km"],
            ["Description", desc],
        ], colWidths=[2.5 * inch, 3.8 * inch])

        place_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fee2e2')),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#f9fafb')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#f97316')),
        ]))

        elements.append(place_table)
        elements.append(Spacer(1, 0.18 * inch))

    doc.build(elements)


# ===============================================================
# HOME ROUTES (NO CHANGE)
# ===============================================================
@app.route('/')
@app.route('/index.html')
def info():
    return render_template('index.html') # CORRECTED: Landing page

@app.route('/plan')
@app.route('/plan.html')
def plan_home():
    return render_template('plan.html')

# NEW ROUTE TO SERVE MAP FROM ROOT
@app.route('/trip_plan_map.html')
def serve_map():
    return send_from_directory(project_root, 'trip_plan_map.html')

# ===============================================================
# 5️⃣ TRIP PLANNING LOGIC (NO CHANGES EXCEPT USING OSRM)
# ===============================================================
def calculate_trip_plan(df, start_lat, start_lon, start_time, end_time, num_days):
    try:
        user_start = datetime.strptime(start_time, "%H:%M")
        user_end = datetime.strptime(end_time, "%H:%M")
    except:
        return pd.DataFrame(), 0, 0, []

    if user_end <= user_start:
        user_end += timedelta(days=1)

    hours_per_day = (user_end - user_start).total_seconds() / 3600.0
    total_trip_hours = hours_per_day * max(1, int(num_days))

    if hours_per_day < 0.5:
        return pd.DataFrame(), total_trip_hours, hours_per_day, []

    def parse_hhmm(val):
        try:
            return datetime.strptime(str(val), "%H:%M").time()
        except:
            return None

    def to_min(t):
        return t.hour * 60 + t.minute

    start_time_obj = user_start.time()

    # FILTER BY OPEN HOURS
    def is_open(row):
        open_t = parse_hhmm(row.get("visit_start"))
        close_t = parse_hhmm(row.get("visit_end"))
        if open_t is None or close_t is None:
            return True

        user_start_min = to_min(start_time_obj)
        user_end_min = user_start_min + int(hours_per_day * 60)

        place_open_min = to_min(open_t)
        place_close_min = to_min(close_t)
        if place_close_min <= place_open_min:
            place_close_min += 24 * 60
        if user_end_min <= user_start_min:
            user_end_min += 24 * 60

        return max(user_start_min, place_open_min) < min(user_end_min, place_close_min)

    try:
        open_places = df[df.apply(is_open, axis=1)].copy()
    except:
        open_places = df.copy()

    if open_places.empty:
        return pd.DataFrame(), total_trip_hours, hours_per_day, []

    # SORT BY APPROX DISTANCE
    def quick_dist(a, b, c, d):
        try:
            return ((a - c) ** 2 + (b - d) ** 2) ** 0.5
        except:
            return 999999

    open_places["approx_dist"] = open_places.apply(
        lambda r: quick_dist(start_lat, start_lon, r["latitude"], r["longitude"]), axis=1
    )
    open_places = open_places.sort_values("approx_dist")

    remaining_minutes = total_trip_hours * 60
    avg_speed = 25

    current_lat, current_lon = start_lat, start_lon

    selected = []
    geoms = []
    dists = []

    for _, row in open_places.iterrows():
        lat2 = float(row["latitude"])
        lon2 = float(row["longitude"])

        result = osrm_route(current_lat, current_lon, lat2, lon2)

        if result:
            dist_km, geom = result
        else:
            approx = quick_dist(current_lat, current_lon, lat2, lon2)
            dist_km = approx * 111
            geom = None


        # Adjust speed for highway travel if distance is far
        speed = 70 if dist_km > 50 else 25
        travel_min = (dist_km / speed) * 60
        spend_min = float(row.get("spend_time_minutes", 30))

        if remaining_minutes < (travel_min + spend_min):
            continue

        selected.append(row.to_dict())
        geoms.append(geom)
        dists.append(round(dist_km, 2))

        remaining_minutes -= (travel_min + spend_min)
        current_lat, current_lon = lat2, lon2

    if not selected:
        return pd.DataFrame(), total_trip_hours, hours_per_day, []

    df_sel = pd.DataFrame(selected)
    df_sel["distance_from_previous_km"] = dists
    df_sel.reset_index(drop=True, inplace=True)

    return df_sel, total_trip_hours, hours_per_day, geoms


# ===============================================================
# PLAN TRIP ROUTE
# ===============================================================
@app.route('/plan_trip', methods=['GET', 'POST'])
def plan_trip():
    if request.method == "GET":
        return render_template("index.html")

    try:
        start_lat = float(request.form.get('start_lat', 0.0))
        start_lon = float(request.form.get('start_lon', 0.0))
    except:
        return render_template("result.html", # CORRECTED: File is in root
                               message="Invalid location data. Check GPS or manual location.")

    start_time = request.form.get('start_time', '')
    end_time = request.form.get('end_time', '')
    num_days = int(request.form.get('num_days', 1))
    trip_date = request.form.get('trip_date', '')

    if not start_time or not end_time:
        return render_template("result.html", message="Start & End times required.") # CORRECTED

    csv_path = os.path.join(project_root, "tirupati_places_final_updated.csv")
    if not os.path.exists(csv_path):
        return render_template("result.html", message="Places database missing.") # CORRECTED

    df = pd.read_csv(csv_path)
    if df.empty:
        return render_template("result.html", message="Places CSV empty.") # CORRECTED

    selected_df, total_trip_hours, hours_per_day, geoms = calculate_trip_plan(
        df, start_lat, start_lon, start_time, end_time, num_days
    )

    if selected_df.empty:
        return render_template("result.html", # CORRECTED
                               message="No places found. Increase time or choose nearer locations.",
                               places=[])

    # GENERATE PDF
    pdf_path = os.path.join(static_dir, "trip_itinerary.pdf")
    generate_trip_pdf(selected_df, num_days, total_trip_hours, trip_date, pdf_path)
    pdf_url = url_for("static", filename="trip_itinerary.pdf")

    # ===============================================================
    # F. LEAFLET MAP — ONLY OSRM ROAD ROUTES (NO STRAIGHT LINES)
    # ===============================================================
    try:
        map_obj = folium.Map(location=[start_lat, start_lon], zoom_start=13)

        # HOME MARKER (exact original design)
        home_popup = folium.Popup(
            "<b>Your Location</b><br>Trip Starting Point",
            max_width=300
        )

        folium.Marker(
            [start_lat, start_lon],
            popup=home_popup,
            icon=folium.Icon(color="blue", icon="home")
        ).add_to(map_obj)

        # We'll collect the places into a list for a combined OSRM call
        places_list = []

        # Add markers (exact original popup design) and build places_list
        for idx, row in selected_df.iterrows():
            place_lat = row["latitude"]
            place_lon = row["longitude"]
            name = row["name of the place"]
            cat = row.get("category", "")
            vst = row.get("visit_start", "")
            ven = row.get("visit_end", "")
            spend = row.get("spend_time_minutes", "")
            dist_prev = row.get("distance_from_previous_km", 0.0)
            desc = row.get("description", "")

            popup_html = f"""
                <div style='width:320px; font-family:"Segoe UI", sans-serif; padding:5px;'>
                    <div style='border-bottom: 2px solid #ec4899; margin-bottom: 10px; padding-bottom: 5px;'>
                        <h3 style='margin:0; color:#831843; font-size:16px;'>{name}</h3>
                    </div>

                    <table style='width:100%; border-collapse:collapse; font-size:13px;'>
                        <tr style='border-bottom: 1px solid #fce7f3;'>
                            <td style='padding:6px 0; color:#9d174d; font-weight:600; vertical-align:top; width:90px;'>Category</td>
                            <td style='padding:6px 0; color:#374151;'>{cat}</td>
                        </tr>
                        <tr style='border-bottom: 1px solid #fce7f3;'>
                            <td style='padding:6px 0; color:#9d174d; font-weight:600; vertical-align:top;'>Visit</td>
                            <td style='padding:6px 0; color:#374151;'>{vst} - {ven}</td>
                        </tr>
                        <tr style='border-bottom: 1px solid #fce7f3;'>
                            <td style='padding:6px 0; color:#9d174d; font-weight:600; vertical-align:top;'>Spend</td>
                            <td style='padding:6px 0; color:#374151;'>{spend} mins</td>
                        </tr>
                        <tr style='border-bottom: 1px solid #fce7f3;'>
                            <td style='padding:6px 0; color:#9d174d; font-weight:600; vertical-align:top;'>Distance</td>
                            <td style='padding:6px 0; color:#374151;'>{dist_prev:.2f} km</td>
                        </tr>
                        <tr>
                            <td style='padding:8px 0; color:#9d174d; font-weight:600; vertical-align:top;'>Description</td>
                            <td style='padding:8px 0; color:#4b5563; line-height:1.4;'>{desc}</td>
                        </tr>
                    </table>
                </div>
            """

            folium.Marker(
                [place_lat, place_lon],
                popup=popup_html,
                icon=folium.Icon(color="pink", icon="info-sign")
            ).add_to(map_obj)

            # append to places_list in the format needed
            places_list.append({"lat": float(place_lat), "lng": float(place_lon)})

        # Use the order from the itinerary (selected_df) directly
        sorted_places = places_list


        # =========================================================
        # ROBUST SEGMENT-BASED ROUTING (NEVER BREAKS ROUTE)
        # =========================================================

        # =========================
        # ROUTING WITH PROFILE FALLBACK
        # =========================

        all_route_coords = []

        points = [{"lat": start_lat, "lng": start_lon}] + sorted_places

        for i in range(len(points) - 1):
            src = points[i]
            dst = points[i + 1]

            # Try DRIVING first
            seg = ors_segment(src, dst, profile="driving-car")

            # If driving fails, try WALKING
            if not seg or "features" not in seg:
                print("Driving failed, switching to walking:", dst)
                seg = ors_segment(src, dst, profile="foot-walking")

            # If walking also fails → SKIP (no straight line)
            if not seg or "features" not in seg:
                print("Unroutable even for walking:", dst)
                continue

            coords = [(c[1], c[0]) for c in seg["features"][0]["geometry"]["coordinates"]]

            if all_route_coords:
                coords = coords[1:]

            all_route_coords.extend(coords)


        # Draw route (PURE ROAD / PATH ONLY)
        AntPath(
            locations=all_route_coords,
            color="#2563eb",
            pulseColor="#ec4899",
            weight=6,
            opacity=0.9,
            delay=800
        ).add_to(map_obj)



        # ---------------------------------------------------------------
        # INJECT CUSTOM HTML/CSS/JS FOR BACK BUTTON ONLY
        # ---------------------------------------------------------------
        custom_map_code = """
        <style>
            /* Back Button Styling */
            .back-btn-map {
                position: fixed;
                bottom: 20px;
                left: 20px;
                z-index: 9999;
                background: linear-gradient(135deg, #6366f1, #4f46e5);
                color: white;
                border: none;
                padding: 12px 24px;
                font-size: 16px;
                font-family: 'Segoe UI', sans-serif;
                font-weight: 600;
                cursor: pointer;
                border-radius: 50px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .back-btn-map:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(0,0,0,0.4);
            }
        </style>

        <!-- Back Button -->
        <button class="back-btn-map" onclick="history.back()">&#8592; Back</button>

        <script>
            document.addEventListener("DOMContentLoaded", function() {
                var attempt = 0;
                var maxAttempts = 20; // Try for 10 seconds
                
                var checkMap = setInterval(function() {
                    attempt++;
                    
                    // Locate the Leaflet map object globally
                    var mapName = Object.keys(window).find(k => k.startsWith("map_"));
                    var map = window[mapName];

                    if (map && map.eachLayer) {
                        clearInterval(checkMap);
                        console.log("Map object found:", mapName);

                        map.eachLayer(function(layer) {
                            if (layer instanceof L.Marker) {
                                if (layer.options && layer.options.icon && layer.options.icon.options) {
                                    var opts = layer.options.icon.options;
                                    
                                    // Target info-sign markers
                                    if (opts.icon === 'info-sign') {
                                        layer.on('click', function(e) {
                                            var currentIcon = this.getIcon();
                                            var curColor = currentIcon.options.markerColor;
                                            var newColor = (curColor === 'pink') ? 'blue' : 'pink';

                                            var newIcon = L.AwesomeMarkers.icon({
                                                icon: 'info-sign',
                                                markerColor: newColor,
                                                prefix: 'glyphicon',
                                                iconColor: 'white'
                                            });
                                            this.setIcon(newIcon);
                                            this.openPopup();
                                        });
                                    }
                                }
                            }
                        });
                    } else {
                        if (attempt >= maxAttempts) {
                            clearInterval(checkMap);
                            console.error("Leaflet map object not found after retries.");
                        }
                    }
                }, 500); // Check every 500ms
            });
        </script>
        """
        map_obj.get_root().html.add_child(folium.Element(custom_map_code))

        # SAVE MAP
        html_path = os.path.join(project_root, "trip_plan_map.html") # CHANGED: Save to root
        map_obj.save(html_path)
        map_url = "/trip_plan_map.html" # CHANGED: Point to new route

    except Exception as e:
        print("MAP ERROR:", e)
        map_url = ""

    # GOOGLE MAPS MULTISTOP URL
    google_maps_url = ""
    try:
        if len(selected_df) > 0:
            origin = f"{start_lat},{start_lon}"
            dest_lat = selected_df.iloc[-1]["latitude"]
            dest_lon = selected_df.iloc[-1]["longitude"]

            waypoints = "|".join(
                f"{selected_df.iloc[i]['latitude']},{selected_df.iloc[i]['longitude']}"
                for i in range(len(selected_df) - 1)
            )

            google_maps_url = (
                f"https://www.google.com/maps/dir/?api=1"
                f"&origin={origin}"
                f"&destination={dest_lat},{dest_lon}"
                f"{'&waypoints=' + waypoints if waypoints else ''}"
                f"&travelmode=driving"
            )
    except:
        google_maps_url = ""

    return render_template(
        "result.html", # CORRECTED: File is in root
        map_url=map_url,
        pdf_url=pdf_url,
        google_maps_url=google_maps_url,
        places_selected=len(selected_df),
        places=selected_df.to_dict("records"),
        total_trip_days=num_days,
        total_trip_hours=round(total_trip_hours, 2),
        hours_per_day=round(hours_per_day, 2),
        trip_date=trip_date
    )


# ===============================================================
# RUN APP
# ===============================================================
if __name__ == "__main__":
    app.run(debug=True)
