"""
Fleet Lookup Tool
-----------------
WHY TOOL CALLING IS REQUIRED:
  Instead of the LLM hallucinating fleet data, we force it to call this tool
  which reads from the ground-truth JSON database. This ensures factual accuracy.
  Tool calling is the bridge between LLM reasoning and real-world data.
"""

import json
import os
from typing import Dict, List, Any

# Path to the fleet data JSON file
FLEET_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "fleet_data.json")


def load_fleet_data() -> Dict:
    """Load the full fleet database from JSON."""
    with open(FLEET_DATA_PATH, "r") as f:
        return json.load(f)


def get_all_vehicles() -> List[Dict]:
    """Return all vehicles from the fleet database."""
    data = load_fleet_data()
    return data.get("vehicles", [])


def get_available_vehicles() -> List[Dict]:
    """
    Tool 1: Fleet Lookup Tool
    Returns only vehicles with status 'available'.
    Available = can be dispatched immediately.
    """
    all_vehicles = get_all_vehicles()
    available = [v for v in all_vehicles if v["status"] == "available"]
    return available


def get_vehicle_by_id(vehicle_id: str) -> Dict | None:
    """Find a specific vehicle by its ID."""
    all_vehicles = get_all_vehicles()
    for vehicle in all_vehicles:
        if vehicle["vehicle_id"].upper() == vehicle_id.upper():
            return vehicle
    return None


def get_fleet_statistics() -> Dict:
    """Compute summary statistics for the sidebar dashboard."""
    all_vehicles = get_all_vehicles()
    total = len(all_vehicles)
    available = sum(1 for v in all_vehicles if v["status"] == "available")
    on_delivery = sum(1 for v in all_vehicles if v["status"] == "on_delivery")
    maintenance = sum(1 for v in all_vehicles if v["status"] == "maintenance")
    avg_fuel = sum(v["fuel_level"] for v in all_vehicles) / total if total > 0 else 0

    return {
        "total_vehicles": total,
        "available": available,
        "on_delivery": on_delivery,
        "maintenance": maintenance,
        "average_fuel_level": round(avg_fuel, 1),
        "vehicle_types": {
            "truck": sum(1 for v in all_vehicles if v["vehicle_type"] == "truck"),
            "van": sum(1 for v in all_vehicles if v["vehicle_type"] == "van"),
            "mini_truck": sum(1 for v in all_vehicles if v["vehicle_type"] == "mini_truck"),
        },
    }


def fleet_lookup_tool(query: str = "available") -> str:
    """
    LangGraph-compatible tool function for fleet lookup.
    Returns a structured string summary of fleet data for the agent.

    Args:
        query: 'available', 'all', or a vehicle_id like 'V101'
    """
    if query.startswith("V") or query.startswith("v"):
        # Look up a specific vehicle
        vehicle = get_vehicle_by_id(query)
        if vehicle:
            return (
                f"Vehicle {vehicle['vehicle_id']} — Driver: {vehicle['driver_name']} | "
                f"Location: {vehicle['location_name']} ({vehicle['latitude']}, {vehicle['longitude']}) | "
                f"Status: {vehicle['status']} | Fuel: {vehicle['fuel_level']}% | "
                f"Type: {vehicle['vehicle_type']} | Capacity: {vehicle['capacity_tons']} tons"
            )
        return f"No vehicle found with ID: {query}"

    elif query == "all":
        vehicles = get_all_vehicles()
    else:
        # Default: available only
        vehicles = get_available_vehicles()

    if not vehicles:
        return "No vehicles found matching the criteria."

    lines = [f"Found {len(vehicles)} vehicle(s):\n"]
    for v in vehicles:
        lines.append(
            f"  • {v['vehicle_id']} ({v['vehicle_type']}) — {v['driver_name']} | "
            f"At: {v['location_name']} | Fuel: {v['fuel_level']}% | Status: {v['status']}"
        )
    return "\n".join(lines)
