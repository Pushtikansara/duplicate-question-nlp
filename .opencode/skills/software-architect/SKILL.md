---
name: software-architect
description: Use when designing software architecture. Covers architectural patterns, system design, trade-off analysis, and documentation.
---

# Software Architect Skill

## Instructions

Software architecture is the set of structures needed to reason about a software system, comprising software elements, relations among them, and properties of both. Architecture decisions are the most consequential decisions in software development, affecting system qualities like performance, scalability, maintainability, and security. This skill covers architectural patterns, system design, trade-off analysis, architecture documentation, and decision-making frameworks.

### The Role of a Software Architect

A software architect bridges business requirements and technical implementation. Key responsibilities include:

- Defining the high-level structure of the system
- Making technology choices that align with business goals
- Establishing technical standards and patterns for the team
- Communicating architecture decisions to stakeholders
- Ensuring architectural qualities (performance, security, scalability)
- Governing implementation to ensure architectural compliance
- Managing technical risk through analysis and prototyping
- Mentoring developers on architectural principles

### Architecture Characteristics (Non-functional Requirements)

Every system has architectural characteristics that drive design decisions:

| Characteristic | Definition | Trade-off |
|----------------|------------|-----------|
| Scalability | Ability to handle increased load | Complexity, cost |
| Availability | System uptime and resilience | Cost, complexity |
| Performance | Response time and throughput | Cost, scalability |
| Security | Protection from threats | Performance, usability |
| Maintainability | Ease of making changes | Design up-front effort |
| Testability | Ease of verifying correctness | Design complexity |
| Deployability | Ease of releasing to production | Infrastructure complexity |
| Observability | Ability to understand system state | Logging/tracing overhead |
| Extensibility | Ease of adding new features | Abstraction overhead |
| Portability | Ability to run in different environments | Native feature usage |

### Architecture Decision-Making

Architecture decisions should be made systematically using the following approach:

1. **Identify the decision**: What needs to be decided?
2. **Gather context**: What are the constraints and requirements?
3. **Identify alternatives**: Research possible options
4. **Evaluate trade-offs**: Use a trade-off matrix
5. **Make the decision**: Select the best alternative
6. **Document the decision**: Use Architecture Decision Records (ADRs)
7. **Communicate**: Share with stakeholders
8. **Govern**: Ensure implementation follows the decision

## Examples

### Example 1: Architecture Decision Record (ADR)

```markdown
# ADR-001: Use PostgreSQL for Primary Data Store

## Status
Accepted

## Context
We need to choose a primary data store for our e-commerce platform. The system needs to handle:
- 500,000+ product SKUs
- 10,000+ orders per day
- Complex product catalog queries with faceted search
- Transactional integrity for order processing
- Multi-tenancy support
- Team familiarity with relational databases

## Decision
We will use PostgreSQL as our primary data store.

## Alternatives Considered

### MongoDB
- Pros: Schema flexibility, horizontal scaling, good for product catalog
- Cons: No native ACID transactions across collections (pre-4.0), weaker query capabilities for complex joins, team less experienced

### MySQL
- Pros: Good read performance, widely used, replication support
- Cons: Weaker JSON support, less mature partitioning, fewer advanced extensions

### Amazon DynamoDB
- Pros: Fully managed, infinite scaling, low operational overhead
- Cons: Limited query patterns, no joins, high costs at scale, vendor lock-in

## Consequences

### Positive
- Strong ACID compliance for order processing
- Excellent JSON support for flexible product attributes
- Rich extension ecosystem (PostGIS for geo, pgvector for ML)
- Mature tooling and hosting options
- Team has strong PostgreSQL experience

### Negative
- Vertical scaling limit for write-heavy workloads
- Need to implement caching layer for read-heavy queries
- Sharding requires application-level complexity

## Compliance
- Must use parameterized queries to prevent SQL injection
- All schema changes must go through migrations
- Row-level security must be used for multi-tenancy

## Notes
- Consider PostgreSQL 16 for improved performance
- Evaluate connection pooling with PgBouncer
- Plan for read replicas for reporting queries
```

### Example 2: Trade-off Analysis Matrix

```typescript
/**
 * Trade-off analysis for monolith vs. microservices.
 */

interface ArchitectureOption {
    name: string;
    scores: Record<string, number>;  // 1-5 scale
    weights: Record<string, number>; // 0-1 importance
}

function evaluateOptions(options: ArchitectureOption[]): void {
    const characteristics = [
        'Scalability',
        'Development Speed',
        'Operational Complexity',
        'Deployment Risk',
        'Team Autonomy',
        'Testing Ease',
        'Performance',
        'Cost',
    ];

    console.log('Architecture Trade-off Analysis');
    console.log('='.repeat(60));

    for (const option of options) {
        let totalScore = 0;
        let totalWeight = 0;

        console.log(`\n${option.name}`);
        console.log('-'.repeat(40));

        for (const char of characteristics) {
            const score = option.scores[char];
            const weight = option.weights[char] ?? 1;
            const weighted = score * weight;

            totalScore += weighted;
            totalWeight += weight;

            console.log(`  ${char.padEnd(25)} ${score}/5 (weight: ${weight})`);
        }

        const average = (totalScore / totalWeight).toFixed(2);
        console.log(`  ${'─'.repeat(35)}`);
        console.log(`  Weighted Score: ${average}/5`);
    }
}

// Usage
const options: ArchitectureOption[] = [
    {
        name: 'Modular Monolith',
        scores: {
            'Scalability': 2,
            'Development Speed': 5,
            'Operational Complexity': 5,
            'Deployment Risk': 4,
            'Team Autonomy': 3,
            'Testing Ease': 5,
            'Performance': 4,
            'Cost': 5,
        },
        weights: {
            'Development Speed': 0.9,
            'Operational Complexity': 0.8,
            'Cost': 0.7,
        },
    },
    {
        name: 'Microservices',
        scores: {
            'Scalability': 5,
            'Development Speed': 2,
            'Operational Complexity': 1,
            'Deployment Risk': 2,
            'Team Autonomy': 5,
            'Testing Ease': 2,
            'Performance': 3,
            'Cost': 1,
        },
        weights: {
            'Scalability': 0.5,
            'Team Autonomy': 0.9,
        },
    },
];

evaluateOptions(options);
```

### Example 3: System Context and Container Diagrams (C4 Model)

```python
"""
C4 Model visualizations using diagrams library.
"""
# pip install diagrams

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import EC2, Lambda
from diagrams.aws.database import RDS, ElastiCache
from diagrams.aws.network import ELB, Route53, CloudFront
from diagrams.aws.storage import S3
from diagrams.aws.security import WAF
from diagrams.onprem.queue import Kafka
from diagrams.programming.language import Python, NodeJS, Go


def draw_system_context():
    """System Context diagram showing the system's place in the world."""
    with Diagram("System Context - E-Commerce Platform", show=False, direction="TB"):
        customer = Customer("Customer")
        system = System("E-Commerce\nPlatform")

        customer >> Edge(label="Browses products,\nplaces orders") >> system
        system >> Edge(label="Sends order\nconfirmations") >> EmailService("Email")

        with Cluster("External Systems"):
            payment = ExternalSystem("Payment Gateway")
            shipping = ExternalSystem("Shipping Provider")

        system >> payment
        system >> shipping


def draw_container_diagram():
    """Container diagram showing the high-level technical architecture."""
    with Diagram("Container Diagram - E-Commerce Platform", show=False, direction="TB"):
        # Users
        customer = User("Customer")

        # CDN and load balancers
        cdn = CloudFront("CDN")
        lb = ELB("Load Balancer")

        customer >> cdn >> lb

        # Frontend containers
        with Cluster("Frontend"):
            web_app = NodeJS("Web App\n(React/Next.js)")
            mobile = Go("Mobile API\n(GraphQL)")

        lb >> web_app
        web_app >> mobile

        # Backend services
        with Cluster("Backend Services"):
            with Cluster("API Layer"):
                api = Python("REST API\n(FastAPI)")
                graphql = Go("GraphQL\n(Gateway)")

            with Cluster("Service Layer"):
                orders = NodeJS("Order Service")
                products = Python("Product Service")
                users = Go("User Service")
                inventory = Python("Inventory Service")

            with Cluster("Async Processing"):
                queue = Kafka("Event Bus\n(Kafka)")
                workers = [Lambda("Order Worker"),
                           Lambda("Email Worker"),
                           Lambda("Analytics Worker")]

            api >> graphql
            graphql >> [orders, products, users, inventory]

            orders >> queue
            queue >> workers

        # Data stores
        with Cluster("Data Stores"):
            primary_db = RDS("PostgreSQL\n(Primary)")
            replica_db = RDS("PostgreSQL\n(Read Replica)")
            cache = ElastiCache("Redis\n(Cache)")
            storage = S3("Object Storage")

        # External integrations
        with Cluster("External"):
            payment = ExternalSystem("Payment Provider")
            shipping = ExternalSystem("Shipping Provider")

        # Connections
        orders >> primary_db
        products >> primary_db
        users >> primary_db

        orders >> cache
        products >> cache

        orders >> payment
        orders >> shipping

        products >> storage
        users >> storage

        workers >> primary_db
        workers >> EmailService("SMTP")


def draw_deployment_diagram():
    """Deployment diagram showing infrastructure layout."""
    with Diagram("Deployment - Production Environment", show=False):
        # AWS Region
        with Cluster("AWS us-east-1"):
            with Cluster("VPC"):
                with Cluster("Public Subnets"):
                    lb = ELB("ALB")
                    nat = NAT("NAT Gateway")

                with Cluster("Private App Subnets"):
                    api_asg = EC2("API Servers\n(Auto Scaling)")
                    service_asg = EC2("Service Instances\n(Auto Scaling)")

                with Cluster("Data Subnets"):
                    db_primary = RDS("PostgreSQL\n(Primary)")
                    db_replica = RDS("PostgreSQL\n(Replica)")
                    redis = ElastiCache("Redis\n(Cluster)")

                api_asg >> db_primary
                service_asg >> db_primary
                service_asg >> redis

            with Cluster("Global"):
                cdn = CloudFront("CloudFront")
                dns = Route53("Route 53")

            dns >> cdn
            cdn >> lb
```

### Example 4: Microservices vs Monolith Decision Guide

```python
"""
Decision guide for microservices vs. monolith architecture.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Optional


class TeamSize(Enum):
    SMALL = "1-5 developers"
    MEDIUM = "6-20 developers"
    LARGE = "20+ developers"


class ArchitectureStyle(Enum):
    MONOLITH = "monolith"
    MODULAR_MONOLITH = "modular_monolith"
    MICROSERVICES = "microservices"


@dataclass
class ProjectContext:
    team_size: TeamSize
    team_distribution: str  # "co-located", "distributed"
    domain_complexity: str   # "simple", "moderate", "complex"
    release_cadence: str     # "daily", "weekly", "monthly"
    scalability_need: str    # "low", "medium", "high"
    startup_or_established: str
    regulatory_requirements: List[str]


def recommend_architecture(context: ProjectContext) -> ArchitectureStyle:
    """Recommend architecture style based on project context."""
    score = {style: 0 for style in ArchitectureStyle}

    # Team size analysis
    if context.team_size == TeamSize.SMALL:
        score[ArchitectureStyle.MONOLITH] += 3
        score[ArchitectureStyle.MODULAR_MONOLITH] += 2
        score[ArchitectureStyle.MICROSERVICES] -= 1
    elif context.team_size == TeamSize.MEDIUM:
        score[ArchitectureStyle.MODULAR_MONOLITH] += 3
        score[ArchitectureStyle.MICROSERVICES] += 2
    else:  # LARGE
        score[ArchitectureStyle.MICROSERVICES] += 3
        score[ArchitectureStyle.MODULAR_MONOLITH] += 2

    # Team distribution
    if context.team_distribution == "distributed":
        score[ArchitectureStyle.MICROSERVICES] += 2

    # Scalability needs
    if context.scalability_need == "high":
        score[ArchitectureStyle.MICROSERVICES] += 3
        score[ArchitectureStyle.MODULAR_MONOLITH] += 1
    elif context.scalability_need == "medium":
        score[ArchitectureStyle.MODULAR_MONOLITH] += 2

    # Release cadence
    if context.release_cadence == "daily":
        score[ArchitectureStyle.MICROSERVICES] += 2
    elif context.release_cadence == "monthly":
        score[ArchitectureStyle.MONOLITH] += 1

    # Project stage
    if context.startup_or_established == "startup":
        score[ArchitectureStyle.MONOLITH] += 2
        score[ArchitectureStyle.MICROSERVICES] -= 2

    # Complexity
    if context.domain_complexity == "complex":
        score[ArchitectureStyle.MICROSERVICES] += 2

    # Return the highest scoring architecture
    recommendation = max(score, key=score.get)
    return recommendation


def generate_architecture_report(context: ProjectContext) -> str:
    """Generate an architecture recommendation report."""
    recommendation = recommend_architecture(context)

    report = f"""
Architecture Recommendation Report
{'=' * 60}

Project Context:
- Team Size: {context.team_size.value}
- Team Distribution: {context.team_distribution}
- Domain Complexity: {context.domain_complexity}
- Release Cadence: {context.release_cadence}
- Scalability Need: {context.scalability_need}
- Project Stage: {context.startup_or_established}

Recommended Architecture: {recommendation.value.upper()}

Reasoning:
"""
    if recommendation == ArchitectureStyle.MONOLITH:
        report += """
- Best fit for small teams with simple domains
- Fastest development velocity for startups
- No operational complexity overhead
- Easy to refactor to modular monolith later
"""
    elif recommendation == ArchitectureStyle.MODULAR_MONOLITH:
        report += """
- Best fit for medium teams with moderate complexity
- Clear module boundaries enable future extraction
- Lower operational costs than microservices
- Good balance of autonomy and simplicity
"""
    elif recommendation == ArchitectureStyle.MICROSERVICES:
        report += """
- Necessary for large, distributed teams
- Enables independent scaling of components
- Supports polyglot persistence and technology choices
- Requires mature DevOps and observability practices
"""

    report += """
Next Steps:
1. Document architecture decisions with ADRs
2. Define module/service boundaries using Domain-Driven Design
3. Establish contracts and APIs between components
4. Set up CI/CD pipelines and infrastructure as code
5. Implement observability (logging, metrics, tracing)
"""
    return report
```

### Example 5: Domain-Driven Design Bounded Contexts

```python
"""
Domain-Driven Design bounded context mapping.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set


class ContextRelationship(Enum):
    PARTNERSHIP = "Partnership"
    SHARED_KERNEL = "Shared Kernel"
    CUSTOMER_SUPPLIER = "Customer-Supplier"
    CONFORMIST = "Conformist"
    ANTICORRUPTION_LAYER = "Anticorruption Layer"
    OPEN_HOST = "Open Host"
    PUBLISHED_LANGUAGE = "Published Language"
    SEPARATE_WAY = "Separate Way"


@dataclass
class BoundedContext:
    name: str
    domain: str  # "core", "supporting", "generic"
    description: str
    ubiquitous_language_terms: List[str] = field(default_factory=list)
    aggregates: List[str] = field(default_factory=list)
    events: List[str] = field(default_factory=list)

    def __post_init__(self):
        assert self.domain in ("core", "supporting", "generic")

    def strategic_importance(self) -> str:
        ratings = {"core": "High", "supporting": "Medium", "generic": "Low"}
        return ratings[self.domain]


@dataclass
class ContextMap:
    contexts: Dict[str, BoundedContext] = field(default_factory=dict)
    relationships: Dict[str, Dict[str, ContextRelationship]] = field(default_factory=dict)

    def add_context(self, context: BoundedContext):
        self.contexts[context.name] = context
        if context.name not in self.relationships:
            self.relationships[context.name] = {}

    def add_relationship(self, source: str, target: str,
                         relationship: ContextRelationship):
        if source in self.contexts and target in self.contexts:
            self.relationships[source][target] = relationship

    def visualize(self) -> str:
        """Generate a text-based context map visualization."""
        lines = ["Context Map", "=" * 60]

        for name, context in self.contexts.items():
            importance = context.strategic_importance()
            lines.append(f"\n{name} [{importance}]")
            lines.append(f"  Domain: {context.domain.capitalize()}")
            lines.append(f"  {context.description}")

            if name in self.relationships:
                for target, rel in self.relationships[name].items():
                    lines.append(f"  -> {target}: {rel.value}")

            if context.ubiquitous_language_terms:
                terms = ", ".join(context.ubiquitous_language_terms[:5])
                lines.append(f"  Terms: {terms}")

        return "\n".join(lines)


# Example usage
map = ContextMap()

# Define bounded contexts
ordering = BoundedContext(
    name="Ordering",
    domain="core",
    description="Handles order placement, payment processing, and fulfillment",
    ubiquitous_language_terms=["Order", "Cart", "Checkout", "Payment", "Invoice"],
    aggregates=["Order", "Cart"],
    events=["OrderPlaced", "PaymentReceived", "OrderShipped"],
)

catalog = BoundedContext(
    name="Product Catalog",
    domain="core",
    description="Manages product information, pricing, and inventory",
    ubiquitous_language_terms=["Product", "SKU", "Category", "Price", "Inventory"],
    aggregates=["Product", "Category"],
    events=["ProductCreated", "PriceChanged", "StockDepleted"],
)

billing = BoundedContext(
    name="Billing",
    domain="supporting",
    description="Handles invoicing, payments, and financial reporting",
    ubiquitous_language_terms=["Invoice", "Payment", "Refund", "Credit"],
    aggregates=["Invoice", "Payment"],
    events=["InvoiceGenerated", "PaymentCollected"],
)

notifications = BoundedContext(
    name="Notifications",
    domain="generic",
    description="Sends email, SMS, and push notifications",
    ubiquitous_language_terms=["Notification", "Template", "Channel"],
    aggregates=["Notification"],
    events=["NotificationSent"],
)

# Add contexts
map.add_context(ordering)
map.add_context(catalog)
map.add_context(billing)
map.add_context(notifications)

# Define relationships
map.add_relationship("Ordering", "Billing",
                     ContextRelationship.CUSTOMER_SUPPLIER)
map.add_relationship("Ordering", "Notifications",
                     ContextRelationship.PARTNERSHIP)
map.add_relationship("Ordering", "Product Catalog",
                     ContextRelationship.SHARED_KERNEL)
map.add_relationship("Billing", "Notifications",
                     ContextRelationship.CUSTOMER_SUPPLIER)

print(map.visualize())
```

### Example 6: System Quality Attributes Scenarios

```python
"""
Quality attribute scenario specification.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable


@dataclass
class QualityAttributeScenario:
    """A concrete scenario for a quality attribute (performance, security, etc.)."""
    attribute: str
    id: str
    title: str
    source: str        # Who initiates the stimulus?
    stimulus: str       # What happens?
    environment: str    # Under what conditions?
    artifact: str       # Which part of the system?
    response: str       # What should happen?
    response_measure: str  # How is it measured?


class QualityAttributeAnalyzer:
    """Analyze and document quality attributes for a system."""

    def __init__(self, system_name: str):
        self.system_name = system_name
        self.scenarios: List[QualityAttributeScenario] = []

    def add_scenario(self, scenario: QualityAttributeScenario):
        self.scenarios.append(scenario)

    def generate_report(self) -> str:
        report = [
            f"Quality Attribute Scenarios: {self.system_name}",
            "=" * 60,
        ]

        for scenario in self.scenarios:
            report.extend([
                f"\n[{scenario.id}] {scenario.title}",
                f"Attribute: {scenario.attribute}",
                f"  Source: {scenario.source}",
                f"  Stimulus: {scenario.stimulus}",
                f"  Environment: {scenario.environment}",
                f"  Artifact: {scenario.artifact}",
                f"  Response: {scenario.response}",
                f"  Measure: {scenario.response_measure}",
                "---",
            ])

        return "\n".join(report)


# Performance scenario example
analyzer = QualityAttributeAnalyzer("E-Commerce Platform")

analyzer.add_scenario(QualityAttributeScenario(
    attribute="Performance",
    id="PERF-001",
    title="Product Search Response Time",
    source="User",
    stimulus="Searches for products with multiple filters",
    environment="Normal operation, 10,000 concurrent users",
    artifact="Product Search API",
    response="Search results displayed within threshold",
    response_measure="Average response time < 200ms, p99 < 500ms",
))

analyzer.add_scenario(QualityAttributeScenario(
    attribute="Scalability",
    id="SCAL-001",
    title="Black Friday Traffic Spike",
    source="External user load",
    stimulus="Traffic spike to 10x normal during flash sale",
    environment="Production, auto-scaling enabled",
    artifact="Order Processing System",
    response="System auto-scales and maintains throughput",
    response_measure="Maintain < 1% error rate at 50,000 requests/second",
))

analyzer.add_scenario(QualityAttributeScenario(
    attribute="Availability",
    id="AV-001",
    title="Database Primary Failure",
    source="Infrastructure failure",
    stimulus="Primary database server fails",
    environment="Production, multi-AZ deployment",
    artifact="PostgreSQL Primary",
    response="System fails over to replica within timeout",
    response_measure="Failover completes in < 30 seconds, no data loss",
))

analyzer.add_scenario(QualityAttributeScenario(
    attribute="Security",
    id="SEC-001",
    title="SQL Injection Attempt",
    source="Malicious user",
    stimulus="Submits SQL injection payload in search field",
    environment="Normal operation, WAF and parameterized queries enabled",
    artifact="Product Search API endpoint",
    response="Request is sanitized or rejected, no SQL injection occurs",
    response_measure="100% of injection attempts are blocked",
))

analyzer.add_scenario(QualityAttributeScenario(
    attribute="Maintainability",
    id="MAINT-001",
    title="New Payment Provider Integration",
    source="Development team",
    stimulus="Request to add a new payment provider",
    environment="Development sprint, existing payment abstraction layer",
    artifact="Payment Module",
    response="New provider is integrated without modifying existing providers",
    response_measure="Integration completed in < 5 developer days",
))

print(analyzer.generate_report())
```

## Best Practices

### Architecture Design

- Start with a monolith or modular monolith; extract services only when proven necessary
- Apply Domain-Driven Design for bounded context identification
- Use Architecture Decision Records (ADRs) for all significant decisions
- Model architecture using C4 diagrams (Context, Container, Component, Code)
- Evaluate trade-offs explicitly using a matrix with weighted criteria
- Involve the full team in architecture discussions
- Prototype risky decisions to validate assumptions early

### Communication

- Tailor architecture documentation to the audience (executives, developers, ops)
- Use diagrams and visual models alongside text
- Maintain an architecture repository for all decisions and models
- Present architecture decisions with alternatives and rationale
- Hold regular architecture review sessions

### Governance

- Conduct architecture reviews as part of the development process
- Define and enforce coding standards and design patterns
- Use static analysis and automated checks for architectural rules
- Monitor for architectural drift during implementation
- Keep technical debt visible and manage it proactively

### Keeping Current

- Continuously evaluate new technologies through proof-of-concepts
- Participate in architecture communities (conferences, meetups, online)
- Read industry books and papers on software architecture
- Practice architecture design through side projects and katas
- Learn from incident post-mortems and system failures

## Common Mistakes

- **Over-engineering**: Building for scale or flexibility the system will never need. "You ain't gonna need it" (YAGNI) applies to architecture too.
- **Analysis paralysis**: Spending too much time evaluating options instead of building. Use time-boxed research and prototyping.
- **Ignoring non-functional requirements**: Performance, security, and scalability designed after implementation, not before.
- **Not documenting decisions**: Without documentation, architecture decisions are lost and have to be re-made repeatedly.
- **Big Design Up Front (BDUF)**: Trying to design everything perfectly before starting development leads to wasted effort.
- **Golden hammer**: Using the same technology or pattern for every problem, regardless of fit.
- **Microservices by default**: Starting with microservices adds significant complexity. Extract services only when the monolith proves insufficient.
- **Not involving the team**: Architecture imposed without team input leads to poor adoption and knowledge silos.
- **Ignoring operational concerns**: Architecture that works well in development but is impossible to operate in production.
- **No governance**: Without enforcement, implementation drifts from architecture, creating a "big ball of mud."

## Libraries

### Architecture Tools

| Tool | Purpose |
|------|---------|
| Diagrams (Python) | Code-based infrastructure diagrams |
| Structurizr | C4 model diagramming |
| PlantUML | UML diagram generation from text |
| Mermaid | Markdown-based diagram generation |
| ArchUnit | Java architecture testing |
| NetArchTest | .NET architecture testing |
| ADR Tools | Architecture Decision Record management |
| arc42 | Architecture documentation template |

### Architecture Books

| Book | Author | Focus |
|------|--------|-------|
| Software Architecture in Practice | Bass, Clements, Kazman | Architecture fundamentals |
| Building Evolutionary Architectures | Ford, Parsons, Kua | Evolutionary architecture |
| Domain-Driven Design | Eric Evans | DDD fundamentals |
| Clean Architecture | Robert C. Martin | Uncle Bob's architecture principles |
| Fundamentals of Software Architecture | Richards, Ford | Architecture decision-making |
| Designing Data-Intensive Applications | Martin Kleppmann | Data systems architecture |

## Design Principles

### Separation of Concerns

Divide the system into distinct sections, each addressing a separate concern. This is the most fundamental architectural principle, appearing in layers, modules, services, and components. High cohesion within modules, low coupling between them.

### Modularity and Encapsulation

Each module or service should have a well-defined boundary and interface. Internal implementation details should be hidden. Modules communicate through contracts (interfaces, APIs, events), not by sharing internal state.

### Favor Simplicity

Simple architectures are easier to understand, change, and debug. Complexity should be justified by clear, measurable requirements. Prefer boring technology that the team knows well over exciting technology that adds risk.

### Evolvability

Architecture is never finished. It evolves as requirements change, technology advances, and understanding deepens. Design for change by maintaining loose coupling, using stable interfaces, and keeping deployment pipelines automated.

### Fitness Functions

Use automated checks (fitness functions) to ensure architectural qualities are maintained. Test for performance thresholds, dependency rules, coupling constraints, and security policies as part of the CI/CD pipeline.

## Coding Standards

### Architecture Documentation Structure

```
docs/
  architecture/
    README.md              # Architecture overview
    adr/                   # Architecture Decision Records
      001-use-postgresql.md
      002-use-kafka-for-events.md
    diagrams/
      system-context.png
      container-diagram.png
      deployment-diagram.png
    quality-attributes/
      performance-scenarios.md
      security-scenarios.md
    decisions/
      tech-stack.md
      deployment-strategy.md
```

### ADR Template

```markdown
# ADR-NNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded]

## Context
[Description of the problem and context]

## Decision
[The decision that was made]

## Alternatives Considered
[Other options that were evaluated]

## Consequences
[Positive and negative consequences of the decision]

## Compliance
[How the decision will be enforced]

## Notes
[Additional context, links, references]
```

### Architecture Review Checklist

```
Architecture Review Checklist
=============================

Non-Functional Requirements
- [ ] Performance targets defined (latency, throughput)
- [ ] Scalability plan documented (horizontal/vertical)
- [ ] Availability targets defined (SLA/SLO/SLI)
- [ ] Security requirements addressed
- [ ] Disaster recovery plan documented

Structure
- [ ] Component boundaries are clear
- [ ] Dependencies between components are explicit
- [ ] No circular dependencies
- [ ] Cohesion is high within modules
- [ ] Coupling is low between modules

Technology Choices
- [ ] Technology stack is justified
- [ ] Licensing is compatible
- [ ] Team has necessary skills
- [ ] Technology is mature enough

Operations
- [ ] Deployment process is automated
- [ ] Monitoring and alerting is configured
- [ ] Backup and restore procedures are documented
- [ ] Scaling procedures are documented

Documentation
- [ ] Architecture diagrams are up to date
- [ ] ADRs cover all significant decisions
- [ ] API contracts are documented
- [ ] Runbooks exist for common operations
```
