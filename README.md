# 🏭 Sherlock – Autonomous Plant Intelligence System

## 🚀 Overview

Sherlock is an AI-powered Autonomous Plant Intelligence System designed to help steel manufacturing facilities improve operational efficiency, enhance workplace safety, reduce downtime, and optimize energy consumption. Modern industrial plants generate massive volumes of data from equipment sensors, maintenance systems, safety monitoring infrastructure, production lines, and energy management platforms. While this data contains valuable insights, extracting actionable intelligence from it remains a significant challenge.

Built as a Tata Steel hackathon solution, Sherlock transforms raw operational data into meaningful recommendations through a multi-agent AI architecture powered by LangGraph and Gemini. The platform enables engineers, plant operators, and executives to make faster and more informed decisions by providing predictive insights, operational intelligence, and automated reporting through a unified dashboard experience.

---

## 🎯 Problem Statement

Steel manufacturing plants operate in highly complex environments where unexpected equipment failures, safety incidents, energy inefficiencies, and production bottlenecks can lead to significant operational and financial losses. Traditional monitoring systems often provide large amounts of data but lack the intelligence required to proactively identify risks and recommend corrective actions.

Sherlock addresses these challenges by leveraging autonomous AI agents that continuously analyze plant operations, detect anomalies, assess risks, and generate actionable recommendations. By shifting organizations from reactive problem-solving to proactive decision-making, the platform helps improve reliability, productivity, and overall plant performance.

---

## ✨ Key Features

* Multi-agent AI architecture for specialized operational intelligence
* Predictive maintenance and equipment failure analysis
* Safety monitoring and risk assessment
* Energy optimization and efficiency recommendations
* Production planning and bottleneck detection
* Executive dashboard with real-time KPIs
* Conversational AI assistant for natural language queries
* Live operational and industrial event simulation
* Automated executive PDF report generation

---

## 🤖 Multi-Agent Intelligence

At the core of Sherlock is a LangGraph-powered multi-agent system. A Supervisor Agent coordinates interactions between specialized agents responsible for maintenance, safety, energy, production, and reporting functions. Each agent focuses on a specific operational domain, enabling deeper analysis and more accurate recommendations than a traditional single-model approach.

This architecture allows users to interact with the platform naturally while receiving expert-level insights tailored to different areas of plant operations.

---

## 📊 Executive Dashboard

Sherlock provides a centralized operational dashboard that offers complete visibility into plant performance. The dashboard consolidates critical metrics such as active alerts, downtime predictions, safety indicators, energy efficiency scores, production KPIs, and overall plant health into a single interface.

By presenting operational intelligence in real time, the platform enables stakeholders to quickly identify emerging issues and make informed decisions before problems impact production.

---

## 💬 AI Assistant

The platform includes a conversational AI assistant that allows users to interact with operational data using natural language. Engineers and managers can ask questions such as:

* Why is Plant B at risk?
* How can we reduce energy consumption?
* Show current production bottlenecks.
* Generate an executive report.

Each response includes AI-generated recommendations, supporting reasoning, confidence scores, and expected business impact, making complex operational analysis accessible to both technical and non-technical users.

---

## 📡 Operational Simulation

To demonstrate real-world industrial scenarios, Sherlock includes a live simulation environment capable of generating operational events and sensor updates. Users can simulate equipment failures, gas leaks, and energy surges while observing how the system detects issues, generates alerts, and updates key performance indicators in real time.

This simulation layer showcases the platform's ability to respond intelligently to dynamic plant conditions and provides a realistic representation of production environments.

---

## 📄 Automated Reporting

Sherlock simplifies executive communication by automatically generating professional PDF reports containing KPI summaries, operational insights, strategic recommendations, and plant status overviews. These reports are designed for management reviews and board-level presentations, significantly reducing the effort required to prepare operational updates.

---

## 🏗 Architecture

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

## 🛠 Technology Stack

### Frontend

* Next.js 15
* TypeScript
* Tailwind CSS
* ShadCN UI
* Recharts

### Backend

* FastAPI
* Python

### AI & Agents

* LangGraph
* Gemini API

### Database

* PostgreSQL Ready Architecture

### Reporting

* ReportLab

---

## 📂 Project Structure

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

## ⚙️ Installation

### Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

---

## 🌟 Future Scope

* Real-time IoT integration
* SAP and ERP connectivity
* Mobile application support
* Advanced predictive analytics
* Cloud-native deployment
* Digital twin integration
* Multi-plant operational intelligence

---

## 👨‍💻 Team

Developed as a submission for the Tata Steel Hackathon.

Sherlock demonstrates how multi-agent AI systems can transform industrial operations by combining predictive maintenance, safety intelligence, energy optimization, production analytics, and executive reporting into a single intelligent platform for modern manufacturing environments.
