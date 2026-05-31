import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import time
from streamlit_folium import st_folium
from agents.fleet_agent import run_fleet_agent
from tools.fleet_lookup import get_fleet_statistics, get_all_vehicles, get_available_vehicles
from services.map_service import create_fleet_map
from utils.ui_helpers import get_fuel_color, get_congestion_color, format_eta

# Page settings
st.set_page_config(
    page_title="Fleet Operations Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium dark layout styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [data-testid="stAppViewContainer"] {
    background: #0a0c10 !important;
    color: #c9d1d9 !important;
    font-family: 'Inter', sans-serif !important;
}
.stMetric {
    background: #161b22 !important;
    border: 1px solid #21262d !important;
    border-radius: 6px !important;
    padding: 12px !important;
}
.stMetric label {
    color: #8b949e !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
}
.stMetric div[data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 20px !important;
    font-weight: 600 !important;
}
.card {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 14px;
    margin-bottom: 12px;
}
.sec-title {
    font-size: 10px;
    font-weight: 600;
    color: #8b949e;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    padding-bottom: 6px;
    border-bottom: 1px solid #21262d;
    margin-bottom: 12px;
    margin-top: 10px;
}
.kv-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #1c2128;
    font-size: 12px;
}
.kv-row:last-child {
    border-bottom: none;
}
.kv-label {
    color: #8b949e;
}
.kv-val {
    color: #e6edf3;
    font-weight: 500;
}
.health-bar {
    background: #21262d;
    border-radius: 3px;
    height: 4px;
    margin-top: 6px;
}
.tag-badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.03em;
}
</style>
""", unsafe_allow_html=True)

# ── Session State Management ──────────────────────────────────────────────────
if "query_box" not in st.session_state:
    st.session_state["query_box"] = ""
if "last_executed_query" not in st.session_state:
    st.session_state["last_executed_query"] = ""
if "agent_result" not in st.session_state:
    st.session_state["agent_result"] = None
if "elapsed" not in st.session_state:
    st.session_state["elapsed"] = 0

def run_query(query_str):
    if query_str.strip():
        with st.spinner("Analyzing request and calculating optimal routes"):
            t0 = time.time()
            res = run_fleet_agent(query_str)
            st.session_state["elapsed"] = round(time.time() - t0, 2)
            st.session_state["agent_result"] = res
            st.session_state["last_executed_query"] = query_str

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
stats = get_fleet_statistics()
all_v = get_all_vehicles()
available = get_available_vehicles()

with st.sidebar:
    st.markdown("### Fleet Operations")
    st.caption("Delhi NCR Agent and Real-Time Routing")
    st.divider()

    # Section 1: Overview
    st.markdown('<p class="sec-title">Overview</p>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Total", stats["total_vehicles"])
        st.metric("On Route", stats["on_delivery"])
    with c2:
        st.metric("Available", stats["available"])
        st.metric("Service", stats["maintenance"])
    st.divider()

    # Section 2: Fleet Health
    st.markdown('<p class="sec-title">Fleet Health</p>', unsafe_allow_html=True)
    af = stats["average_fuel_level"]
    fc = get_fuel_color(int(af))
    st.markdown(f"""
    <div class="card">
        <div class="kv-row">
            <span class="kv-label">Avg Fuel Level</span>
            <span style="color:{fc};font-weight:600;">{af}%</span>
        </div>
        <div class="health-bar">
            <div style="width:{af}%;height:100%;background:{fc};border-radius:3px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    types = stats["vehicle_types"]
    tlabels = {"truck": "Truck", "van": "Van", "mini_truck": "Mini Truck"}
    type_html = '<div class="card">'
    for vt, cnt in types.items():
        pct = int(cnt / stats["total_vehicles"] * 100)
        type_html += f'<div class="kv-row"><span class="kv-label">{tlabels.get(vt, vt)}</span><span class="kv-val">{cnt} <span style="color:#484f58;">({pct}%)</span></span></div>'
    type_html += "</div>"
    st.markdown(type_html, unsafe_allow_html=True)
    st.divider()

    # Section 3: Health Alerts
    st.markdown('<p class="sec-title">Health Alerts</p>', unsafe_allow_html=True)
    low_fuel = [v for v in all_v if v["fuel_level"] < 40]
    maint_v  = [v for v in all_v if v["status"] == "maintenance"]
    st.markdown(f"""
    <div class="card">
        <div class="kv-row"><span class="kv-label">Low Fuel</span><span style="color:{"#d29922" if low_fuel else "#238636"};font-weight:600;">{len(low_fuel)}</span></div>
        <div class="kv-row"><span class="kv-label">Maintenance</span><span style="color:{"#da3633" if maint_v else "#238636"};font-weight:600;">{len(maint_v)}</span></div>
        <div class="kv-row"><span class="kv-label">Operational</span><span style="color:#238636;font-weight:600;">{stats["available"]+stats["on_delivery"]}</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    if low_fuel:
        alert_html = '<div class="card"><div style="font-size:10px;color:#d29922;text-transform:uppercase;letter-spacing:.05em;margin-bottom:6px;">Alerts</div>'
        for v in low_fuel[:4]:
            alert_html += f'<div class="kv-row"><span style="color:#e6edf3;">{v["vehicle_id"]}</span><span style="color:#d29922;">{v["fuel_level"]}%</span></div>'
        alert_html += "</div>"
        st.markdown(alert_html, unsafe_allow_html=True)
    st.divider()

    # Section 4: Available list
    st.markdown(f'<p class="sec-title">Available ({len(available)})</p>', unsafe_allow_html=True)
    for v in available[:6]:
        fl = v["fuel_level"]
        fclr = get_fuel_color(fl)
        s_color = {"available": "#238636", "on_delivery": "#d29922", "maintenance": "#da3633"}.get(v["status"], "#8b949e")
        st.markdown(f"""
        <div style="padding:8px 0;border-bottom:1px solid #21262d;">
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:12px;font-weight:600;color:#e6edf3;">{v['vehicle_id']}</span>
                <span style="font-size:11px;color:{fclr};font-weight:500;">{fl}%</span>
            </div>
            <div style="font-size:11px;color:#8b949e;margin-top:2px;">{v['driver_name']}</div>
            <div style="font-size:10px;color:#484f58;margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{v['location_name']}</div>
            <div style="margin-top:4px;"><span class="tag-badge" style="background:{s_color}18;color:{s_color};border:1px solid {s_color}33;">{v['vehicle_type'].replace('_',' ').title()}</span></div>
        </div>
        """, unsafe_allow_html=True)

    if len(available) > 6:
        st.markdown(f'<div style="font-size:11px;color:#484f58;padding-top:6px;">+{len(available)-6} more available</div>', unsafe_allow_html=True)
    st.divider()
    st.markdown('<p style="font-size:9px;color:#30363d;text-align:center;margin:0;">LangGraph · Gemini · OSRM Free Routing</p>', unsafe_allow_html=True)


# ── MAIN CONTENT ──────────────────────────────────────────────────────────────
st.markdown('<h2 style="font-size:22px;font-weight:700;color:#e6edf3;letter-spacing:-.02em;margin:0 0 4px;">Fleet Routing and Dispatch Console</h2><p style="font-size:13px;color:#8b949e;margin:0 0 20px;">Calculate routes, estimate ETAs, analyze traffic delays, and select optimal dispatch options globally.</p>', unsafe_allow_html=True)

# Examples section (Purely Indian cities as requested)
EXAMPLES = [
    "Which vehicle should deliver to Noida Sector 18",
    "Which vehicle can reach Noida fastest",
    "What is the ETA of Vehicle V101 to Jaipur",
    "Which route avoids traffic to Gurugram",
    "Best vehicle for delivery to Faridabad",
]

# Display standard buttons for examples that immediately execute the query!
st.markdown('<p style="font-size:11px;color:#8b949e;margin-bottom:8px;">Example test cases:</p>', unsafe_allow_html=True)
ex_cols = st.columns(len(EXAMPLES))
for idx, (col, ex_text) in enumerate(zip(ex_cols, EXAMPLES)):
    with col:
        if st.button(f"Example {idx+1}", key=f"ex_btn_{idx}", help=ex_text, use_container_width=True):
            st.session_state["query_box"] = ex_text
            st.rerun()

# Main Search Input Field
user_query = st.text_input(
    "Query Console",
    placeholder="Ask literally anything: e.g. Which vehicle is closest to Mumbai or ETA of V102 to Jaipur",
    key="query_box"
)

# Run button
mc1, mc2 = st.columns([5, 1])
with mc2:
    trigger_run = st.button("Run Intelligence", use_container_width=True)

# State check: Execute if button pressed or if the query is fresh and unexecuted
should_run = False
if trigger_run and user_query.strip():
    should_run = True
elif user_query.strip() and user_query != st.session_state["last_executed_query"]:
    should_run = True

if should_run:
    run_query(user_query)

st.divider()

# ── RESULTS DISPLAY ───────────────────────────────────────────────────────────
if st.session_state["agent_result"]:
    res = st.session_state["agent_result"]
    elapsed = st.session_state["elapsed"]
    
    dest = res.get("destination") or {"lat": 28.5706, "lon": 77.3219, "name": "Noida Sector 18"}
    sel  = res.get("selected_vehicle")
    route_data   = res.get("route_data") or {}
    traffic_data = res.get("traffic_data") or {}
    opt_data     = res.get("optimization_data") or {}
    ranked       = opt_data.get("ranked_vehicles", [])

    best_route = None
    intent = res.get("intent", "optimization")
    if sel:
        best_route = route_data.get(sel.get("vehicle_id"))
    if not best_route and opt_data.get("best_vehicle"):
        best_route = opt_data["best_vehicle"].get("route")
    # For traffic queries: pick first available route from route_data (any vehicle)
    if not best_route and route_data:
        best_route = next(iter(route_data.values()), None)

    # Metrics Overview Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Destination Name", dest.get("name", "Noida Sector 18"))
    with m2:
        st.metric("Distance", f'{best_route["distance_km"]} km' if best_route else "—")
    with m3:
        st.metric("Estimated Time", format_eta(best_route["duration_minutes"]) if best_route else "—")
    with m4:
        cong = traffic_data.get("congestion_level", "—")
        delay = traffic_data.get("traffic_delay_minutes", 0)
        st.metric("Traffic Status", cong, delta=f"+{delay:.0f} min delay" if delay else "No Delay", delta_color="inverse")
    with m5:
        st.metric("Assigned Vehicle", sel.get("vehicle_id", "—") if sel else "—")

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    
    # 3 Column Detail Layout
    L, M, R = st.columns([1.6, 3.0, 1.8])

    # Left: Agent Reasoning & Steps
    with L:
        st.markdown('<p class="sec-title">Agent Reasoning Steps</p>', unsafe_allow_html=True)
        for i, step in enumerate(res.get("thinking_steps", [])):
            clean = step.encode("ascii", "ignore").decode().strip()
            # Strip formatting punctuation
            if "—" in clean:
                clean = clean.split("—", 1)[-1].strip()
            st.markdown(f"""
            <div style="padding:9px 12px;border-left:2px solid #388bfd;background:#161b22;border-radius:0 4px 4px 0;margin-bottom:6px;">
                <div style="font-size:10px;color:#8b949e;margin-bottom:2px;">Step {i+1}</div>
                <div style="font-size:11px;color:#c9d1d9;line-height:1.5;">{clean}</div>
            </div>
            """, unsafe_allow_html=True)

        tools = res.get("tools_called", [])
        st.markdown('<p class="sec-title" style="margin-top:12px;">Tools Invoked</p>', unsafe_allow_html=True)
        t_html = '<div class="card">'
        for t in tools:
            t_html += f'<div class="kv-row"><span class="kv-val" style="color:#388bfd;">{t}</span></div>'
        t_html += f'<div style="font-size:10px;color:#8b949e;margin-top:8px;">Calculated in {elapsed} seconds</div></div>'
        st.markdown(t_html, unsafe_allow_html=True)

    # Middle: Folium Map, Answer & Matrix
    with M:
        st.markdown('<p class="sec-title">Geocoded Location Map</p>', unsafe_allow_html=True)
        fmap = create_fleet_map(
            all_v, 
            destination=dest, 
            selected_vehicle=sel, 
            selected_route=best_route, 
            zoom_start=10 if dest.get("name") != "Noida Sector 18" else 11,
            custom_source=res.get("custom_source")
        )
        map_key = f"folium_map_{dest.get('lat')}_{dest.get('lon')}_{sel.get('vehicle_id') if sel else 'none'}_{intent}"
        st_folium(fmap, width=None, height=380, returned_objects=[], key=map_key)

        st.markdown('<p class="sec-title" style="margin-top:12px;">Final Synthesis</p>', unsafe_allow_html=True)
        answer = res.get("final_answer", "No synthesis provided.")
        answer = answer.replace("?", "")
        st.markdown(f"""
        <div class="card" style="border-left:3px solid #1f6feb;font-size:13px;color:#c9d1d9;line-height:1.75;">
            {answer.replace(chr(10), "<br>")}
        </div>
        """, unsafe_allow_html=True)

        if ranked:
            st.markdown('<p class="sec-title" style="margin-top:12px;">Fleet Routing Analytics Matrix</p>', unsafe_allow_html=True)
            hdr = '<div class="card"><div style="display:grid;grid-template-columns:70px 65px 55px 45px 45px 65px 45px;font-size:10px;color:#8b949e;font-weight:600;text-transform:uppercase;letter-spacing:.05em;padding-bottom:6px;border-bottom:1px solid #21262d;">'
            hdr += "<div>ID</div><div>Driver</div><div>ETA</div><div>Fuel</div><div>Cap</div><div>Traffic</div><div>Score</div></div>"
            rows = ""
            for r in ranked:
                v = r["vehicle"]; rt = r["route"]
                is_best = sel and v["vehicle_id"] == sel.get("vehicle_id", "")
                clr = "#238636" if is_best else "#8b949e"
                rows += f'<div style="display:grid;grid-template-columns:70px 65px 55px 45px 45px 65px 45px;font-size:11px;padding:6px 0;border-bottom:1px solid #1c2128;align-items:center;">'
                rows += f'<div style="color:{clr};font-weight:600;">{"Recommended " if is_best else ""}{v["vehicle_id"]}</div>'
                rows += f'<div style="color:#8b949e;font-size:10px;">{v["driver_name"].split()[0]}</div>'
                rows += f'<div>{format_eta(rt.get("duration_minutes",0))}</div>'
                rows += f'<div style="color:{get_fuel_color(v["fuel_level"])};">{v["fuel_level"]}%</div>'
                rows += f'<div>{v["capacity_tons"]}t</div>'
                cclr = get_congestion_color(rt.get("congestion_level","CLEAR"))
                rows += f'<div style="color:{cclr};font-size:10px;">{rt.get("congestion_level","—")}</div>'
                rows += f'<div style="color:{clr};font-weight:600;">{r["total_score"]}</div></div>'
            st.markdown(hdr + rows + '<div style="font-size:10px;color:#8b949e;margin-top:6px;">Calculated using formula: ETA (35 points) + Fuel (30 points) + Capacity (20 points) + Traffic (15 points)</div></div>', unsafe_allow_html=True)

    # Right: Dispatch Candidate & Details
    with R:
        intent = res.get("intent", "optimization")
        if intent == "traffic_analysis":
            st.markdown('<p class="sec-title">Route & Traffic Profile</p>', unsafe_allow_html=True)
            if best_route:
                route_color = "#10B981" if best_route.get("congestion_level") == "CLEAR" else "#F59E0B" if best_route.get("congestion_level") == "MODERATE" else "#EF4444"
                c = f'<div class="card" style="border-color:{route_color};">'
                c += f'<div style="font-size:16px;font-weight:700;color:#e6edf3;margin-bottom:10px;">Road Route Summary</div>'
                
                def kv(label, val, vc="#c9d1d9"):
                    return f'<div class="kv-row"><span class="kv-label">{label}</span><span style="color:{vc};font-weight:500;">{val}</span></div>'
                
                c += kv("Destination", dest.get("name", "Noida Sector 18"))
                c += kv("Road Distance", f'{best_route.get("distance_km","—")} km')
                c += kv("Dynamic Road ETA", format_eta(best_route.get("duration_minutes",0)))
                c += kv("Free-flow Time", format_eta(best_route.get("base_duration_minutes",0)))
                c += kv("Estimated Delay", f'{best_route.get("traffic_delay_minutes",0):.0f} minutes', route_color)
                c += kv("Traffic Status", best_route.get("congestion_level", "—"), route_color)
                c += kv("Routing Engine", best_route.get("source","—"))
                c += f'<div style="font-size:10px;color:#8b949e;padding-top:6px;">Calculated live turn-by-turn road geometries without API keys.</div>'
                c += '</div>'
                st.markdown(c, unsafe_allow_html=True)
        else:
            st.markdown('<p class="sec-title">Selected Dispatch Candidate</p>', unsafe_allow_html=True)
            if sel:
                fl = sel.get("fuel_level", 0)
                fclr = get_fuel_color(fl)
                vtype = sel.get("vehicle_type","").replace("_"," ").title()
                c = f'<div class="card" style="border-color:#238636;">'
                c += f'<div style="font-size:16px;font-weight:700;color:#e6edf3;margin-bottom:10px;">{sel.get("vehicle_id")} <span style="font-size:10px;color:#238636;font-weight:600;margin-left:8px;text-transform:uppercase;">Optimal Selection</span></div>'
                
                def kv(label, val, vc="#c9d1d9"):
                    return f'<div class="kv-row"><span class="kv-label">{label}</span><span style="color:{vc};font-weight:500;">{val}</span></div>'
                
                c += kv("Driver", sel.get("driver_name","—"))
                c += kv("Type", vtype)
                c += kv("Fuel Level", f'{fl}%', fclr)
                c += kv("Capacity Weight", f'{sel.get("capacity_tons","—")} tons')
                c += kv("Operational Status", sel.get("status","—").title())
                c += kv("Mileage Profile", f'{sel.get("mileage_kmpl","—")} km/l')
                c += kv("Contact Details", sel.get("contact","—"))
                c += kv("Last Service", sel.get("last_service_date","—"))
                c += f'<div style="font-size:10px;color:#8b949e;padding-top:6px;">Current Area: {sel.get("location_name","")}</div>'
                
                if best_route:
                    c += '<div style="margin-top:10px;padding:10px;background:#161b22;border-radius:6px;">'
                    c += kv("Distance to Location", f'{best_route.get("distance_km","—")} km')
                    c += kv("Dynamic ETA", format_eta(best_route.get("duration_minutes",0)))
                    c += kv("Free-flow ETA", format_eta(best_route.get("base_duration_minutes",0)))
                    c += kv("Estimated Delay", f'{best_route.get("traffic_delay_minutes",0):.0f} minutes')
                    c += kv("Routing Engine", best_route.get("source","—"))
                    c += '</div>'
                c += '</div>'
                st.markdown(c, unsafe_allow_html=True)

            if ranked:
                best_scores = ranked[0].get("scores", {})
                if best_scores:
                    st.markdown('<p class="sec-title" style="margin-top:12px;">Candidate Performance Indicators</p>', unsafe_allow_html=True)
                    s = '<div class="card">'
                    for label, key, mx in [("ETA Score","eta_score",35),("Fuel Score","fuel_score",30),("Capacity","capacity_score",20),("Traffic","traffic_score",15)]:
                        val = best_scores.get(key, 0)
                        pct = int(val/mx*100)
                        clr = "#238636" if pct >= 75 else "#d29922" if pct >= 40 else "#da3633"
                        s += f'<div style="margin-bottom:8px;"><div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:3px;"><span class="kv-label">{label}</span><span style="color:{clr};">{val}/{mx}</span></div><div class="health-bar"><div style="width:{pct}%;height:100%;background:{clr};border-radius:2px;"></div></div></div>'
                    st.markdown(s + "</div>", unsafe_allow_html=True)

        st.markdown('<p class="sec-title" style="margin-top:12px;">Traffic Analytics Profile</p>', unsafe_allow_html=True)
        if traffic_data:
            cong2 = traffic_data.get("congestion_level","N/A")
            sev   = traffic_data.get("severity_score", 0)
            cclr2 = get_congestion_color(cong2)
            advice = traffic_data.get("routing_advice", [])
            t = '<div class="card">'
            t += f'<div class="kv-row"><span class="kv-label">Condition</span><span style="color:{cclr2};font-weight:600;">{cong2}</span></div>'
            t += f'<div class="kv-row"><span class="kv-label">Congestion Severity</span><span style="color:#c9d1d9;">{sev}/100</span></div>'
            t += f'<div class="kv-row"><span class="kv-label">Accumulated Delay</span><span style="color:#c9d1d9;">{traffic_data.get("traffic_delay_minutes",0):.0f} minutes</span></div>'
            t += f'<div style="margin:8px 0;background:#21262d;border-radius:2px;height:3px;"><div style="width:{sev}%;height:100%;background:{cclr2};border-radius:2px;"></div></div>'
            for a in advice[:3]:
                clean_a = a.encode("ascii","ignore").decode().strip().replace("?", "")
                t += f'<div style="font-size:11px;color:#8b949e;padding:2px 0;">{clean_a}</div>'
            t += '</div>'
            st.markdown(t, unsafe_allow_html=True)

else:
    # Default Dashboard View
    st.markdown('<p class="sec-title">Delhi NCR Hub Overview Map</p>', unsafe_allow_html=True)
    default_map = create_fleet_map(vehicles=all_v, zoom_start=10)
    st_folium(default_map, width=None, height=520, returned_objects=[])
    st.markdown("""
    <div style="text-align:center;padding:28px 0;">
        <div style="font-size:14px;color:#8b949e;margin-bottom:5px;">Enter a query in the console to evaluate fleet routing</div>
        <div style="font-size:12px;color:#484f58;">The agent evaluates candidates globally using dynamic address resolving. Try "Which vehicle can reach Jaipur fastest".</div>
    </div>
    """, unsafe_allow_html=True)
