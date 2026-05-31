"""
Fleet Optimization Tool
------------------------
WHY AGENTIC AI IS USED HERE:
  A traditional rule-based system would pick the nearest vehicle blindly.
  An agent reasons about MULTIPLE factors simultaneously — fuel, traffic,
  vehicle type, driver availability, route conditions — and synthesizes
  them into a single optimal recommendation. This is genuine AI reasoning.

  LangGraph enables this multi-step reasoning as a stateful graph where each
  node represents a reasoning step and edges represent decision transitions.
"""

from typing import Dict, List, Any, Optional
from tools.fleet_lookup import get_available_vehicles
from tools.here_routing import call_here_routing_api, haversine_distance


def score_vehicle(
    vehicle: Dict,
    route_data: Dict,
    required_capacity: float = 0.0,
) -> Dict[str, Any]:
    """
    Score a single vehicle for dispatch suitability.
    
    Scoring formula (100 points total):
      - ETA score       : 35 pts  (faster = better)
      - Fuel score      : 30 pts  (higher fuel = better)
      - Capacity score  : 20 pts  (adequate capacity = better)
      - Traffic score   : 15 pts  (less congestion on route = better)
    """
    scores = {}
    total = 0

    # ── ETA Score (35 pts) ──────────────────────────────────────────────────
    duration = route_data.get("duration_minutes", 999)
    if duration < 15:
        eta_score = 35
    elif duration < 30:
        eta_score = 28
    elif duration < 60:
        eta_score = 18
    elif duration < 90:
        eta_score = 10
    else:
        eta_score = 3
    scores["eta_score"] = eta_score
    total += eta_score

    # ── Fuel Score (30 pts) ─────────────────────────────────────────────────
    fuel = vehicle.get("fuel_level", 0)
    fuel_score = min(30, int(fuel * 0.30))
    scores["fuel_score"] = fuel_score
    total += fuel_score

    # ── Capacity Score (20 pts) ─────────────────────────────────────────────
    capacity = vehicle.get("capacity_tons", 0)
    if required_capacity == 0.0:
        # No requirement given, reward higher capacity vehicles
        cap_score = min(20, int(capacity * 2.5))
    elif capacity >= required_capacity:
        cap_score = 20
    elif capacity >= required_capacity * 0.8:
        cap_score = 12
    else:
        cap_score = 0
    scores["capacity_score"] = cap_score
    total += cap_score

    # ── Traffic Score (15 pts) ──────────────────────────────────────────────
    congestion = route_data.get("congestion_level", "CLEAR")
    traffic_map = {"CLEAR": 15, "MODERATE": 10, "HEAVY": 5, "SEVERE": 0}
    traffic_score = traffic_map.get(congestion, 8)
    scores["traffic_score"] = traffic_score
    total += traffic_score

    scores["total_score"] = total
    return scores


def fleet_optimization_tool(
    dest_lat: float,
    dest_lon: float,
    required_capacity: float = 0.0,
    top_n: int = 3,
    route_data: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Tool 3: Fleet Optimization Tool
    
    Compares all available vehicles, routes each to the destination,
    scores them on multiple criteria, and returns the ranked recommendation.

    Args:
        dest_lat, dest_lon: Destination coordinates
        required_capacity: Minimum cargo capacity in tons (0 = any)
        top_n: Number of top candidates to return
        route_data: Cached routing data from the routing node

    Returns:
        Dict with best_vehicle, ranked_list, and explanation
    """
    available_vehicles = get_available_vehicles()

    if not available_vehicles:
        return {
            "success": False,
            "message": "No available vehicles found in the fleet.",
            "ranked_vehicles": [],
            "best_vehicle": None,
        }

    # Sort available vehicles by straight-line distance to destination first
    # This prevents hitting rate limits on public OSRM by only routing the top 3 closest operational vehicles
    for vehicle in available_vehicles:
        vehicle["_temp_dist"] = haversine_distance(
            vehicle["latitude"], vehicle["longitude"], dest_lat, dest_lon
        )
    
    # Filter out low fuel vehicles, sort by proximity, and pick top 3
    valid_candidates = [v for v in available_vehicles if v["fuel_level"] >= 15]
    valid_candidates.sort(key=lambda x: x["_temp_dist"])
    top_closest = valid_candidates[:3]

    ranked = []

    for vehicle in top_closest:
        # Check if route is already calculated in the previous graph node
        vid = vehicle["vehicle_id"]
        if route_data and vid in route_data:
            route = route_data[vid]
        else:
            # Call HERE/OSRM Routing for top closest vehicles
            route = call_here_routing_api(
                origin_lat=vehicle["latitude"],
                origin_lon=vehicle["longitude"],
                dest_lat=dest_lat,
                dest_lon=dest_lon,
                transport_mode=_vehicle_type_to_transport(vehicle["vehicle_type"]),
            )

        scores = score_vehicle(vehicle, route, required_capacity)

        ranked.append(
            {
                "vehicle": vehicle,
                "route": route,
                "scores": scores,
                "total_score": scores["total_score"],
            }
        )

    # Sort by total score descending
    ranked.sort(key=lambda x: x["total_score"], reverse=True)

    top_candidates = ranked[:top_n]
    best = top_candidates[0] if top_candidates else None

    return {
        "success": True,
        "best_vehicle": best,
        "ranked_vehicles": top_candidates,
        "total_evaluated": len(ranked),
        "explanation": _generate_explanation(best, top_candidates) if best else "No suitable vehicle found.",
    }


def _vehicle_type_to_transport(vehicle_type: str) -> str:
    """Map fleet vehicle type to HERE transport mode."""
    mapping = {
        "truck": "truck",
        "mini_truck": "truck",
        "van": "car",  # HERE doesn't have 'van', use 'car' for similar routing
    }
    return mapping.get(vehicle_type, "truck")


def _generate_explanation(best: Dict, ranked: List[Dict]) -> str:
    """Generate a human-readable explanation for the recommendation."""
    v = best["vehicle"]
    r = best["route"]
    s = best["scores"]

    lines = [
        f"✅ RECOMMENDED: {v['vehicle_id']} driven by {v['driver_name']}",
        f"   Current location: {v['location_name']}",
        f"   ETA to destination: {r['duration_minutes']} minutes ({r['distance_km']} km)",
        f"   Fuel level: {v['fuel_level']}% | Capacity: {v['capacity_tons']} tons",
        f"   Traffic condition: {r['congestion_level']} (delay: {r['traffic_delay_minutes']} min)",
        f"   Overall score: {s['total_score']}/100",
        "",
        "📊 Score breakdown:",
        f"   ETA: {s['eta_score']}/35 | Fuel: {s['fuel_score']}/30 | "
        f"Capacity: {s['capacity_score']}/20 | Traffic: {s['traffic_score']}/15",
    ]

    if len(ranked) > 1:
        lines.append("\n🔄 Other candidates considered:")
        for candidate in ranked[1:]:
            cv = candidate["vehicle"]
            cr = candidate["route"]
            lines.append(
                f"   • {cv['vehicle_id']} ({cv['driver_name']}) — "
                f"ETA: {cr['duration_minutes']} min | Score: {candidate['total_score']}/100"
            )

    return "\n".join(lines)


def fleet_optimization_tool_str(
    dest_lat: float,
    dest_lon: float,
    required_capacity: float = 0.0,
) -> str:
    """LangGraph-compatible string output version of the optimization tool."""
    result = fleet_optimization_tool(dest_lat, dest_lon, required_capacity)
    if not result["success"]:
        return result["message"]
    return result["explanation"]
