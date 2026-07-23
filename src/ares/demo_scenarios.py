from __future__ import annotations

from typing import Any

DEMO_SCENARIOS: dict[str, dict[str, Any]] = {
    "duplicate_detection": {
        "name": "Duplicate Question Detection",
        "description": "Analyze whether two questions are duplicates using the full ARES pipeline",
        "goal": "Analyze the semantic similarity between two questions and determine if they are duplicates",
        "question1": "How do I learn to code?",
        "question2": "What is the best way to start programming?",
        "strategy": "LINEAR",
        "agent_ids": ["planner", "predict", "memory", "reflection"],
        "available_tools": ["predict", "memory"],
    },
    "duplicate_detection_exact": {
        "name": "Exact Duplicate Detection",
        "description": "Test with clearly duplicate questions to verify detection",
        "goal": "Determine if two identical questions are correctly identified as duplicates",
        "question1": "What is machine learning?",
        "question2": "What is machine learning?",
        "strategy": "LINEAR",
        "agent_ids": ["planner", "predict", "memory", "reflection"],
        "available_tools": ["predict", "memory"],
    },
    "duplicate_detection_non": {
        "name": "Non-Duplicate Detection",
        "description": "Test with clearly non-duplicate questions",
        "goal": "Determine if two unrelated questions are correctly identified as non-duplicates",
        "question1": "How do I bake a cake?",
        "question2": "What is quantum physics?",
        "strategy": "LINEAR",
        "agent_ids": ["planner", "predict", "memory", "reflection"],
        "available_tools": ["predict", "memory"],
    },
    "memory_demo": {
        "name": "Memory Operations Demo",
        "description": "Store prediction results and retrieve them from memory",
        "goal": "Store and retrieve prediction results using the memory system",
        "question1": "What is Python?",
        "question2": "What is Python programming language?",
        "strategy": "LINEAR",
        "agent_ids": ["planner", "predict", "memory", "reflection"],
        "available_tools": ["predict", "memory"],
    },
    "full_pipeline": {
        "name": "Full ARES Pipeline Demo",
        "description": "Complete end-to-end pipeline with planning, prediction, memory, and reflection",
        "goal": "Execute the complete ARES demonstration pipeline end-to-end",
        "question1": "How does artificial intelligence work?",
        "question2": "Can you explain how AI functions?",
        "strategy": "DAG",
        "agent_ids": ["planner", "predict", "memory", "reflection"],
        "available_tools": ["predict", "memory"],
    },
}
