# 🎒 SmartPack — Agentic AI Smart Packing Assistant

SmartPack is an **Agentic AI-powered travel packing assistant** that creates personalized packing lists based on the user's destination, trip duration, purpose, activities, destination characteristics, and real-world weather information.

Unlike a traditional chatbot, SmartPack can **use external tools, retrieve information, validate the user's request, and then generate a context-aware packing recommendation.**

---

## 🤖 How SmartPack Works

The user provides:

- 📍 Destination
- 📅 Trip duration
- 🎯 Purpose of travel
- 🏃 Planned activities

The AI agent then follows this workflow:

```text
User Input
    ↓
Groq LLM
    ↓
Tool Calling
    ↓
┌─────────────────────┐
│ check_destination() │
└─────────────────────┘
    ↓
Destination Data
    ↓
┌─────────────────┐
│ check_weather() │
└─────────────────┘
    ↓
Weather Data
    ↓
AI Reasoning
    ↓
🎒 Personalized Packing List
