# Two-Agent Concierge & Booking System (LangGraph)

This repository contains a production-ready, two-agent conversational system built with **LangGraph** for guided discovery, qualification, and booking workflows.

The system is designed to move users from initial exploration to a qualified handoff or scheduled call, while reliably capturing contact information and preferences.

---

## Overview

The application orchestrates two specialized agents using a LangGraph state machine:

* A **Concierge Agent** for discovery and high-level guidance
* A **Listing + Booking Agent** for deep dives, scheduling, and lead capture

All agent transitions, tool calls, and state changes are observable and debuggable in **LangGraph Studio**.

---

## Agent Architecture

### 1. Concierge Agent (Agent 1)

Responsibilities:

* Greets users and sets context
* Browses, lists, and searches available offerings
* Answers high-level questions
* Always offers an expert or advisor connection
* Hands off to the Listing/Booking Agent when the user shows interest in a specific item or requests deeper details

Key behaviors:

* Concise responses
* Smart lookup by ID or fuzzy name match
* Explicit handoff when intent is detected

---

### 2. Listing + Booking Agent (Agent 2)

Responsibilities:

* Provides detailed information
* Offers two clear calls to action:

  1. Schedule a call (e.g. via cal.com)
  2. Get connected to an expert or advisor
* Captures user contact information and preferences
* Submits qualified leads to an external system via webhook

Lead capture rule:

* The moment the system has **name + (email OR phone)**, it triggers the webhook
* Optional preferences (timeline, budget, category) are included when available

---

## Lead Capture & Webhook Integration

When a user is qualified:

1. Contact information is normalized and lightly validated
2. Item identifiers are resolved via smart lookup
3. The appropriate expert or advisor is associated
4. A POST request is sent to the configured webhook endpoint
5. The user is notified that the handoff is complete

### Webhook Configuration

The webhook endpoint is configured via environment variable:

```env
WEBHOOK_URL=...
```

It is used by:

* `send_to_webhook()`
* Called from `capture_contact_info()`

---

## Project Structure

```
.
├── graph.py              # LangGraph state machine, agents, routing
├── listings.py           # Item data, summaries, advisor mappings
├── .env.example          # Environment variable template
├── README.md             # Project documentation
```

Key components:

* **StateGraph** defines agent flow and routing
* **ToolNodes** expose search, booking, and lead capture actions
* **Smart lookup** resolves items by ID or fuzzy name match
* **Webhook integration** submits qualified leads externally

---

## Getting Started

### 1. Install dependencies

```bash
pip install -e . "langgraph-cli[inmem]"
```

---

### 2. Environment setup

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
WEBHOOK_URL=https://example.com/webhook
LANGSMITH_API_KEY=lsv2...   # optional
```

---

### 3. Run the LangGraph server

```bash
langgraph dev
```

Open **LangGraph Studio** to:

* Visualize agent transitions
* Inspect tool calls
* Replay and edit past states
* Debug webhook-triggering conditions

---

## Development & Debugging

* Hot reload applies local code changes automatically
* Past conversation states can be edited and re-run
* Tool usage and routing decisions are fully observable
* Optional LangSmith integration enables deeper tracing and collaboration

---

## Extending the System

Common extensions:

* Add richer user qualification (budget, geography, timeline)
* Introduce seller or provider-side intake flows
* Add lead scoring or prioritization
* Swap the webhook target for a CRM or database
* Add async follow-ups or reminders
* Split agents and tools into separate modules as the system grows

---

## 🚩 Feature Flags (Production Ready)
   
   This demo includes a production-grade feature flag system for:
   - A/B testing agent behavior
   - Gradual rollout (10% → 100%)
   - Kill switches
   - Per-user targeting
   
   See [README_FEATURE_FLAGS.md](README_FEATURE_FLAGS.md) for details.
   
   **Quick start:**
```bash
   export FF_AGGRESSIVE_CAPTURE=50  # Enable for 50% of users
   python src/graph_with_flags.py
```
