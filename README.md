# Intelligent Fleet Operations Agent

An enterprise-grade, agentic AI logistics orchestration system built on LangGraph, Google Gemini, and OpenStreetMap (OSRM) services. The system features a custom-built dynamic routing optimization engine and an interactive Streamlit console to coordinate fleet logistics, manage real-world road congestion delays, and automate vehicle dispatching.

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Streamlit)                │
│   Query Input → Agent Response → Map → Cards → Thinking Log │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH AGENT (Stateful Execution)            │
│                                                             │
│  [understand_intent] → [fetch_fleet] → [call_routing]       │
│        → [analyze_traffic] → [optimize_fleet]               │
│              → [generate_answer]                            │
│                                                             │
│  State flows through every node (TypedDict AgentState)      │
└──────────┬────────────────────────────────────┬────────────┘
           │                                    │
           ▼                                    ▼
┌──────────────────┐                ┌───────────────────────┐
│  fleet_data.json │                │   OSRM Routing API    │
│  (12 vehicles,   │                │   • Distance & ETA     │
│   Delhi NCR)     │                │   • Traffic delays     │
│                  │                │   • Congestion levels  │
└──────────────────┘                └───────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │   Google Gemini 1.5   │
                                    │   Flash (Synthesis)   │
                                    └───────────────────────┘
```

---

## Agent Workflow Execution Flow

```
User Query
    │
    ▼
┌─────────────────────┐
│  Step 1: Intent     │  Classify: eta_lookup / proximity_lookup /
│  Understanding      │  traffic_analysis / fleet_lookup
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 2: Fleet      │  Tool: fleet_lookup_tool
│  Data Fetch         │  Reads: fleet_data.json (ground truth dataset)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 3: OSRM       │  Tool: osrm_routing_tool
│  Routing API        │  Returns: Real-road distance, ETA, polyline
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 4: Traffic    │  Tool: traffic_analysis_tool
│  Analysis           │  Returns: Congestion thresholds, highway hotspots
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 5: Fleet      │  Tool: fleet_optimization_tool
│  Optimization       │  Processes routing matrix and filters by proximity
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 6: Gemini     │  Synthesizes tool outputs into structured
│  Response Gen       │  dispatch recommendations and reasoning
└────────┬────────────┘
         │
         ▼
   Final Answer + UI Map Rendering
```

---

## Technology Stack

| Component | Technology | Purpose | Implementation Context |
|-----------|------------|---------|------------------------|
| **Agent Orchestration** | LangGraph | Stateful multi-step reasoning | Graph-based control flow with node-level state modification |
| **Generative Model** | Google Gemini 1.5 Flash | Natural language synthesis | Reasoning, semantic intent extraction, response synthesis |
| **Routing Engine** | OSRM (OpenStreetMap) | Real-road routing and distance | Live road network ETAs, travel distances, and shape polylines |
| **Geocoding Engine** | Nominatim (OpenStreetMap) | Dynamic address geocoding | High-accuracy coordinate lookup restricted to Indian boundaries |
| **Web UI Console** | Streamlit | Frontend interface dashboard | Sleek dark-mode console displaying mapping canvas and log telemetry |
| **Mapping Engine** | Folium | Interactive Leaflet canvas | Real-time map layers, color-coded road paths, and custom pins |

---

## Repository Structure

```
intelligent-fleet-agent/
│
├── app.py                      # Main Streamlit dashboard application
├── fleet_data.json             # 12-vehicle Delhi NCR fleet database
├── requirements.txt            # Python dependencies
├── .env                        # Local credentials configuration (git-ignored)
├── README.md                   # Project documentation
├── deployment_guide.md         # Deployment and cloud hosting instructions
│
├── agents/
│   ├── __init__.py
│   └── fleet_agent.py          # LangGraph state workflow definition
│
├── tools/
│   ├── __init__.py
│   ├── fleet_lookup.py         # Retrieves static vehicle metrics
│   ├── here_routing.py         # Coordinates OSRM and Nominatim lookups
│   ├── fleet_optimizer.py      # Executes multi-criteria ranking
│   └── traffic_analysis.py     # Models real-time traffic delay metrics
│
├── services/
│   ├── __init__.py
│   └── map_service.py          # Generates Folium maps with road polylines
│
└── utils/
    ├── __init__.py
    └── ui_helpers.py           # Generates HTML component styling cards
```

---

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Theparamvrsingh/Intelligent-Fleet-Optimizer-Agent.git
cd Intelligent-Fleet-Optimizer-Agent
```

### 2. Configure a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Environment Variables
Create a `.env` file in the root directory:
```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
```

### 5. Launch the Dashboard
```bash
streamlit run app.py
```

---

## Model API Configuration

### Gemini API Integration
1. Obtain an API Key from the Google AI Studio console: [aistudio.google.com](https://aistudio.google.com)
2. Assign the key inside your `.env` configuration as `GOOGLE_GEMINI_API_KEY`.
3. In the event of API outages or missing credentials, the framework automatically engages a rule-based synthesis fallback to maintain system availability.

---

## Sample Operations Console Queries

The conversational dispatcher handles complex natural language queries, including:

```
"Which vehicle should deliver Order 123?"
"Which vehicle can reach Noida Sector 18 fastest?"
"What is the ETA of Vehicle V101 to Chandigarh?"
"Recommend the best vehicle for a 4-ton delivery to Faridabad"
"Determine the distance and traffic from Bennett University to Chandigarh"
"Show status logs for V104"
"Display current fleet status dashboard"
```

---

## Core System Architectural Principles

### Stateful Graph Reasoning
Rule-based systems typically select resources based on simple Euclidean straight-line distance. This agent operates on a stateful graph where routing constraints, live capacity thresholds, actual road network travel times, and congestion multipliers are processed sequentially, generating optimal dispatch recommendations.

### Safe Declarative Tool Binding
The agent relies on restricted tool calling to prevent hallucination of fleet parameters. By enforcing declarative tool inputs, the core model is barred from inventing non-existent vehicle IDs, coordinates, or fuel logs. The generative model acts solely as an analytical coordinator rather than a data generator.

### Unified Proximity Dispatch
Dispatch queries seeking the "closest" or "fastest" assets are prioritized using pure OSRM road travel times and path distances. This approach resolves routing errors where global scores outranked physically proximal assets.

### Point-to-Point Custom Routing
The agent parses custom routing queries between arbitrary points (e.g. Bennett to Chandigarh) directly, setting custom map frames, calculating high-accuracy distance segments, and applying live time-of-day traffic congestion models without coupling calculations to the fleet database.

---

## Agent Observability Telemetry

The operations dashboard exposes a live telemetry drawer detailing every logical hop of the model's reasoning chain:

- Step 1: Parsing user query intent and extracting target entities.
- Step 2: Querying fleet databases to identify eligible vehicles.
- Step 3: Resolving road geometry paths and ETAs via OSRM.
- Step 4: Assessing structural congestion and computing delay metrics.
- Step 5: Invoking multi-criteria search algorithms to score candidate assets.
- Step 6: Compiling execution parameters and rendering final outputs.

Each reasoning node provides full observability of input variables, execution durations, and returned payloads.
