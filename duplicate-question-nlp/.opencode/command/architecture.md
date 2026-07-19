---
description: Design or review system architecture.
---

# Architecture Design and Review Prompt

You are tasked with designing a new system architecture or reviewing an existing one.

## Input

{{input}}

## Architecture Framework

### 1. System Context and Boundaries

- **System name**: what is this system called?
- **Purpose**: what business or technical problem does it solve?
- **Stakeholders**: who cares about this system (users, operators, business owners, regulators)?
- **System boundary**: what is inside vs outside the system?
- **External dependencies**: what external systems, services, or APIs does it interact with?
- **Constraints**: budget, timeline, team skills, compliance requirements, technology standards
- **Assumptions**: what are we assuming about load, growth, availability requirements?

### 2. Architectural Drivers

- **Functional requirements**: key features and capabilities (use case diagrams, user stories)
- **Quality attributes (non-functional requirements)**:
  - **Performance**: expected throughput (RPS, TPS), acceptable latency (p50, p95, p99)
  - **Scalability**: expected growth rate, peak load, horizontal vs vertical scaling strategy
  - **Availability**: target uptime (99.9%, 99.99%, 99.999%), RTO, RPO
  - **Security**: compliance standards (SOC2, HIPAA, GDPR, PCI-DSS), threat model
  - **Maintainability**: expected change frequency, team size, onboarding time
  - **Reliability**: fault tolerance, graceful degradation, data durability
  - **Cost**: operating budget, infrastructure cost, licensing
- **Tradeoffs**: which qualities are prioritized over others and why

### 3. Component Breakdown

**High-Level Architecture Diagram** (textual representation):

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│   API GW    │────▶│   Service   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
                                        ┌───────▼───────┐
                                        │   Database    │
                                        └───────────────┘
```

**Component Descriptions**:

Each component should describe:
- **Name**: component name
- **Responsibility**: what it does (single sentence)
- **Key interfaces**: APIs, events, messages it sends/receives
- **Data owned**: what data it stores or is authoritative for
- **Technology**: implementation language, framework, runtime
- **State**: stateless or stateful
- **Replication**: number of instances, replication strategy
- **Failure mode**: what happens when this component fails
- **Scaling strategy**: how it scales

### 4. Data Flow

**Request/Response Flows**:
- Describe the flow for key use cases:
  1. User authentication flow
  2. Primary user action flow (create, read, update, delete)
  3. Background job/data processing flow
  4. Error/exception flow
  5. Degraded mode flow (when dependencies are unavailable)

**Data Models**:
- Entity-Relationship diagram (text-based)
- Key entities, their attributes, and relationships
- Data volume estimates (rows, growth rate, storage size)
- Data retention policy
- Archival and purging strategy

**Event/Message Flow**:
- Events produced and consumed by each component
- Message schemas and formats (Avro, Protobuf, JSON Schema)
- Delivery guarantees (at-most-once, at-least-once, exactly-once)
- Message ordering requirements

### 5. Technology Choices

For each major technology decision, document:

| Decision | Option Chosen | Alternatives Considered | Rationale |
|----------|---------------|------------------------|-----------|
| Programming language | Go | Java, Python | Performance, concurrency model, team expertise |
| Database | PostgreSQL | MySQL, CockroachDB | ACID compliance, JSON support, maturity |
| Message queue | Kafka | RabbitMQ, SQS | Throughput, durability, replay capability |
| Container orchestration | Kubernetes | ECS, Nomad | Portability, ecosystem, community support |
| Cloud provider | AWS | GCP, Azure | Existing investment, service maturity |

### 6. API Design

- **API style**: REST, GraphQL, gRPC, WebSocket, or hybrid
- **Versioning strategy**: URI-based, header-based, or contract-based
- **Authentication**: OAuth 2.0, API keys, JWT, mutual TLS
- **Rate limiting**: per user, per IP, per endpoint
- **Pagination**: cursor-based vs offset-based
- **Error format**: consistent error response structure (RFC 7807 Problem Details)
- **Idempotency**: which operations support idempotency keys
- **Documentation**: OpenAPI/Swagger, GraphQL schema

### 7. Scalability Strategy

- **Load distribution**: load balancer configuration, DNS routing, anycast
- **Stateless services**: horizontally scalable, behind load balancer
- **Database scaling**:
  - Read replicas for read-heavy workloads
  - Sharding for write-heavy workloads (shard key strategy)
  - Connection pooling
  - Caching layer (Redis, Memcached) to reduce database load
- **Caching strategy**:
  - Local cache (in-memory, co-located)
  - Distributed cache (Redis, Memcached)
  - CDN for static and semi-static content
  - HTTP caching (Cache-Control, ETag, CDN)
  - Cache invalidation strategy
- **Asynchronous processing**:
  - Message queues for decoupling
  - Background job processors
  - Event-driven architecture

### 8. Reliability and Resilience

- **High availability**: multi-AZ, multi-region deployment
- **Disaster recovery**: RTO/RPO, backup strategy, cross-region replication
- **Fault tolerance**:
  - Circuit breakers for external dependencies
  - Retry with exponential backoff and jitter
  - Bulkheads to isolate failures
  - Graceful degradation (degraded mode, feature toggles)
  - Timeouts and deadlines
- **Data durability**:
  - Database backups (point-in-time recovery)
  - Replication factor for distributed systems
  - Write-ahead logs and commit logs
  - Saga pattern for distributed transactions

### 9. Security Architecture

- **Network security**: VPC, subnets, security groups, firewalls, WAF
- **Identity and access management**: IAM roles, service accounts, least privilege
- **Authentication**: SSO, MFA, OAuth, OIDC, SAML
- **Authorization**: RBAC, ABAC, policy engine (OPA, Casbin)
- **Data protection**: encryption at rest (AES-256), encryption in transit (TLS 1.3)
- **Secrets management**: Vault, AWS Secrets Manager, Azure Key Vault
- **Audit logging**: who did what, when, from where
- **Compliance**: relevant standards and how they are addressed

### 10. Observability and Monitoring

- **Logging**: structured logging (JSON), log levels, centralized aggregation (ELK, Loki)
- **Metrics**: RED metrics (Rate, Errors, Duration), USE metrics (Utilization, Saturation, Errors)
- **Tracing**: distributed tracing with OpenTelemetry, trace context propagation
- **Dashboards**: Grafana dashboards for each service
- **Alerting**: alert rules, notification channels, escalation policy
- **SLOs/SLIs**: service level objectives and indicators
- **On-call**: rotation schedule, escalation paths, runbooks

### 11. Tradeoffs and Alternatives

Document architectural decisions with Architecture Decision Records (ADRs):

```
## ADR-NNN: [Title]

**Status**: Proposed / Accepted / Deprecated / Superseded

**Context**: What is the issue motivating this decision?

**Decision**: What was decided and why?

**Consequences**: What becomes easier or harder as a result?

**Alternatives considered**: What other options were explored and why rejected?
```

### 12. Deployment and Operations

- **Deployment model**: self-hosted, PaaS, SaaS, hybrid
- **CI/CD pipeline**: build, test, deploy stages
- **Infrastructure as Code**: Terraform, Pulumi, CloudFormation
- **Environment strategy**: dev, staging, production, canary
- **Release strategy**: blue-green, rolling, canary, feature flags
- **Capacity planning**: how to determine resource requirements
- **Cost optimization**: right-sizing, reserved instances, spot instances

## Output Format

### Architecture Document

1. Executive Summary
2. System Context
3. Architectural Drivers
4. Component Architecture
5. Data Architecture
6. Technology Decisions
7. Scalability Design
8. Reliability Design
9. Security Architecture
10. Observability
11. Deployment Strategy
12. ADRs
13. Appendices (diagrams, references, glossary)
