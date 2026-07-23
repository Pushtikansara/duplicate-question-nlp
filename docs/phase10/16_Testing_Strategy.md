# Phase 10 — Testing Strategy

## 1. Test Pyramid

```
         ╱╲
        ╱ E2E ╲          5-10 tests: full workflow with real services
       ╱────────╲
      ╱ Integration ╲    50-100 tests: Agent+Tool+Workflow integration
     ╱──────────────╲
    ╱   Unit Tests    ╲   500+ tests: individual agents, tools, engine
   ╱──────────────────╲
  ╱ Regression Tests   ╲   1960 existing tests — MUST ALL PASS
 ╱──────────────────────╲
```

## 2. Regression Tests (Gate)

All 1960+ existing tests must pass before any Phase 10 code is merged.

```bash
pytest tests/ --ignore=tests/load --ignore=tests/performance --ignore=tests/streamlit
```

**Gate script**: `ci/phase10_gate.sh`

## 3. Unit Tests (New)

| Module | Test Count | Key Scenarios |
|--------|-----------|---------------|
| `ares/agents/base.py` | 20 | Agent ABC validation, metadata, capability resolution |
| `ares/agents/registry.py` | 15 | Register, unregister, get, list, duplicate detection |
| `ares/agents/lifecycle.py` | 30 | State transitions, guards, error handling |
| `ares/agents/builtin/*.py` | 40 | Each built-in agent: happy path, edge cases, error cases |
| `ares/tools/base.py` | 15 | Tool ABC, spec validation, input validation |
| `ares/tools/registry.py` | 20 | Register, unregister, permission checks, execute |
| `ares/tools/builtin/*.py` | 50 | Each tool: mock service layer, verify delegation |
| `ares/workflow/engine.py` | 40 | DAG execution, sequential, parallel, conditional |
| `ares/workflow/models.py` | 15 | YAML serialization/deserialization, variable substitution |
| `ares/workflow/storage.py` | 10 | File-backed save/load/list/delete |
| `ares/planning/engine.py` | 20 | Decompose, validate, replan |
| `ares/eventbus/bus.py` | 25 | Subscribe, emit, unsubscribe, wildcards, concurrency |
| `ares/orchestration/coordinator.py` | 30 | Multi-agent orchestration, strategies, error handling |
| `ares/orchestration/scheduler.py` | 15 | Concurrency, timeouts, retries |

**Total new unit tests: ~350**

## 4. Integration Tests

| Test | Description |
|------|-------------|
| `test_agent_invokes_tool` | Agent calls a tool, verifies result, audit, event |
| `test_workflow_sequential` | 3-step sequential workflow with agents |
| `test_workflow_parallel` | 4-agent parallel execution with consensus |
| `test_workflow_conditional` | Branching workflow based on confidence threshold |
| `test_agent_permission_denied` | Agent without permission → ToolPermissionError |
| `test_workflow_replan` | Failed step triggers replanning |
| `test_event_bus_flow` | Full event lifecycle: emit → subscriber → effect |
| `test_audit_log` | Agent+tool invocations appear in audit log |
| `test_state_persistence` | Workflow store survives restart (file-backed) |
| `test_plugin_agent` | Plugin registers an agent; agent is invocable |

## 5. E2E Tests

| Test | Description |
|------|-------------|
| `test_analyze_pair_workflow` | Full workflow: predict → debate → reflect → store |
| `test_rest_api_agent_flow` | POST /api/v1/agents/{id}/invoke → valid response |
| `test_rest_api_workflow_flow` | Register → execute → poll result |
| `test_cli_agent_workflow` | `ares workflow run` → output |
| `test_backward_compatibility` | All original endpoints return expected responses |

## 6. Security Tests

| Test | Description |
|------|-------------|
| `test_unauthorized_tool_access` | Agent without permission cannot invoke tool |
| `test_agent_isolation` | Agent A cannot read Agent B's ephemeral context |
| `test_audit_trail_integrity` | Every invocation is logged; no gaps |
| `test_tool_timeout` | Hanging tool is terminated |
| `test_infinite_agent_loop` | Agent recursion is detected and stopped |

## 7. Test Fixtures

```python
# New conftest fixtures:
@pytest.fixture
def agent_registry():
    registry = AgentRegistry()
    registry.register(IntentAgent())
    registry.register(SemanticAgent())
    return registry

@pytest.fixture
def tool_registry():
    registry = ToolRegistry()
    registry.register(MockPredictTool())
    registry.register(MockMemoryTool())
    return registry

@pytest.fixture
def event_bus():
    return EventBus()

@pytest.fixture
def workflow_engine(agent_registry, tool_registry, event_bus):
    return WorkflowEngine(agent_registry, tool_registry, event_bus)

@pytest.fixture
def coordinator(agent_registry, tool_registry, event_bus):
    return AgentCoordinator(agent_registry, tool_registry, event_bus)

@pytest.fixture
def planning_engine(agent_registry, tool_registry):
    return PlanningEngine(agent_registry, tool_registry)

@pytest.fixture
def sample_workflow_yaml():
    return Path("tests/fixtures/workflows/analyze_pair.yaml").read_text()
```

## 8. CI Integration

```yaml
# .github/workflows/phase10.yml (new)
jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - run: ARES_SECRET_KEY=test-key python -m pytest tests/ --ignore=tests/load -x

  unit:
    needs: [gate]
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/unit/agents tests/unit/tools tests/unit/workflow tests/unit/eventbus tests/unit/orchestration

  integration:
    needs: [gate]
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/integration/test_phase10_*

  security:
    needs: [gate]
    runs-on: ubuntu-latest
    steps:
      - run: python -m pytest tests/security/test_agent_security*
```
