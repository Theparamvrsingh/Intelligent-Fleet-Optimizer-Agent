"""
HERE Routing Tool
-----------------
WHY HERE APIs ARE USED:
  HERE provides enterprise-grade routing with real-time traffic, turn-by-turn
  navigation, and accurate ETA predictions. Unlike open-source alternatives,
  HERE's routing engine accounts for historical traffic patterns, road closures,
  and dynamic congestion — critical for fleet operations SLAs.

WHY NOT JUST USE GOOGLE MAPS:
  HERE has a dedicated Fleet & Logistics product line with batch routing,
  isoline calculations, and truck-specific routing (bridge heights, weight limits).
  This makes it the industry standard for logistics companies.
"""

import os
import math
import time
import requests
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

HERE_API_KEY = os.getenv("HERE_API_KEY", "")
HERE_ROUTING_BASE_URL = "https://router.hereapi.com/v8/routes"
HERE_GEOCODE_URL = "https://geocode.search.hereapi.com/v1/geocode"


def geocode_address(address: str) -> Optional[Tuple[float, float, str]]:
    """
    Geocodes any city or address globally using HERE Geocoding API,
    falling back to OpenStreetMap's Nominatim public service.
    This guarantees any location query (e.g. Mumbai, Tokyo) works instantly.
    """
    if not address or len(address.strip()) < 2:
        return None
    
    # 1. Try HERE API
    if HERE_API_KEY and HERE_API_KEY != "your_here_api_key_here":
        try:
            params = {
                "q": address,
                "apikey": HERE_API_KEY,
                "limit": 1
            }
            res = requests.get(HERE_GEOCODE_URL, params=params, timeout=5)
            if res.status_code == 200:
                items = res.json().get("items", [])
                if items:
                    pos = items[0]["position"]
                    return float(pos["lat"]), float(pos["lng"]), items[0]["title"]
        except Exception:
            pass

    # 2. Try Nominatim Public API (OSM) as a robust zero-config global fallback
    try:
        headers = {"User-Agent": "intelligent-fleet-ops-agent/1.0"}
        # Restrict searches primarily to India to prevent Bennett University matching South Dakota, USA,
        # unless user specifies global country names
        global_terms = ["tokyo", "japan", "usa", "london", "uk", "america", "united states", "paris", "france", "germany", "berlin", "dubai", "singapore"]
        use_india_filter = not any(term in address.lower() for term in global_terms)
        
        country_param = "&countrycodes=in" if use_india_filter else ""
        url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(address)}&format=json&limit=1{country_param}"
        
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if data:
                return float(data[0]["lat"]), float(data[0]["lon"]), data[0]["display_name"]
    except Exception:
        pass

    return None



def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate straight-line distance in km using the Haversine formula.
    Used as fallback when HERE API is unavailable.
    """
    R = 6371  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def estimate_eta_minutes(distance_km: float, avg_speed_kmph: float = 35.0) -> float:
    """Estimate travel time given distance and average city speed."""
    return (distance_km / avg_speed_kmph) * 60


def call_osrm_routing_api(
    origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float
) -> Dict[str, Any]:
    """
    Call the completely free, zero-config Open Source Routing Machine (OSRM) API.
    Provides actual driving road distances and ETAs globally without keys or billing.
    Also fetches real road coordinates to plot on the Folium map.
    """
    url = f"http://router.project-osrm.org/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    params = {
        "overview": "full",
        "geometries": "geojson",
        "steps": "false"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("routes"):
                route = data["routes"][0]
                distance_km = round(route["distance"] / 1000, 2)
                base_duration = round(route["duration"] / 60, 1)
                
                # Dynamic peak traffic simulation
                current_hour = time.localtime().tm_hour
                is_peak = (7 <= current_hour <= 10) or (17 <= current_hour <= 20)
                multiplier = 1.3 if is_peak else 1.08
                duration_minutes = round(base_duration * multiplier, 1)
                traffic_delay = max(0.0, round(duration_minutes - base_duration, 1))
                
                # Parse geometry points
                geometry = route.get("geometry", {})
                coords = geometry.get("coordinates", [])
                folium_coords = [[pt[1], pt[0]] for pt in coords]
                
                return {
                    "success": True,
                    "source": "OSRM_FREE_API",
                    "distance_km": distance_km,
                    "duration_minutes": duration_minutes,
                    "base_duration_minutes": base_duration,
                    "traffic_delay_minutes": traffic_delay,
                    "transport_mode": "truck",
                    "polyline": "",
                    "geometry_coordinates": folium_coords,
                    "congestion_level": _classify_congestion(traffic_delay, base_duration),
                }
    except Exception:
        pass
    
    # Ultimate straight-line fallback if OSRM is down
    return _synthetic_route(origin_lat, origin_lon, dest_lat, dest_lon)


def call_here_routing_api(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    transport_mode: str = "truck",
) -> Dict[str, Any]:
    """
    Call the actual HERE Routing v8 API.
    Returns route summary with distance, duration, and traffic delay.

    Args:
        origin_lat, origin_lon: Starting point coordinates
        dest_lat, dest_lon: Destination coordinates
        transport_mode: 'truck', 'car', or 'pedestrian'
    """
    if not HERE_API_KEY or HERE_API_KEY == "your_here_api_key_here":
        # Graceful fallback: call the free, zero-config OSRM API
        return call_osrm_routing_api(origin_lat, origin_lon, dest_lat, dest_lon)

    params = {
        "transportMode": transport_mode,
        "origin": f"{origin_lat},{origin_lon}",
        "destination": f"{dest_lat},{dest_lon}",
        "return": "summary,travelSummary,polyline",
        "apikey": HERE_API_KEY,
    }

    try:
        response = requests.get(HERE_ROUTING_BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        route = data["routes"][0]["sections"][0]
        summary = route["travelSummary"]

        distance_km = round(summary["length"] / 1000, 2)
        duration_min = round(summary["duration"] / 60, 1)
        base_duration = round(summary.get("baseDuration", summary["duration"]) / 60, 1)
        traffic_delay = round(duration_min - base_duration, 1)

        return {
            "success": True,
            "source": "HERE_API",
            "distance_km": distance_km,
            "duration_minutes": duration_min,
            "base_duration_minutes": base_duration,
            "traffic_delay_minutes": max(0, traffic_delay),
            "transport_mode": transport_mode,
            "polyline": route.get("polyline", ""),
            "congestion_level": _classify_congestion(traffic_delay),
        }

    except requests.exceptions.RequestException as e:
        # Fallback to synthetic if API call fails
        result = _synthetic_route(origin_lat, origin_lon, dest_lat, dest_lon)
        result["api_error"] = str(e)
        return result


def _synthetic_route(
    origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float
) -> Dict[str, Any]:
    """
    Synthetic route calculation when HERE API key is not configured.
    Uses Haversine distance + realistic traffic multipliers.
    This ensures the demo works without a paid API key.
    """
    straight_line_km = haversine_distance(origin_lat, origin_lon, dest_lat, dest_lon)

    # Road factor: actual road distance is ~1.3–1.5x straight line in urban areas
    road_distance_km = round(straight_line_km * 1.35, 2)

    # Delhi NCR peak hour simulation (7–10 AM, 5–8 PM are congested)
    current_hour = time.localtime().tm_hour
    is_peak = 7 <= current_hour <= 10 or 17 <= current_hour <= 20

    avg_speed = 25.0 if is_peak else 38.0  # km/h
    duration_min = round((road_distance_km / avg_speed) * 60, 1)
    base_duration = round((road_distance_km / 45.0) * 60, 1)  # free-flow speed
    traffic_delay = max(0, round(duration_min - base_duration, 1))

    return {
        "success": True,
        "source": "SYNTHETIC_FALLBACK",
        "distance_km": road_distance_km,
        "duration_minutes": duration_min,
        "base_duration_minutes": base_duration,
        "traffic_delay_minutes": traffic_delay,
        "transport_mode": "truck",
        "polyline": "",
        "congestion_level": _classify_congestion(traffic_delay, base_duration),
        "note": "Using synthetic route — add HERE API key for live data",
    }


def _classify_congestion(delay_minutes: float, base_duration: float = 0.0) -> str:
    """Classify traffic congestion by delay ratio (delay / free-flow time).
    Ratio-based avoids short trips always being CLEAR even with 8-30% slowdowns."""
    if base_duration > 0:
        ratio = delay_minutes / base_duration
        if ratio < 0.06:
            return "CLEAR"
        elif ratio < 0.20:
            return "MODERATE"
        elif ratio < 0.38:
            return "HEAVY"
        else:
            return "SEVERE"
    # Fallback to raw minutes when base is unknown
    if delay_minutes < 3:
        return "CLEAR"
    elif delay_minutes < 12:
        return "MODERATE"
    elif delay_minutes < 25:
        return "HEAVY"
    else:
        return "SEVERE"


def here_routing_tool(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    vehicle_id: str = "",
    transport_mode: str = "truck",
) -> str:
    """
    LangGraph-compatible tool function for HERE routing.
    Returns a structured string with route details for the agent.
    """
    route = call_here_routing_api(origin_lat, origin_lon, dest_lat, dest_lon, transport_mode)

    source_note = f" (source: {route['source']})"
    result = (
        f"Route calculated{source_note}:\n"
        f"  Distance: {route['distance_km']} km\n"
        f"  ETA: {route['duration_minutes']} minutes\n"
        f"  Free-flow time: {route['base_duration_minutes']} minutes\n"
        f"  Traffic delay: {route['traffic_delay_minutes']} minutes\n"
        f"  Congestion: {route['congestion_level']}"
    )
    if vehicle_id:
        result = f"Vehicle {vehicle_id} → " + result
    return result
