# API Report — Phase 10.5.1

## Endpoints Reference

### POST /api/v1/ares/chat

Run the full end-to-end ARES demo pipeline.

**Request Body:**
```json
{
  "question1": "How do I learn to code?",
  "question2": "What is the best way to start programming?",
  "scenario_id": null,
  "goal": "",
  "strategy": "LINEAR",
  "agent_ids": null,
  "available_tools": null
}
```

**Response:** Complete pipeline result with goal, plan, prediction, memory, reflection, orchestration, timeline, events.

### POST /api/v1/ares/plan

Generate a plan without executing it.

**Request Body:**
```json
{
  "goal": "Analyze semantic similarity between two questions",
  "strategy": "LINEAR",
  "agent_ids": ["planner", "predict"],
  "available_tools": ["predict", "memory"]
}
```

### GET /api/v1/ares/plans/{plan_id}

Retrieve a specific plan by ID.

### GET /api/v1/ares/memory

Get all memory entries and stats from the MemoryManager.

### GET /api/v1/ares/tools

List all registered tools.

### GET /api/v1/ares/agents

List all registered agents with status and invocation counts.

### GET /api/v1/ares/events

Get event stream from the EventBus.

### GET /api/v1/ares/metrics

Get PlanningMetrics summary.

### GET /api/v1/ares/health

Health check for the demo system.

### GET /api/v1/ares/scenarios

List available demo scenarios.

## Router Structure

All endpoints are in `ares/api/routers/ares_demo.py` and registered in `ares/api/router.py` under the `ARES Demo` tag.
