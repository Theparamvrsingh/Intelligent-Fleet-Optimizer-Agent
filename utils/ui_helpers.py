"""
UI Utilities — helper functions for the Streamlit frontend.
"""

from typing import Dict, Any


def get_status_badge(status: str) -> str:
    """Return an HTML badge for vehicle status."""
    colors = {
        "available": ("#00D4AA", "#022C22"),
        "on_delivery": ("#F59E0B", "#1C1400"),
        "maintenance": ("#EF4444", "#1C0000"),
    }
    text_color, bg_color = colors.get(status, ("#9CA3AF", "#1F2937"))
    label = status.replace("_", " ").title()
    return (
        f'<span style="background:{bg_color}; color:{text_color}; '
        f'border: 1px solid {text_color}; padding: 3px 10px; '
        f'border-radius: 12px; font-size: 11px; font-weight: 600;">{label}</span>'
    )


def get_fuel_color(fuel_level: int) -> str:
    """Return a color based on fuel level."""
    if fuel_level >= 70:
        return "#00D4AA"
    elif fuel_level >= 40:
        return "#F59E0B"
    else:
        return "#EF4444"


def get_congestion_color(congestion_level: str) -> str:
    """Return color for congestion badge."""
    colors = {
        "CLEAR": "#00D4AA",
        "MODERATE": "#F59E0B",
        "HEAVY": "#EF4444",
        "SEVERE": "#DC2626",
    }
    return colors.get(congestion_level, "#9CA3AF")


def format_eta(minutes: float) -> str:
    """Format ETA minutes into human-readable string."""
    if minutes < 60:
        return f"{int(minutes)} min"
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    return f"{hours}h {mins}m"


def metric_card_html(
    title: str,
    value: str,
    subtitle: str = "",
    color: str = "#00D4AA",
    icon: str = "📊",
) -> str:
    """Generate an HTML metric card for use in st.markdown()."""
    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(15,23,42,0.95) 0%, rgba(30,41,59,0.95) 100%);
        border: 1px solid rgba(148,163,184,0.15);
        border-left: 4px solid {color};
        border-radius: 12px;
        padding: 20px;
        margin: 8px 0;
        backdrop-filter: blur(10px);
    ">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
            <span style="font-size:24px;">{icon}</span>
            <span style="color:#94A3B8; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.05em;">{title}</span>
        </div>
        <div style="color:{color}; font-size:28px; font-weight:800; line-height:1;">{value}</div>
        {f'<div style="color:#64748B; font-size:12px; margin-top:6px;">{subtitle}</div>' if subtitle else ""}
    </div>
    """


def thinking_step_html(step: str, index: int, is_complete: bool = True) -> str:
    """Generate HTML for a single agent thinking step."""
    color = "#00D4AA" if is_complete else "#F59E0B"
    icon = "✅" if is_complete else "⏳"
    return f"""
    <div style="
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 10px 14px;
        background: rgba(0, 212, 170, 0.05);
        border-left: 3px solid {color};
        border-radius: 0 8px 8px 0;
        margin: 6px 0;
    ">
        <span style="font-size:16px; min-width:20px;">{icon}</span>
        <div>
            <span style="color:#64748B; font-size:11px;">Step {index + 1}</span>
            <div style="color:#E2E8F0; font-size:13px; margin-top:2px;">{step}</div>
        </div>
    </div>
    """


def vehicle_card_html(vehicle: Dict, route: Dict = None, is_selected: bool = False) -> str:
    """Generate a vehicle detail card."""
    status_colors = {
        "available": "#00D4AA",
        "on_delivery": "#F59E0B",
        "maintenance": "#EF4444",
    }
    type_icons = {"truck": "🚛", "van": "🚐", "mini_truck": "🚚"}

    status = vehicle.get("status", "available")
    color = status_colors.get(status, "#9CA3AF")
    icon = type_icons.get(vehicle.get("vehicle_type", "truck"), "🚗")
    fuel = vehicle.get("fuel_level", 0)
    fuel_color = get_fuel_color(fuel)
    border_color = "#00D4AA" if is_selected else "rgba(148,163,184,0.15)"
    star = "⭐ " if is_selected else ""

    route_section = ""
    if route:
        route_section = f"""
        <div style="
            background: rgba(99,102,241,0.1);
            border-radius: 8px;
            padding: 10px;
            margin-top: 12px;
            font-size: 12px;
            color: #E2E8F0;
        ">
            <b>Route Info:</b><br>
            📏 Distance: {route.get('distance_km', 'N/A')} km<br>
            ⏱️ ETA: {format_eta(route.get('duration_minutes', 0))}<br>
            🚦 Traffic: <span style="color:{get_congestion_color(route.get('congestion_level', 'CLEAR'))};">{route.get('congestion_level', 'N/A')}</span><br>
            ⏳ Delay: {route.get('traffic_delay_minutes', 0):.0f} min
        </div>
        """

    return f"""
    <div style="
        background: linear-gradient(135deg, rgba(15,23,42,0.98) 0%, rgba(30,41,59,0.98) 100%);
        border: 2px solid {border_color};
        border-radius: 14px;
        padding: 20px;
        margin: 8px 0;
        font-family: 'Inter', sans-serif;
    ">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <div style="font-size:20px; font-weight:800; color:#F1F5F9;">
                {star}{icon} {vehicle.get('vehicle_id', 'N/A')}
            </div>
            <span style="background:rgba({','.join(str(int(color.lstrip('#')[i:i+2], 16)) for i in (0,2,4))},0.15);
                color:{color}; padding:4px 12px; border-radius:12px; font-size:11px; font-weight:600; border:1px solid {color};">
                {status.replace('_',' ').title()}
            </span>
        </div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:8px; font-size:12px; color:#94A3B8;">
            <div><b style="color:#CBD5E1;">👤 Driver</b><br>{vehicle.get('driver_name', 'N/A')}</div>
            <div><b style="color:#CBD5E1;">📍 Location</b><br>{vehicle.get('location_name', 'N/A')}</div>
            <div>
                <b style="color:#CBD5E1;">⛽ Fuel</b><br>
                <span style="color:{fuel_color}; font-weight:700;">{fuel}%</span>
            </div>
            <div><b style="color:#CBD5E1;">📦 Capacity</b><br>{vehicle.get('capacity_tons', 'N/A')} tons</div>
        </div>
        {route_section}
    </div>
    """
