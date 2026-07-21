# Cognitive Pipeline Architecture

## Purpose

The CognitivePipeline unifies six cognitive subsystems into a single coherent execution flow for duplicate question detection. It replaces ad-hoc module wiring with a structured, event-driven pipeline that enforces interfaces, guarantees execution order, and provides observability at every stage.

## Architecture Diagram

```
+-------------------------------------------------------------------+
|                         PIPELINE ENTRY                              |
|  CognitivePipeline.run(question_pair, context)                      |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  1. PERCEPTION ENGINE           (_perception)                       |
|     - normalize text, extract features, build raw tensors          |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  2. ADAPTIVE ROUTER             (_routing)                          |
|     - classify complexity, select model strategy                   |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  3. CMS MEMORY (READ)          (_memory)                            |
|     - retrieve historical context from vector store (optional)     |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  4. SEMANTIC INTELLIGENCE      (_semantic_intelligence)             |
|     - embed, compare semantic similarity                           |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  5. COGNITIVE REASONING        (_reasoning)                         |
|     - apply decision rules, conflict resolution                    |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  6. MULTI-AGENT DEBATE         (_agents/MADE)                       |
|     - simulated agent deliberation (if confidence threshold met)   |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  7. FINAL DECISION              (existing prediction functions)     |
|     - produce verdict, confidence, explainability payload          |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|  8. CMS MEMORY (WRITE)         (_memory)                            |
|     - store outcome for future retrieval (write-only)              |
+-------------------------------------------------------------------+
                                |
                                v
+-------------------------------------------------------------------+
|                         PIPELINE EXIT                               |
|  PipelineResult(verdict, confidence, metadata, events)              |
+-------------------------------------------------------------------+
```

## Design Principles

### Dependency Inversion
All modules expose interfaces (abstract protocols). The CognitivePipeline depends on these interfaces, never on concrete implementations. Modules are injectable at construction time via the IntegrationPlugin system.

### Event-Driven
Every stage boundary fires a PipelineEvent. Hooks subscribed to events receive the PipelineContext at that point. This enables cross-cutting concerns (logging, metrics, tracing) without modifying module code.

### Backward Compatible
The existing prediction function signature `predict(question1, question2)` remains unchanged. The pipeline is a wrapper that dispatches to the same underlying logic. Zero-copy pass-through means no serialization overhead when the pipeline is enabled.

### Fault Isolation
Each module executes in its own try/except block within the lifecycle manager. A module failure produces a FAILED state but does not cascade unless the error is marked critical. The pipeline can degrade gracefully (skip failed modules) when configured.

## Component Overview

| Module | Package | Responsibility |
|---|---|---|
| Perception Engine | `_perception` | Text normalization, feature extraction, input validation |
| Adaptive Router | `_routing` | Complexity classification, model dispatch strategy |
| CMS Memory | `_memory` | Vector store read (pre-prediction) and write (post-prediction) |
| Semantic Intelligence | `_semantic_intelligence` | Embedding generation, similarity scoring |
| Cognitive Reasoning | `_reasoning` | Rule application, conflict resolution, confidence calibration |
| Multi-Agent Debate | `_agents/MADE` | Simulated multi-agent deliberation for ambiguous cases |
| Final Decision | existing prediction functions | Verdict output, confidence score, explainability |
