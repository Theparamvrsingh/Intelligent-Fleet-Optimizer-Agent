# 🚛 Intelligent Fleet Operations Agent

> **Interview-Ready Agentic AI Project** — LangGraph + Gemini + HERE APIs + Streamlit

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.0.55-green)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/Google-Gemini_1.5_Flash-orange)](https://ai.google.dev/)
[![HERE](https://img.shields.io/badge/HERE-Routing_API_v8-cyan)](https://developer.here.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red)](https://streamlit.io)

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INTERFACE (Streamlit)                │
│   Query Input → Agent Response → Map → Cards → Thinking Log │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              LANGGRAPH AGENT (Single-Agent)                  │
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
│  fleet_data.json │                │   HERE Routing API v8  │
│  (12 vehicles,   │                │   • Distance & ETA     │
│   Delhi NCR)     │                │   • Traffic delays     │
└──────────────────┘                │   • Congestion levels  │
                                    └───────────────────────┘
                                                │
                                                ▼
                                    ┌───────────────────────┐
                                    │  Google Gemini 1.5     │
                                    │  Flash (Synthesis)     │
                                    └───────────────────────┘
```

---

## 🔄 Agent Workflow Diagram

```
User Query
    │
    ▼
┌─────────────────────┐
│  Step 1: Intent     │  Classify: eta_lookup / optimization /
│  Understanding      │  traffic_analysis / fleet_lookup
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 2: Fleet      │  Tool: fleet_lookup_tool
│  Data Fetch         │  Reads: fleet_data.json (ground truth)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 3: HERE       │  Tool: here_routing_tool
│  Routing API        │  Returns: distance, ETA, polyline
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 4: Traffic    │  Tool: traffic_analysis_tool
│  Analysis           │  Returns: congestion, hotspots, advice
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 5: Fleet      │  Tool: fleet_optimization_tool
│  Optimization       │  Scores: ETA(35) + Fuel(30) + Cap(20) + Traffic(15)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Step 6: Gemini     │  Synthesizes ALL tool outputs into
│  Response Gen       │  natural language recommendation
└────────┬────────────┘
         │
         ▼
  Final Answer + UI Cards
```

---

## 🛠️ Tech Stack

| Technology | Purpose | Why Chosen |
|-----------|---------|-----------|
| **LangGraph** | Agent orchestration | Stateful multi-step reasoning with observable nodes |
| **Google Gemini 1.5 Flash** | Language model | Fast, capable, multimodal, free tier available |
| **HERE Routing API v8** | Route & ETA | Enterprise-grade, truck-specific routing, traffic-aware |
| **Streamlit** | Frontend | Rapid enterprise dashboards with Python only |
| **Folium** | Map visualization | Interactive Leaflet maps inside Streamlit |
| **Python** | Core language | Ecosystem for AI/ML, data, and APIs |

---

## 📁 Project Structure

```
intelligent-fleet-agent/
│
├── app.py                      # Streamlit enterprise dashboard (main entry)
├── fleet_data.json             # 12-vehicle Delhi NCR dataset
├── requirements.txt            # Python dependencies
├── .env                        # API keys (not committed)
├── README.md                   # This file
│
├── agents/
│   ├── __init__.py
│   └── fleet_agent.py          # LangGraph 6-node agent pipeline
│
├── tools/
│   ├── __init__.py
│   ├── fleet_lookup.py         # Tool 1: Fleet data reader
│   ├── here_routing.py         # Tool 2: HERE Routing API v8
│   ├── fleet_optimizer.py      # Tool 3: Multi-criteria optimizer
│   └── traffic_analysis.py     # Tool 4: Traffic analysis & hotspots
│
├── services/
│   ├── __init__.py
│   └── map_service.py          # Folium map generation
│
└── utils/
    ├── __init__.py
    └── ui_helpers.py           # HTML card generators for Streamlit
```

---

## 🚀 Setup Instructions

### 1. Clone & Navigate
```bash
cd "Intelligent Fleet Operations Agent"
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
# or
venv\Scripts\activate         # Windows
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Keys
Edit `.env` file:
```env
GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here
HERE_API_KEY=your_here_api_key_here
```

### 5. Run the App
```bash
streamlit run app.py
```

---

## 🔑 HERE API Setup

1. Go to [developer.here.com](https://developer.here.com)
2. Create a free account (250,000 free requests/month)
3. Go to **Projects → Create Project**
4. Generate an **API Key** (REST)
5. Paste it in `.env` as `HERE_API_KEY`

> **Without HERE API key**: The app runs with a synthetic routing fallback using Haversine distance + realistic traffic multipliers. All features work — just with estimated data.

---

## 🔑 Gemini API Setup

1. Go to [aistudio.google.com](https://aistudio.google.com)
2. Click **Get API Key → Create API Key**
3. Paste it in `.env` as `GOOGLE_GEMINI_API_KEY`

> **Without Gemini API key**: The agent falls back to a rule-based response synthesizer. All tools still run normally.

---

## 💡 Sample Queries

```
"Which vehicle should deliver Order 123?"
"Which vehicle can reach Noida Sector 18 fastest?"
"What is the ETA of Vehicle V101 to the airport?"
"Which route avoids traffic to Gurugram?"
"Recommend the best vehicle for a 4-ton delivery to Faridabad"
"Where is V104 right now?"
"Show fleet status"
```

---

## 🎯 Interview Talking Points

### Why Agentic AI?
> A traditional rule-based system would pick the nearest vehicle blindly. The agent **reasons** about fuel, traffic, vehicle capacity, and route congestion simultaneously — synthesizing them into an optimal decision. This mirrors how a real fleet manager thinks.

### Why LangGraph?
> LangGraph provides **stateful, observable, multi-step reasoning** as a directed graph. Each node is a discrete reasoning step with its own inputs/outputs. Unlike a single LLM call, the agent can call multiple tools in sequence, maintain state between steps, and produce explainable decisions.

### Why HERE APIs?
> HERE provides **enterprise-grade routing** with real-time traffic, truck-specific restrictions (weight, height limits), and historical traffic patterns. This is the industry standard used by DHL, FedEx, and logistics companies worldwide.

### Why Tool Calling?
> Tool calling prevents **hallucination** of fleet data. Instead of the LLM making up vehicle IDs and ETAs, it is *forced* to call real tools that read from the JSON database and the HERE API. The LLM only synthesizes — it never fabricates data.

---

## 🔮 Future Scope

| Feature | Description |
|---------|-------------|
| **Multi-Agent Architecture** | Separate agents for routing, scheduling, and driver management coordinating via LangGraph's multi-agent framework |
| **Real GPS Integration** | Replace `fleet_data.json` with live GPS telemetry via MQTT/WebSocket from actual vehicle devices |
| **Live Vehicle Telemetry** | Engine health, tire pressure, fuel consumption streaming from IoT sensors |
| **Predictive Fleet Analytics** | ML models predicting maintenance needs, fuel consumption, and delivery delays before they occur |
| **Autonomous Logistics Control Center** | Fully autonomous agent that dispatches, reroutes, and reschedules without human intervention |
| **Voice Interface** | Natural language voice queries using Whisper + TTS for hands-free fleet management |
| **Multi-City Operations** | Scale from Delhi NCR to pan-India fleet management with city-specific traffic models |

---

## 📊 Agent Observability

The UI displays a real-time **Agent Thinking Process** panel showing:

- ✅ Step 1: Understanding User Intent
- ✅ Step 2: Fetching Fleet Data  
- ✅ Step 3: Calling HERE Routing API
- ✅ Step 4: Traffic Analysis
- ✅ Step 5: Fleet Optimization
- ✅ Step 6: Generating Recommendation

Each step shows which tool was called and what it returned — full **end-to-end observability** of the agent's reasoning chain.

---

*Built for interview demonstration of Agentic AI, Tool Calling, and Enterprise Logistics Systems.*
