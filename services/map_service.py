"""
Map Service
-----------
Generates interactive Folium maps showing vehicle locations,
destinations, and selected routes for the Streamlit dashboard.
"""

import folium
from folium import plugins
from typing import List, Dict, Any, Optional


# Color scheme for vehicle status
STATUS_COLORS = {
    "available": "#00D4AA",      # Teal green
    "on_delivery": "#F59E0B",    # Amber
    "maintenance": "#EF4444",    # Red
}

VEHICLE_TYPE_ICONS = {
    "truck": "🚛",
    "van": "🚐",
    "mini_truck": "🚚",
}


def create_fleet_map(
    vehicles: List[Dict],
    destination: Optional[Dict] = None,
    selected_vehicle: Optional[Dict] = None,
    selected_route: Optional[Dict] = None,
    zoom_start: int = 11,
    custom_source: Optional[Dict] = None,
) -> folium.Map:
    """
    Create an enterprise-style dark-themed fleet map.

    Args:
        vehicles: List of vehicle dicts from fleet_data.json
        destination: Dict with lat, lon, name for the delivery destination
        selected_vehicle: The recommended vehicle (gets highlighted differently)
        selected_route: The active OSRM route details (holds geometry coordinates)
        zoom_start: Initial zoom level

    Returns:
        A configured folium.Map object
    """
    # Dynamic map centering based on query targets
    if custom_source and destination:
        center_lat = (custom_source["lat"] + destination["lat"]) / 2
        center_lon = (custom_source["lon"] + destination["lon"]) / 2
        from tools.here_routing import haversine_distance
        dist = haversine_distance(custom_source["lat"], custom_source["lon"], destination["lat"], destination["lon"])
        if dist > 200:
            zoom_start = 7
        elif dist > 100:
            zoom_start = 8
        elif dist > 50:
            zoom_start = 9
        else:
            zoom_start = 10
    elif destination:
        center_lat = destination["lat"]
        center_lon = destination["lon"]
    else:
        center_lat = 28.6139
        center_lon = 77.2090

    # Use dark tiles for enterprise look — attribution hidden for clean UI
    fleet_map = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter",
        control_scale=False,
        prefer_canvas=True,
        attr=" ",
    )
    # Inject CSS to hide Leaflet branding and attribution
    hide_attr_css = """
    <style>
    .leaflet-control-attribution { display: none !important; }
    .leaflet-control-zoom { border: 1px solid #30363d !important; border-radius: 4px !important; }
    .leaflet-control-zoom a {
        background: #161b22 !important;
        color: #8b949e !important;
        border-color: #30363d !important;
        font-size: 16px !important;
        line-height: 26px !important;
    }
    .leaflet-control-zoom a:hover { background: #21262d !important; color: #c9d1d9 !important; }
    </style>
    """
    fleet_map.get_root().html.add_child(folium.Element(hide_attr_css))

    # Add vehicle markers
    for vehicle in vehicles:
        is_selected = (
            selected_vehicle is not None
            and vehicle["vehicle_id"] == selected_vehicle.get("vehicle_id")
        )

        _add_vehicle_marker(fleet_map, vehicle, is_selected)

    # Add origin marker for custom point-to-point queries
    if custom_source:
        _add_origin_marker(fleet_map, custom_source)

    # Add destination marker (offset slightly if overlapping with the selected vehicle so both markers remain visible)
    if destination:
        dest_lat = destination.get("lat")
        dest_lon = destination.get("lon")
        if selected_vehicle:
            # If coordinates match within ~20 meters
            if abs(dest_lat - selected_vehicle["latitude"]) < 0.0002 and abs(dest_lon - selected_vehicle["longitude"]) < 0.0002:
                dest_lat += 0.0005
                dest_lon += 0.0005
        _add_destination_marker(fleet_map, {"lat": dest_lat, "lon": dest_lon, "name": destination.get("name")})

    # Draw route line: use selected_vehicle as origin if available,
    # or fall back to geometry_coordinates in selected_route (traffic-only queries)
    if selected_vehicle and destination:
        _add_route_line(fleet_map, selected_vehicle, destination, selected_route)
    elif destination and selected_route and selected_route.get("geometry_coordinates"):
        # Traffic-only query: draw road from geometry without highlighting a vehicle
        _add_route_line_from_geometry(fleet_map, selected_route)

    # Add legend
    _add_legend(fleet_map)

    # Add fullscreen button
    plugins.Fullscreen(position="topright").add_to(fleet_map)

    return fleet_map


def _add_vehicle_marker(
    fleet_map: folium.Map, vehicle: Dict, is_selected: bool = False
):
    """Add a styled vehicle marker to the map."""
    status = vehicle.get("status", "available")
    color = STATUS_COLORS.get(status, "#6B7280")
    v_type = vehicle.get("vehicle_type", "truck")
    icon_emoji = VEHICLE_TYPE_ICONS.get(v_type, "🚗")

    # Selected vehicle gets a larger, pulsing marker
    if is_selected:
        icon_color = "green"
        icon_name = "star"
        popup_bg = "#064E3B"
        border_style = "border: 2px solid #00D4AA;"
    else:
        icon_color = (
            "blue" if status == "available"
            else "orange" if status == "on_delivery"
            else "red"
        )
        icon_name = "truck"
        popup_bg = "#1E293B"
        border_style = ""

    popup_html = f"""
    <div style="
        background: {popup_bg};
        color: #E2E8F0;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        min-width: 200px;
        {border_style}
    ">
        <div style="font-size: 16px; font-weight: 700; margin-bottom: 8px;">
            {icon_emoji} {vehicle['vehicle_id']}
            {"⭐ SELECTED" if is_selected else ""}
        </div>
        <div style="font-size: 12px; color: #94A3B8;">
            <b>Driver:</b> {vehicle['driver_name']}<br>
            <b>Location:</b> {vehicle['location_name']}<br>
            <b>Status:</b> <span style="color: {color};">{vehicle['status'].replace('_', ' ').title()}</span><br>
            <b>Fuel:</b> {vehicle['fuel_level']}%<br>
            <b>Type:</b> {vehicle['vehicle_type'].replace('_', ' ').title()}<br>
            <b>Capacity:</b> {vehicle['capacity_tons']} tons
        </div>
    </div>
    """

    folium.Marker(
        location=[vehicle["latitude"], vehicle["longitude"]],
        popup=folium.Popup(popup_html, max_width=280),
        tooltip=f"{vehicle['vehicle_id']} — {vehicle['driver_name']} ({vehicle['status']})",
        icon=folium.Icon(color=icon_color, icon=icon_name, prefix="fa"),
    ).add_to(fleet_map)

    # Add pulsing circle for selected vehicle
    if is_selected:
        folium.CircleMarker(
            location=[vehicle["latitude"], vehicle["longitude"]],
            radius=18,
            color="#00D4AA",
            fill=True,
            fill_color="#00D4AA",
            fill_opacity=0.15,
            weight=2,
        ).add_to(fleet_map)


def _add_destination_marker(fleet_map: folium.Map, destination: Dict):
    """Add a prominent destination marker."""
    popup_html = f"""
    <div style="
        background: #1E1B4B;
        color: #E2E8F0;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        border: 2px solid #6366F1;
    ">
        <div style="font-size: 16px; font-weight: 700; color: #818CF8;">
            📍 DESTINATION
        </div>
        <div style="font-size: 13px; margin-top: 4px;">
            {destination.get('name', 'Destination')}
        </div>
        <div style="font-size: 11px; color: #94A3B8; margin-top: 4px;">
            {destination.get('lat', ''):.4f}, {destination.get('lon', ''):.4f}
        </div>
    </div>
    """

    folium.Marker(
        location=[destination["lat"], destination["lon"]],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"📍 {destination.get('name', 'Destination')}",
        icon=folium.Icon(color="purple", icon="flag", prefix="fa"),
    ).add_to(fleet_map)

    # Destination radius circle
    folium.CircleMarker(
        location=[destination["lat"], destination["lon"]],
        radius=12,
        color="#6366F1",
        fill=True,
        fill_color="#6366F1",
        fill_opacity=0.2,
        weight=2,
    ).add_to(fleet_map)


def _add_origin_marker(fleet_map: folium.Map, origin: Dict):
    """Add a prominent origin marker (green flag)."""
    popup_html = f"""
    <div style="
        background: #064E3B;
        color: #E2E8F0;
        padding: 12px 16px;
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
        border: 2px solid #10B981;
    ">
        <div style="font-size: 16px; font-weight: 700; color: #34D399;">
            🏁 STARTING HUB
        </div>
        <div style="font-size: 13px; margin-top: 4px;">
            {origin.get('name', 'Origin')}
        </div>
        <div style="font-size: 11px; color: #A7F3D0; margin-top: 4px;">
            {origin.get('lat', ''):.4f}, {origin.get('lon', ''):.4f}
        </div>
    </div>
    """

    folium.Marker(
        location=[origin["lat"], origin["lon"]],
        popup=folium.Popup(popup_html, max_width=250),
        tooltip=f"🏁 {origin.get('name', 'Origin')}",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(fleet_map)

    # Origin circle
    folium.CircleMarker(
        location=[origin["lat"], origin["lon"]],
        radius=12,
        color="#10B981",
        fill=True,
        fill_color="#10B981",
        fill_opacity=0.3,
        weight=2,
    ).add_to(fleet_map)


def _add_route_line(
    fleet_map: folium.Map, selected_vehicle: Dict, destination: Dict, selected_route: Optional[Dict] = None
):
    """Draw an animated, real-road color-coded route line based on live traffic congestion."""
    
    # 1. Default to straight-line coordinates
    points = [
        [selected_vehicle["latitude"], selected_vehicle["longitude"]],
        [destination["lat"], destination["lon"]],
    ]
    
    # 2. If we have actual road coordinates from OSRM, use them instead!
    if selected_route and selected_route.get("geometry_coordinates"):
        points = selected_route["geometry_coordinates"]
        
    # 3. Determine traffic congestion color (Google Maps style)
    congestion = (selected_route or {}).get("congestion_level", "CLEAR")
    color_map = {
        "CLEAR": "#10B981",      # Emerald Green
        "MODERATE": "#F59E0B",   # Amber / Orange
        "HEAVY": "#EF4444",      # Crimson Red
        "SEVERE": "#B91C1C",     # Dark blood Red
    }
    route_color = color_map.get(congestion, "#10B981")
    
    # Main route line
    folium.PolyLine(
        locations=points,
        color=route_color,
        weight=4,
        opacity=0.9,
        tooltip=f"Selected Route — Traffic: {congestion}",
    ).add_to(fleet_map)
    
    # Glowing background line
    folium.PolyLine(
        locations=points,
        color=route_color,
        weight=9,
        opacity=0.2,
    ).add_to(fleet_map)


def _add_route_line_from_geometry(fleet_map: folium.Map, route: Dict):
    """Draw a color-coded road from geometry_coordinates when no vehicle is selected (traffic queries)."""
    points = route.get("geometry_coordinates", [])
    if not points:
        return
    congestion = route.get("congestion_level", "MODERATE")
    color_map = {
        "CLEAR": "#10B981",
        "MODERATE": "#F59E0B",
        "HEAVY": "#EF4444",
        "SEVERE": "#B91C1C",
    }
    route_color = color_map.get(congestion, "#F59E0B")
    folium.PolyLine(
        locations=points,
        color=route_color,
        weight=4,
        opacity=0.9,
        tooltip=f"Traffic Route — {congestion}",
    ).add_to(fleet_map)
    folium.PolyLine(
        locations=points,
        color=route_color,
        weight=9,
        opacity=0.2,
    ).add_to(fleet_map)


def _add_legend(fleet_map: folium.Map):
    """Add a custom legend to the map."""
    legend_html = """
    <div style="
        position: fixed;
        bottom: 30px;
        left: 30px;
        z-index: 1000;
        background: rgba(15, 23, 42, 0.92);
        color: #E2E8F0;
        padding: 14px 18px;
        border-radius: 10px;
        font-family: 'Inter', sans-serif;
        font-size: 12px;
        border: 1px solid rgba(148, 163, 184, 0.2);
        backdrop-filter: blur(10px);
    ">
        <div style="font-weight: 700; margin-bottom: 8px; color: #00D4AA;">
            🚛 Fleet Legend
        </div>
        <div>🟢 Available</div>
        <div>🟡 On Delivery</div>
        <div>🔴 Maintenance</div>
        <div>⭐ Selected Vehicle</div>
        <div>🟣 Destination</div>
    </div>
    """
    fleet_map.get_root().html.add_child(folium.Element(legend_html))
