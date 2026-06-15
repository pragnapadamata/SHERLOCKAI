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

# ⚙ Installation

## Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

## Frontend

```bash
cd frontend

npm install

npm run dev
```

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

