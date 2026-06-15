# SyncUp Job Platform 🚀

A scalable, real-time, **AI-powered job matching and applicant screening platform**. Built using a multi-agent orchestration architecture to automate resume parsing, applicant tracking (ATS) scoring, and context-aware recruitment Q&A.

## 🌟 Key Features

* **AI Resume Parsing & Autofill:** Upload a resume (PDF) and instantly extract a highly structured candidate profile (skills, education, experience) via an LLM.
* **Smart ATS Scoring:** Evaluates candidates against specific job descriptions to compute objective fit percentages and identify critical skill gaps.
* **Real-time Notifications:** Instant, bi-directional asynchronous updates using **Socket.IO** (e.g., notifying the frontend the moment a background AI analysis completes).
* **AI Knowledge Assistant (RAG):** Context-aware chatbot widget built with **Qdrant Vector Database** and **Gemini Embeddings** to answer user queries using domain-specific markdown files.
* **Secure Cloud Storage:** Robust integration with **AWS S3** for resume storage.
* **Production-Grade Worker Queues:** Event-driven background processing using **Redis Streams** with Dead Letter Queue (DLQ) routing, latency tracking, and exponential backoff.

---

## 🏗️ System Architecture

The project is structured into three highly decoupled tiers:

### 1. Frontend (`/frontend`)
* **Framework:** Next.js 16 (App Router)
* **Styling:** Tailwind CSS v4
* **Interactivity:** Real-time Socket.IO client, drag-and-drop resume uploading, dynamic ATS scoring dashboards.

### 2. API Gateway / BFF (`/backend`)
* **Framework:** Node.js & Express
* **Database:** MongoDB (Candidate profiles, Job posts, Application states)
* **Auth:** JWT-based user authentication
* **Role:** Acts as the Backend-for-Frontend (BFF), managing AWS S3 file uploads and publishing heavy AI tasks to the Redis Message Broker.

### 3. AI Core Microservice (`/ai-service`)
* **Framework:** Python FastAPI
* **Multi-Agent System:** Employs specialized, isolated agents (e.g., `ResumeAgent`, `ATSAgent`, `RecruiterAgent`) adhering to strict Pydantic validation schemas.
* **Orchestration:** Consumes events from Redis Streams via custom async worker loop (`base_worker.py`).
* **Vector Database:** Integrates **Qdrant** (with built-in `:memory:` fallback) to index and query document embeddings.

---

## 🛠️ Tech Stack Overview

| Category | Technologies |
|---|---|
| **Frontend** | Next.js, React, Tailwind CSS |
| **Backend** | Node.js, Express, Socket.IO |
| **AI / Python** | FastAPI, Pydantic, Tenacity (retries) |
| **LLM Providers**| Google Gemini, Azure OpenAI |
| **Databases** | MongoDB, Redis (Streams/Cache), Qdrant (Vector) |
| **Cloud** | AWS S3 |

---

## 🚀 Running the Project Locally

### Prerequisites
* Node.js (v18+)
* Python 3.10+
* MongoDB URI
* Redis Instance
* AWS Credentials & S3 Bucket
* Gemini API Key

### 1. Start the Backend (API Gateway)
```bash
cd backend
npm install
npm run dev
```

### 2. Start the AI Microservice
```bash
cd ai-service
pip install -r requirements.txt
# Set your Gemini / Qdrant environment variables in .env
python -m uvicorn api.app:app --host 127.0.0.1 --port 8001
```

### 3. Start the Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 🧠 AI Agent Design Patterns Used
* **Dependency Injection:** Agents interface strictly through an `LLMProvider` abstraction, making it easy to swap models.
* **Monadic Error Handling:** The system relies on an `AgentResult` object wrapper (Success/Failure states) rather than bubbling unhandled exceptions.
* **RAG Auto-Indexing:** The platform automatically parses, chunks, and indexes local knowledge base files on application boot.

---

*Designed and developed as an advanced showcase of multi-agent LLM orchestration, scalable event queues, and modern Full-Stack engineering.*
