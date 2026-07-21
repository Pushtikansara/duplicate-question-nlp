# Knowledge Graph — Semantic Relationship Storage

---

## 1. Overview

The KnowledgeGraph is a component of the ARES CMS that stores and manages semantic relationships between concepts extracted from memory entries. It provides graph-based operations — node/edge CRUD, neighbor traversal, label/type-based search, and path finding — that enable relationship discovery and query expansion across the CMS.

---

## 2. Architecture

```
KnowledgeGraph
  |
  +-- Nodes:   dict[str, KnowledgeNode]    (id -> node)
  +-- Edges:   dict[str, KnowledgeEdge]    (id -> edge)
  +-- Adjacency: dict[str, set[str]]       (node_id -> set of neighbor node_ids)
```

### Data Structures

```python
@dataclass
class KnowledgeNode:
    id: str                     # Unique node identifier
    label: str                  # Human-readable label
    type: str                   # Node type (concept, entity, intent, ...)
    properties: dict[str, Any]  # Arbitrary properties
    confidence: float           # Confidence in this node [0, 1]

@dataclass
class KnowledgeEdge:
    id: str                     # Unique edge identifier
    source: str                 # Source node ID
    target: str                 # Target node ID
    relation: str               # Relation type (is_a, related_to, supports, contradicts, ...)
    weight: float               # Edge weight [0, 1]
    properties: dict[str, Any]  # Arbitrary properties
```

---

## 3. Graph Operations

### Node Operations

| Method | Signature | Description |
|---|---|---|
| `add_node` | `(id, label, type, properties, confidence) -> str` | Add node, return node ID |
| `get_node` | `(node_id) -> KnowledgeNode \| None` | Retrieve node by ID |
| `update_node` | `(node_id, **kwargs) -> bool` | Update node properties |
| `remove_node` | `(node_id) -> bool` | Remove node and all incident edges |
| `search_nodes` | `(label=None, type=None) -> list[KnowledgeNode]` | Search by label or type |
| `get_all_nodes` | `() -> list[KnowledgeNode]` | List all nodes |

### Edge Operations

| Method | Signature | Description |
|---|---|---|
| `add_edge` | `(id, source, target, relation, weight, properties) -> str` | Add edge, return edge ID |
| `get_edge` | `(edge_id) -> KnowledgeEdge \| None` | Retrieve edge by ID |
| `remove_edge` | `(edge_id) -> bool` | Remove edge |
| `get_edges_from` | `(node_id) -> list[KnowledgeEdge]` | Get all outgoing edges |
| `get_edges_to` | `(node_id) -> list[KnowledgeEdge]` | Get all incoming edges |

### Traversal Operations

| Method | Signature | Description |
|---|---|---|
| `get_neighbors` | `(node_id, relation=None, max_depth=1) -> set[str]` | Get neighbor node IDs, optionally filtered by relation |
| `traverse` | `(start_id, relation, max_depth=3) -> list[list[str]]` | BFS traversal finding all paths matching relation |
| `shortest_path` | `(source_id, target_id) -> list[str] \| None` | Shortest path between two nodes |
| `find_subgraph` | `(node_ids) -> tuple[list, list]` | Extract subgraph containing specified nodes |

---

## 4. Building the Graph from Memory Entries

The KnowledgeGraph can be populated from memory entries, particularly from `SEMANTIC` and `REASONING` types:

```python
def build_from_entry(graph: KnowledgeGraph, entry: MemoryEntry) -> None:
    if entry.memory_type == MemoryType.SEMANTIC:
        # Extract concepts as nodes
        for concept in entry.content.get("concepts", []):
            graph.add_node(
                id=f"concept_{concept['name']}",
                label=concept["name"],
                type=concept.get("type", "concept"),
                properties={"source_memory": entry.memory_id},
                confidence=concept.get("confidence", 1.0),
            )

        # Extract entities as nodes
        for entity in entry.content.get("entities", []):
            graph.add_node(
                id=f"entity_{entity['name']}",
                label=entity["name"],
                type=entity.get("category", "entity"),
                properties={"source_memory": entry.memory_id},
                confidence=1.0,
            )

        # Extract relations as edges
        for relation in entry.content.get("relations", []):
            graph.add_edge(
                id=f"rel_{relation['source']}_{relation['target']}",
                source=f"concept_{relation['source']}",
                target=f"concept_{relation['target']}",
                relation=relation.get("relation", "related_to"),
                weight=relation.get("weight", 1.0),
                properties={"source_memory": entry.memory_id},
            )
```

---

## 5. Search Operations

### Search Nodes by Label

```python
# Find all nodes with "Python" in the label
nodes = graph.search_nodes(label="Python")
# Returns: [KnowledgeNode(id="concept_Python", label="Python", type="programming_language", ...)]
```

### Search Nodes by Type

```python
# Find all programming language nodes
nodes = graph.search_nodes(type="programming_language")
# Returns: [KnowledgeNode(id="concept_Python", ...), KnowledgeNode(id="concept_Java", ...)]
```

### Combined Search

```python
# Find all entity nodes
nodes = graph.search_nodes(type="entity")
```

---

## 6. Traversal Examples

### Basic Neighbor Traversal

```python
# Find concepts directly related to "Python"
neighbors = graph.get_neighbors("concept_Python", max_depth=1)
# Returns: {"concept_installation", "entity_Ubuntu", "concept_programming"}
```

### Path Finding

```python
# Find a path from "Python" to "Linux"
path = graph.shortest_path("concept_Python", "entity_Linux")
# Returns: ["concept_Python", "entity_Ubuntu", "entity_Linux"]
```

### Multi-Hop Traversal

```python
# Find all concepts related to Python through any relation, up to 3 hops
paths = graph.traverse("concept_Python", relation=None, max_depth=3)
# Returns: [
#   ["concept_Python", "concept_installation"],
#   ["concept_Python", "entity_Ubuntu", "entity_Linux"],
#   ...
# ]
```

---

## 7. Serialization

```python
# Serialize entire graph
graph_dict = {
    "nodes": {nid: node.__dict__ for nid, node in graph._nodes.items()},
    "edges": {eid: edge.__dict__ for eid, edge in graph._edges.items()},
}

# Deserialize
def from_dict(data: dict) -> KnowledgeGraph:
    graph = KnowledgeGraph()
    for nid, node_data in data.get("nodes", {}).items():
        graph.add_node(**node_data)
    for eid, edge_data in data.get("edges", {}).items():
        graph.add_edge(**edge_data)
    return graph
```

---

## 8. Example Usage Scenarios

### Query Expansion for Retrieval

```python
def expand_query_with_graph(query_text, graph):
    # Find nodes matching query text
    matching_nodes = graph.search_nodes(label=query_text)

    # Get related concepts
    expanded_terms = set()
    for node in matching_nodes:
        neighbors = graph.get_neighbors(node.id, max_depth=2)
        for neighbor_id in neighbors:
            neighbor = graph.get_node(neighbor_id)
            if neighbor:
                expanded_terms.add(neighbor.label)

    # Augment search query with related terms
    return f"{query_text} {' '.join(expanded_terms)}"
```

### Concept Drift Detection

```python
def detect_concept_drift(graph, concept_name, old_edges, new_edges):
    # Compare edge structure around a concept over time
    node = graph.search_nodes(label=concept_name)
    if not node:
        return None

    current_edges = set(graph.get_edges_from(node[0].id))
    old_edge_set = set(old_edges)
    new_edge_set = set(new_edges)

    return {
        "removed_relations": old_edge_set - current_edge_set,
        "added_relations": current_edge_set - old_edge_set,
        "drift_score": len(current_edge_set ^ old_edge_set) / max(len(current_edge_set | old_edge_set), 1),
    }
```

---

## 9. Performance Characteristics

| Operation | Complexity | Typical Time (1000 nodes) |
|---|---|---|
| `add_node` | O(1) | < 0.01 ms |
| `add_edge` | O(1) | < 0.01 ms |
| `get_neighbors` (depth=1) | O(d) where d = degree | < 0.01 ms |
| `shortest_path` | O(V + E) | < 0.1 ms |
| `traverse` (depth=3) | O(b^d) where b = branching factor | < 0.5 ms |
| `search_nodes` (linear) | O(N) | < 0.1 ms |

---

## 10. Limitations and Future Work

### Current Limitations

- In-memory only (no persistent graph storage)
- No graph analytics (centrality, community detection, PageRank)
- No support for graph embeddings or vector representations
- No incremental update from memory changes
- No visualization capabilities

### Future Work

- Graph analytics: degree centrality, betweenness, PageRank for importance scoring
- Concept drift detection: track changes in graph structure over time to identify evolving concepts
- Query expansion: use graph traversal to augment retrieval queries with related terms
- Graph visualization: export to Graphviz or D3.js for debugging
- Persistent graph backend: optional integration with Neo4j or similar

---

## 11. References

- Architecture: `MEMORY_ARCHITECTURE.md`
- Memory types: `MEMORY_TYPES.md`
- Retrieval: `RETRIEVAL_ENGINE.md`
- Semantic memory (graph source): `MEMORY_TYPES.md#4-semantic-memory`
