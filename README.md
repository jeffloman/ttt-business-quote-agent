# Local Business Quote Agent

A small Python-based Local Business Quote Agent built step by step to learn agent routing, session memory, quote intake, clarifying follow-ups, logging, testing, and maintainable agent structure.

## Current Status
This project has been built day by day as a learning project focused on agentic AI fundamentals for a local service business use case.

Current implemented areas include:
- Intent detection and routing
- Business info tool calling
- Session memory for follow-up questions
- Multi-turn quote intake flow
- Clarifying fallback behavior
- Toggleable logging
- Regression testing

## Project Files
- `agent.py` — main agent orchestration and routing
- `app.py` — command-line entry point
- `business_data.py` — business information used by the tools
- `tools.py` — business tools used by the agent
- `tests.py` — regression and behavior tests
- `.gitignore` — ignores virtual env, cache, logs, and env files

## Run Locally

### 1. Open the project folder
Open the project in VS Code or your terminal.

### 2. Run the tests

```bash
python tests.py