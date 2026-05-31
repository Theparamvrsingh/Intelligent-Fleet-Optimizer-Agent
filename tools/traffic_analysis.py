"""
Traffic Analysis Tool
---------------------
WHY THIS TOOL EXISTS:
  Routing data from HERE gives raw numbers (delay in minutes).
  This tool interprets those numbers and generates actionable logistics
  intelligence: "avoid this route", "expect X minute delay", "consider
  alternate route via Y". This is the difference between data and insight.
"""

from typing import Dict, List, Any
from tools.here_routing import call_here_routing_api, _classify_congestion


# Known congestion hotspots in Delhi NCR (for enhanced analysis)
CONGESTION_HOTSPOTS = {
    "NH-48": {"lat": 28.4890, "lon": 77.0800, "peak_delay": 35},
    "NH-9 Ghaziabad": {"lat": 28.6667, "lon": 77.4200, "peak_delay": 28},
    "NH-44 Badarpur": {"lat": 28.5050, "lon": 77.2820, "peak_delay": 40},
    "Ring Road Ashram": {"lat": 28.5700, "lon": 77.2500, "peak_delay": 25},
    "DND Flyway": {"lat": 28.5600, "lon": 77.3100, "peak_delay": 20},
    "Akshardham": {"lat": 28.6127, "lon": 77.2773, "peak_delay": 22},
}


def analyze_traffic(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> Dict[str, Any]:
    """
    Tool 4: Traffic Analysis Tool
    
    Analyzes the route from origin to destination using HERE API data,
    identifies congestion levels, delays, and provides routing recommendations.

    Returns a structured traffic analysis report.
    """
    # Get primary route from HERE
    primary_route = call_here_routing_api(origin_lat, origin_lon, dest_lat, dest_lon, "truck")

    delay = primary_route.get("traffic_delay_minutes", 0)
    congestion = primary_route.get("congestion_level", "CLEAR")
    distance = primary_route.get("distance_km", 0)
    duration = primary_route.get("duration_minutes", 0)

    # Identify nearby hotspots that might affect the route
    affected_hotspots = _identify_affected_hotspots(origin_lat, origin_lon, dest_lat, dest_lon)

    # Generate routing advice
    advice = _generate_routing_advice(congestion, delay, affected_hotspots)

    # Compute severity score 0–100
    severity = _compute_traffic_severity(delay, congestion)

    return {
        "success": True,
        "primary_route": primary_route,
        "congestion_level": congestion,
        "traffic_delay_minutes": delay,
        "severity_score": severity,
        "affected_hotspots": affected_hotspots,
        "routing_advice": advice,
        "eta_minutes": duration,
        "distance_km": distance,
        "summary": _build_summary(congestion, delay, duration, affected_hotspots, advice),
    }


def _identify_affected_hotspots(
    origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float
) -> List[Dict]:
    """
    Identify known congestion hotspots that fall roughly along the route.
    Uses a bounding box heuristic for simplicity.
    """
    min_lat = min(origin_lat, dest_lat) - 0.05
    max_lat = max(origin_lat, dest_lat) + 0.05
    min_lon = min(origin_lon, dest_lon) - 0.05
    max_lon = max(origin_lon, dest_lon) + 0.05

    affected = []
    for name, info in CONGESTION_HOTSPOTS.items():
        if min_lat <= info["lat"] <= max_lat and min_lon <= info["lon"] <= max_lon:
            affected.append({"name": name, "peak_delay_minutes": info["peak_delay"]})

    return affected


def _compute_traffic_severity(delay_minutes: float, congestion_level: str) -> int:
    """Return a 0–100 severity score for UI color coding."""
    base = {"CLEAR": 5, "MODERATE": 30, "HEAVY": 65, "SEVERE": 90}
    score = base.get(congestion_level, 10)
    # Add delay contribution
    score = min(100, score + int(delay_minutes * 0.5))
    return score


def _generate_routing_advice(
    congestion: str, delay: float, hotspots: List[Dict]
) -> List[str]:
    """Generate actionable routing recommendations."""
    advice = []

    if congestion == "CLEAR":
        advice.append("✅ Route is clear — proceed via the primary route.")
    elif congestion == "MODERATE":
        advice.append("⚠️ Moderate congestion detected. Expect minor delays.")
        advice.append("💡 Consider departing 10 minutes earlier.")
    elif congestion == "HEAVY":
        advice.append("🚨 Heavy traffic on primary route.")
        advice.append("🔄 Consider alternate routes to avoid peak-hour congestion.")
        advice.append("⏰ Best departure window: before 7 AM or after 8 PM.")
    elif congestion == "SEVERE":
        advice.append("🚨 SEVERE congestion — route blocked or extremely slow.")
        advice.append("🔄 STRONGLY recommend alternate route.")
        advice.append("📞 Contact dispatch for alternate delivery slot.")

    if hotspots:
        advice.append(f"🗺️ Known hotspots on route: {', '.join(h['name'] for h in hotspots)}")

    if delay > 20:
        advice.append(f"⏱️ Current traffic adds {delay:.0f} minutes to ETA — update customer accordingly.")

    return advice


def _build_summary(
    congestion: str, delay: float, duration: float, hotspots: List, advice: List[str]
) -> str:
    """Build a readable summary string for the agent."""
    hotspot_text = ""
    if hotspots:
        hotspot_text = f" Known hotspots: {', '.join(h['name'] for h in hotspots[:2])}."

    return (
        f"Traffic Analysis: {congestion} conditions with {delay:.0f} min delay. "
        f"Total ETA: {duration:.0f} minutes.{hotspot_text} "
        f"Advice: {advice[0] if advice else 'Proceed normally.'}"
    )


def traffic_analysis_tool_str(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
) -> str:
    """LangGraph-compatible string output version of the traffic analysis tool."""
    result = analyze_traffic(origin_lat, origin_lon, dest_lat, dest_lon)
    lines = [result["summary"], ""]
    lines.append("Routing Recommendations:")
    for item in result["routing_advice"]:
        lines.append(f"  {item}")
    return "\n".join(lines)
