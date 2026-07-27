# Explainability Architecture

## Overview

The Decision Trace Engine provides complete transparency into every decision made by the ARES Query Understanding pipeline. It is purely explanatory and does not affect prediction behavior.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DecisionTraceBuilder                      │
│  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌──────────┐  │
│  │ Layer 1  │  │ Layer 2  │  │  Layer 3   │  │ Layer 4  │  │
│  │Question  │  │ Entity   │  │Relationship│  │Complexity│  │
│  │  Type    │  │ Trace    │  │   Trace    │  │  Trace   │  │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └────┬─────┘  │
│       │             │              │               │        │
│       └─────────────┴──────┬───────┴───────────────┘        │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   Layer 5      │                       │
│                    │ Routing Trace  │                       │
│                    └───────┬────────┘                       │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   Layer 6      │                       │
│                    │  Confidence    │                       │
│                    │  Aggregation   │                       │
│                    └───────┬────────┘                       │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   Layer 7      │                       │
│                    │   Decision     │                       │
│                    │   Summary      │                       │
│                    └───────┬────────┘                       │
│                            │                                │
│                    ┌───────▼────────┐                       │
│                    │   Layer 8      │                       │
│                    │ Final Decision │                       │
│                    │     Trace      │                       │
│                    └────────────────┘                       │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              DecisionTraceRenderer                   │   │
│  │  Plain Text    │  Markdown    │  JSON    │  Dict     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Layers

| Layer | Component | Description |
|-------|-----------|-------------|
| 1 | Question Type Trace | Explains type classification for both questions and pair |
| 2 | Entity Trace | Documents entity extraction, matching, and overlap |
| 3 | Relationship Trace | Records relationship detection rules fired and evidence |
| 4 | Complexity Trace | Details complexity metrics and their contributions |
| 5 | Routing Trace | Explains strategy selection and rejection |
| 6 | Confidence Aggregation | Combines per-stage confidence into overall score |
| 7 | Decision Summary | Produces human-readable summary |
| 8 | Final Decision Trace | Assembles complete DecisionTrace object |

## Key Design Decisions

- **Deterministic**: No ML, no LLMs, no external APIs
- **Non-intrusive**: Does not modify any existing prediction or analysis
- **Lightweight**: Average <2ms overhead
- **Composable**: Each layer can be used independently
- **Serializable**: Full JSON round-trip support
