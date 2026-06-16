# 🏭 Tata Steel Autonomous Plant Intelligence System (Sherlock)

## 🚀 Overview

Sherlock (Autonomous Plant Intelligence System) is a multi-agent AI platform designed to help steel plants reduce downtime, improve safety, optimize energy consumption, and support executive decision-making.

The system leverages LangGraph-based AI agents, live operational simulations, and an enterprise-grade dashboard to transform raw plant data into actionable intelligence.

Built as a hackathon solution for Tata Steel.

---

# 🎯 Problem Statement

Modern steel plants generate enormous amounts of operational data from:

* Equipment sensors
* Safety monitoring systems
* Maintenance logs
* Production systems
* Energy consumption trackers

Organizations face challenges such as:

* Unexpected equipment failures
* Worker safety incidents
* Rising energy costs
* Production bottlenecks
* Slow management reporting

Sherlock addresses these challenges using AI-powered autonomous agents and intelligent analytics.

---

# ✨ Key Features

## Multi-Agent AI Architecture

### Supervisor Agent

Routes queries to the most relevant expert agents.

### Maintenance Agent

Predictive maintenance recommendations and failure analysis.

### Safety Agent

Risk assessment and safety incident analysis.

### Energy Agent

Energy optimization and efficiency recommendations.

### Production Agent

Production planning and bottleneck identification.

### Reporting Agent

Executive summaries and automated reporting.

---

## Predictive Maintenance

### Inputs

* Vibration
* Temperature
* Pressure

### Outputs

* Failure probability
* Recommended actions
* Confidence score
* Expected impact

---

## Safety Monitoring

### Inputs

* Incident reports
* Sensor alerts

### Outputs

* Risk score
* Preventive actions
* Safety recommendations

---

## Energy Optimization

### Inputs

* Plant energy consumption

### Outputs

* Optimization recommendations
* Estimated savings
* Efficiency metrics

---

## Production Planning

### Outputs

* Scheduling suggestions
* Bottleneck detection
* Production KPIs

---

## Executive Dashboard

The dashboard provides:

* Active Alerts
* Downtime Prediction
* Safety Score
* Energy Score
* Production KPIs
* Plant Health Monitoring
* Live Operational Metrics

---

## AI Assistant

Users can interact with the system using natural language.

### Example Queries

* Why is Plant B at risk?
* How can we reduce energy consumption?
* Show production bottlenecks.
* Generate executive report.

Each response includes:

* Recommendation
* Confidence Score
* Reasoning
* Expected Impact

---

## Live Sensor Simulation

Features include:

* Real-time sensor updates
* Alert generation
* Live KPI changes
* Industrial event simulation

---

## PDF Executive Reports

Generate board-ready reports containing:

* KPI Summary
* Executive Insights
* Recommendations
* Plant Status Overview
* Timestamped Reports

---

# 🏗 Architecture

```text
User
 │
 ▼
Next.js Frontend
 │
 ▼
FastAPI Backend
 │
 ▼
LangGraph Supervisor Agent
 │
 ├── Maintenance Agent
 ├── Safety Agent
 ├── Energy Agent
 ├── Production Agent
 └── Reporting Agent
 │
 ▼
Gemini API
 │
 ▼
Recommendations & Insights
```

---

# 🛠 Technology Stack

## Frontend

* Next.js 15
* TypeScript
* TailwindCSS
* ShadCN UI
* Recharts

## Backend

* FastAPI
* Python

## AI

* LangGraph
* Gemini API

## Database

* PostgreSQL Ready Architecture

## Reporting

* ReportLab

---

# 📂 Project Structure

```text
tata-steel-apis/
│
├── backend/
│   ├── app/
│   ├── agents/
│   ├── api/
│   ├── services/
│   └── data/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── app/
│   └── lib/
│
├── docs/
│
└── README.md
```

---

# ⚙️ Installation & Running the Project

You can run the project either locally (recommended for development) or using Docker Compose.

---

## Prerequisites

- **Python 3.9+** (if running locally)
- **Node.js 18+** (if running locally)
- **Docker & Docker Compose** (if running via Docker)
- **Gemini API Key**: An active Gemini API key is required for the LLM agents to function.

### 🔑 Environment Setup

1. **Backend Env Setup**:
   - Navigate to the `backend/` directory.
   - Copy the template file to `.env` (e.g., `cp .env.example .env`).
   - Open `.env` and fill in your **`GEMINI_API_KEY`**:
     ```env
     GEMINI_API_KEY=your_actual_gemini_api_key_here
     ```
2. **Frontend Env Setup** (Optional):
   - Navigate to the `frontend/` directory.
   - Create a `.env.local` file with the backend API URL (already defaulted to `http://localhost:8000`):
     ```env
     NEXT_PUBLIC_API_URL=http://localhost:8000
     ```

---

## Option A: Run Locally (Recommended)

### 1. Start the Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On macOS/Linux:
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the FastAPI server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
The backend API will be running at [http://localhost:8000](http://localhost:8000).

### 2. Start the Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   ```
The frontend will be running at [http://localhost:3000](http://localhost:3000).

---

## Option B: Run with Docker Compose

If you prefer to run both backend and frontend in containerized environments:

1. Make sure you have created the `backend/.env` file with your `GEMINI_API_KEY`.
2. In the root directory of the project, run:
   ```bash
   docker compose up --build
   ```
3. Once the containers are built and running:
   - **Frontend**: Accessible at [http://localhost:3001](http://localhost:3001) (mapped from port 3000 inside the container).
   - **Backend**: Accessible at [http://localhost:8000](http://localhost:8000).

---

# 🔐 Demo Login

Email:

```text
admin@tatasteel.com
```

Password:

```text
TataSteel@2025
```

---

# 📊 Demo Workflow

1. Login to Sherlock
2. Open Dashboard
3. Trigger a live event using:

   * Equipment Failure
   * Gas Leak
   * Energy Surge
4. Open AI Assistant
5. Ask operational questions
6. Generate Executive PDF Report

---

# 🌟 Future Scope

* Real IoT Integration
* SAP/ERP Connectivity
* Mobile Application
* Advanced Predictive Analytics
* Cloud Deployment
* Digital Twin Integration

---

# 👨‍💻 Team

Tata Steel Hackathon Submission

Autonomous Plant Intelligence System (Sherlock)

Built using AI, LangGraph, FastAPI, Next.js, and Gemini.

