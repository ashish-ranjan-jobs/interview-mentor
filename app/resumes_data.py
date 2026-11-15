"""
Production 10-Track Resume Data and Interview Specifications for Ashish Ranjan.
4 Java Tracks (J1-J4) + 6 Python & AI Tracks (P1-P6).
"""

from typing import Dict, List, Any

CANDIDATE_PROFILE = {
    "name": "Ashish Ranjan",
    "email": "contact@ashish-ranjan.cloud",
    "linkedin": "https://linkedin.com/in/ashish-ranjan",
    "github": "https://github.com/ashish-ranjan-jobs",
    "portfolio": "https://ashish-ranjan.cloud",
    "education": {
        "institution": "Jadavpur University",
        "degree": "Bachelor of Engineering in Computer Science & Engineering",
        "dates": "2018 – 2022",
        "gpa": "8.09 / 10.0",
        "location": "Kolkata, India"
    },
    "competitive_programming": {
        "leetcode": "1,111+ problems solved (Peak rating: 1877)",
        "codeforces": "590+ problems solved",
        "wbjee": "State Rank 1160 (99.2 percentile among 150,000+ candidates)"
    },
    "companies": {
        "airtel": {
            "name": "Airtel International",
            "role": "Software Engineer",
            "period": "April 2025 – Present",
            "location": "Gurgaon, India",
            "context": "Middleware Team - Airtel Africa Payment Bank / AI Platform"
        },
        "dolcera": {
            "name": "Dolcera",
            "role": "Software Developer / Engineer",
            "period": "October 2022 – March 2025",
            "location": "Hyderabad, India",
            "context": "IP Author SaaS & Legal Tech AI Platform"
        }
    }
}

RESUME_TRACKS: Dict[str, Dict[str, Any]] = {
    # ==================== JAVA TRACKS (4) ====================
    "J1": {
        "id": "J1",
        "code": "Track J1",
        "category": "java",
        "category_title": "Java Production Track",
        "badge_color": "amber",
        "title": "Senior Java Backend & Distributed Systems Engineer",
        "subtitle": "Fintech & High-Throughput Payment Banking",
        "target_roles": [
            "Senior Java Backend Engineer",
            "Fintech Distributed Systems Engineer",
            "Payment Gateway Platform Architect",
            "High-Throughput Java Engineer"
        ],
        "core_stack": [
            "Java 21/17", "Spring Boot 3", "Apache Kafka", "Redis Distributed Locks (SETNX PX + Lua)",
            "Spring State Machine (Sagas)", "Spring Batch", "PostgreSQL", "HikariCP", "async-profiler", "NMT", "AWS EKS"
        ],
        "key_metrics": [
            "350 peak TPS (p99 < 110ms) over 16-partition Kafka",
            "50% container pod reduction (8GB -> 4GB) via NMT off-heap leak resolution",
            "99.9% availability SLO via distributed Sagas & Redis locks",
            "Multi-million daily batch reconciliation with Spring Batch range partitioning"
        ],
        "experience_bullets": [
            "Architected payment routing across banking switches using Java 21, Spring Boot 3, and 16-partition Kafka, sustaining 350 peak TPS (avg 180, p99 < 110 ms) with idempotency and consumer groups; eliminated message loss via manual container acks and DLT retries.",
            "Profiled off-heap memory leaks and resolved thread-pool contention in notification middleware via async-profiler and NMT, slashing pod footprint by 50% (8 GB to 4 GB) at p99 < 120 ms (~200 TPS); isolated network I/O to prevent HikariCP pool starvation.",
            "Eliminated double-debit races across payment pods via multi-layer concurrency control combining Redis distributed locks (SETNX PX + Lua release) and primary DB routing; orchestrated distributed Sagas via Spring State Machine (99.9% monthly availability SLO).",
            "Scaled End-of-Day reconciliation and merchant disbursements on Spring Batch and PostgreSQL, leveraging range partitioning with JdbcPagingItemReader, table partition pruning, and skip listeners to settle multi-million daily records within strict SLAs.",
            "Dolcera: Greenfield backend for IP Author SaaS over Kafka, cutting core API latency by 45% across Hibernate/JPA by eliminating N+1 queries, tuning HikariCP pools, and using Resilience4j circuit breakers with Redis similarity caching (0.94 cosine threshold)."
        ],
        "top_interview_questions": [
            {
                "q": "Walk me through how you diagnosed and resolved the off-heap memory leak using async-profiler and Native Memory Tracking (NMT).",
                "ideal_answer": "Explain that JVM heap (-Xmx) was stable, but pod RSS kept climbing past the 8GB limit leading to OOMKilled by Linux cgroups. Enabled -XX:NativeMemoryTracking=summary. Ran jcmd VM.native_memory baseline, followed by VM.native_memory detail.diff. Identified off-heap growth in direct ByteBuffers / unclosed Netty ByteBuf pools inside the notification middleware, alongside unbounded thread pool creation. Replaced unpooled ByteBuf allocation with pooled, tuned Netty's PooledByteBufAllocator, and capped ForkJoinPool/thread executors with proper rejection policies, cutting memory consumption by 50%."
            },
            {
                "q": "How did you implement double-debit prevention across payment pods with Redis distributed locks? What happens if the lock TTL expires while the transaction is still processing?",
                "ideal_answer": "Used Redis SETNX with unique lock token (UUID) and expiration (PX). Atomic release was done via Lua script verifying token before deleting. To protect against lock expiration mid-flight: 1) kept critical sections minimal, 2) implemented lock lease heartbeat/renewal (watchdog pattern), 3) coupled with database-level idempotent uniqueness constraints (transaction_reference) and database row-level locking (SELECT ... FOR UPDATE) on the ledger balance to ensure double debit is mathematically impossible even in split-brain."
            },
            {
                "q": "How did you configure your 16-partition Kafka topic for payment routing to guarantee strictly ordered, idempotent processing without duplicates?",
                "ideal_answer": "Partitioned by customer/account ID as key so transactions for the same account arrive at the same partition in sequential order. Used transactional producer (enable.idempotence=true, acks=all, max.in.flight.requests.per.connection<=5). On consumer side: disabled auto-commit, used manual container acknowledgment mode (RECORD/MANUAL_IMMEDIATE) only after database transaction commit, and recorded transaction UUID in an idempotent processed_events table with unique index."
            },
            {
                "q": "Explain your Spring State Machine distributed Saga pattern and how compensating transactions are orchestrated if a banking switch fails.",
                "ideal_answer": "Payment workflow follows Choreography/Orchestration via Spring State Machine: States: INITIATED -> DEBIT_RESERVED -> SWITCH_SUBMITTED -> CLEARED / FAILED. If banking switch returns timeout or failure, state machine transitions to COMPENSATION_PENDING, emitting a reversal event that unfreezes/refunds the customer balance and updates ledger audit logs, maintaining 99.9% availability."
            }
        ]
    },

    "J2": {
        "id": "J2",
        "code": "Track J2",
        "category": "java",
        "category_title": "Java Production Track",
        "badge_color": "blue",
        "title": "Senior Java Microservices & Cloud Platform Engineer",
        "subtitle": "Enterprise SaaS Multi-Tenancy & Resilient Cloud",
        "target_roles": [
            "Senior Java Microservices Engineer",
            "Cloud Platform Engineer (Java)",
            "Enterprise SaaS Backend Engineer",
            "Spring Cloud Developer"
        ],
        "core_stack": [
            "Java 21/17", "Spring Boot 3", "Spring Cloud", "OpenAPI", "Resilience4j",
            "Hibernate / JPA", "PostgreSQL", "Docker", "AWS EKS", "HikariCP"
        ],
        "key_metrics": [
            "45% API latency reduction by eliminating N+1 queries & index restructuring",
            "99.9% platform availability across AWS EKS microservices",
            "50% container memory footprint reduction",
            "350 TPS p99 < 110ms with Resilience4j circuit breakers"
        ],
        "experience_bullets": [
            "Architected greenfield backend for IP Author SaaS platform from scratch using Java 17, Spring Boot, and Spring Cloud, orchestrating event-driven microservices over Apache Kafka for asynchronous document ingestion.",
            "Reduced core API response latency by 45% across Hibernate/JPA and PostgreSQL/MySQL (AWS RDS) by eliminating N+1 queries, restructuring SQL execution plans, optimizing indexes, and tuning HikariCP connection pools alongside Redis caching.",
            "Standardized contract-first RESTful APIs to OpenAPI specifications, enforcing stateless OAuth2/JWT authentication and isolating cascading downstream failures using Resilience4j circuit breakers and fallback policies.",
            "Maintained 99.9% platform availability across production microservices on AWS EKS via Jenkins and Docker CI/CD pipelines; slashed redundant compute via SSE streaming and similarity caching."
        ],
        "top_interview_questions": [
            {
                "q": "How do you design multi-tenant isolation in a Spring Boot & PostgreSQL SaaS architecture?",
                "ideal_answer": "Three architectural tiers: 1) Database-per-tenant (highest isolation/cost, enterprise tiers), 2) Schema-per-tenant (shared DB, dedicated schemas, configured via Hibernate MultiTenantConnectionProvider), 3) Discriminator column / Row-Level Security (shared tables with tenant_id and Postgres RLS policies). Tenant context is extracted in API Gateway/filters from JWT claims, stored in ThreadLocal / ScopedContext, and propagated to async threads via TaskDecorator."
            },
            {
                "q": "How did you identify and eliminate N+1 queries in Hibernate/JPA?",
                "ideal_answer": "Enabled hibernate.generate_statistics and SQL logging in dev/staging. Detected queries where loading N parent entities triggered N separate child queries. Fixed by using JOIN FETCH in JPQL, @EntityGraph with attribute nodes, BatchSize(size=50) for batch collection fetching, and DTO projection queries for read-only endpoints."
            },
            {
                "q": "Explain how Resilience4j circuit breakers and bulkheads protect upstream services from downstream latency spikes.",
                "ideal_answer": "Circuit breaker monitors failure/slow call rate over a sliding window (e.g. 100 calls). If slow calls (>2000ms) or errors exceed 50%, state switches from CLOSED to OPEN, immediately returning fallbacks without stressing the failing dependency. Bulkhead pattern limits concurrent calls to downstream service to 20, preventing a slow external partner from exhausting Tomcat threads or HikariCP connections."
            }
        ]
    },

    "J3": {
        "id": "J3",
        "code": "Track J3",
        "category": "java",
        "category_title": "Java Production Track",
        "badge_color": "purple",
        "title": "Senior Java & Enterprise AI Platform Engineer",
        "subtitle": "Enterprise GenAI Gateway & High-Concurrency Streaming",
        "target_roles": [
            "Senior Java & AI Platform Engineer",
            "Enterprise GenAI Java Architect",
            "AI Gateway Backend Engineer",
            "Java LLM Platform Developer"
        ],
        "core_stack": [
            "Java 21/17", "Spring Boot 3", "Apache Kafka", "FastAPI AI Workers",
            "Server-Sent Events (SSE)", "Redis Vector Search (VSS)", "AWS EKS", "Cosine Similarity"
        ],
        "key_metrics": [
            "Redis Vector Search semantic caching at 0.94 cosine similarity threshold",
            "Sub-110ms p99 token streaming latency via SSE and WebFlux/Netty",
            "350 peak TPS over Kafka event-streaming AI pipelines",
            "99.9% availability across high-concurrency Enterprise AI Gateway"
        ],
        "experience_bullets": [
            "Architected Enterprise GenAI gateway in Java 21 & Spring Boot 3 integrating with Python/FastAPI AI workers and external LLMs, delivering low-latency SSE token streaming to thousands of concurrent users.",
            "Engineered semantic response caching using Redis Vector Search (0.94 cosine similarity threshold), slashing redundant LLM calls and API costs by over 60%.",
            "Orchestrated asynchronous document analysis pipelines over 16-partition Kafka topics, balancing load across GPU worker pools with consumer group auto-scaling on AWS EKS.",
            "Tuned JVM off-heap buffers and network socket timeouts to handle long-lived SSE connections without memory leaks or thread starvation."
        ],
        "top_interview_questions": [
            {
                "q": "Why chose Java for an Enterprise GenAI Gateway instead of pure Python?",
                "ideal_answer": "Python excels at model training and rapid AI libraries, but Java Spring Boot offers superior enterprise-grade concurrency, type safety, integration with core banking/enterprise systems, robust OAuth2/JWT security filters, battle-tested connection pooling (HikariCP), and deterministic garbage collection under high concurrent load (thousands of open HTTP SSE connections)."
            },
            {
                "q": "How does semantic caching with Redis Vector Search work, and why did you choose a 0.94 cosine similarity threshold?",
                "ideal_answer": "When a query arrives, it is embedded using an embedding model. A vector similarity query (KNN with HNSW index) checks Redis VSS. 0.94 cosine similarity was chosen based on precision/recall testing: higher (>0.96) had too few cache hits, while lower (<0.90) caused false positives where nuanced technical queries received cached answers to different questions. 0.94 achieved 82% hit rate on recurring queries with <1% semantic divergence."
            },
            {
                "q": "How do you handle thread management for thousands of concurrent Server-Sent Events (SSE) connections in Spring Boot?",
                "ideal_answer": "Traditional Spring MVC allocates 1 Tomcat worker thread per active request. For long-lived streaming connections (5-30 seconds), this exhausts thread pools. Solved by: 1) Using Spring WebFlux / Netty event loops (non-blocking I/O), or 2) Java 21 Virtual Threads (Project Loom) where virtual threads block at minimal memory overhead (few KBs) without blocking OS threads, paired with SseEmitter / Flux<ServerSentEvent>."
            }
        ]
    },

    "J4": {
        "id": "J4",
        "code": "Track J4",
        "category": "java",
        "category_title": "Java Production Track",
        "badge_color": "teal",
        "title": "Senior Full Stack Java Developer",
        "subtitle": "React.js + Next.js + Spring Boot 3 Microservices",
        "target_roles": [
            "Senior Full Stack Java Developer",
            "Full Stack Engineer (React + Spring Boot)",
            "Java / React Architect",
            "Full Stack Developer (Next.js + Java)"
        ],
        "core_stack": [
            "Java 21/17", "Spring Boot 3", "React.js", "Next.js", "TypeScript",
            "Tailwind CSS", "OpenAPI", "PostgreSQL", "Docker", "AWS EKS"
        ],
        "key_metrics": [
            "Full-stack low-latency UX with sub-110ms p99 backend APIs",
            "React token streaming UX with incremental Markdown rendering",
            "45% query latency reduction across PostgreSQL",
            "Clean contract-first OpenAPI integration between React frontend & Spring backend"
        ],
        "experience_bullets": [
            "Engineered responsive full-stack applications integrating modern React/Next.js/TypeScript frontend with resilient Java 17/21 and Spring Boot 3 microservices.",
            "Designed and implemented real-time SSE streaming interfaces in React, rendering streaming markdown and code blocks with smooth chunk buffering and abort controllers.",
            "Built robust RESTful APIs with OpenAPI specs, integrating stateful authentication via HttpOnly JWT cookies and CSRF protection.",
            "Optimized frontend bundle size and backend database queries, cutting end-to-end page load times by 40%."
        ],
        "top_interview_questions": [
            {
                "q": "How do you coordinate API schema changes between React/TypeScript and Spring Boot backend?",
                "ideal_answer": "Used contract-first OpenAPI / Swagger specs. Spring Boot code generates openapi.json, or an OpenAPI yaml contract is the single source of truth. On the frontend, openapi-typescript-codegen generates TypeScript interfaces and API client methods automatically during build, eliminating runtime contract drift and type mismatch bugs."
            },
            {
                "q": "How do you render streaming token chunks in React without causing constant laggy re-renders?",
                "ideal_answer": "Avoid updating full React state on every single token. Use a ref (useRef) to accumulate incoming chunks from ReadableStream, and throttle state updates using requestAnimationFrame or a 50ms batching interval. Markdown parsing is run incrementally on the throttled buffer."
            }
        ]
    },

    # ==================== PYTHON & AI TRACKS (6) ====================
    "P1": {
        "id": "P1",
        "code": "Track P1",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "emerald",
        "title": "Master Python & AI Platform Engineer",
        "subtitle": "High-Throughput Async Microservices & Hybrid RAG",
        "target_roles": [
            "Staff / Senior AI Platform Engineer",
            "Lead Python Engineer",
            "AI Systems Architect",
            "Principal AI Engineer"
        ],
        "core_stack": [
            "Python 3.11", "FastAPI", "AsyncIO", "Apache Kafka", "LangGraph",
            "Hybrid RAG (Dense + BM25 + RRF)", "Redis Vector Search", "AWS EKS", "Qdrant", "RAGAS"
        ],
        "key_metrics": [
            "3,500+ requests/sec at 99.9% uptime across 14 African countries (~200M users)",
            "64% LLM inference cost reduction ($180K+/year savings) via Redis Vector Search",
            "42% automated ticket deflection rate across ~6M conversations (sub-400ms p95)",
            "Recall@10 improvement from 0.58 to 0.81 via Reciprocal Rank Fusion (RRF)"
        ],
        "experience_bullets": [
            "Architected and owned 2 high-throughput Python backend microservices (FastAPI, asyncio) powering AI customer support across 14 African countries (~200M subscriber base), sustaining peak traffic of 3,500+ RPS at 99.9% uptime.",
            "Engineered distributed event-streaming pipelines with Apache Kafka partitioned by conversation ID, coordinating Redis conversational state and FastAPI SSE streaming for ~6M conversations with sub-400ms p95 latency, driving a 42% automated ticket deflection rate.",
            "Designed intelligent routing and semantic similarity caching on Redis Vector Search (0.88 cosine similarity threshold, 82% hit rate), slashing LLM inference costs by 64% ($180K+/year savings).",
            "Implemented multilingual Hybrid RAG over 180K+ telecom support documents combining dense vector embeddings, BM25 lexical search, and Reciprocal Rank Fusion (RRF) reranking.",
            "Orchestrated stateful LangGraph multi-agent workflows featuring dynamic tool calling, PII redaction, human-in-the-loop approval gates, token-bucket rate limiting, and Pydantic-enforced structured outputs.",
            "Established production observability (OpenTelemetry, Prometheus, Grafana) on Kubernetes (AWS EKS), tuning PostgreSQL asyncpg connection pooling and indexes to sustain 99.9% uptime; authored architecture RFCs and SLO budgets.",
            "Dolcera: Boosted retrieval Recall@10 from 0.58 to 0.81 using Hybrid RAG; slashed transformer p95 latency by 45% via ONNX Runtime; integrated RAGAS/TruLens automated CI evaluation gates."
        ],
        "top_interview_questions": [
            {
                "q": "How did you sustain 3,500+ RPS in FastAPI without blocking the Python AsyncIO event loop?",
                "ideal_answer": "Ensured zero synchronous blocking calls in async def route handlers: 1) Used non-blocking drivers exclusively (asyncpg for PostgreSQL, redis-py async, aiokafka for streaming), 2) Offloaded CPU-heavy tasks (tokenization, encryption, embedding compute) to ProcessPoolExecutor / Celery workers with pre-fork pools, 3) Tuned Uvicorn worker count to match CPU cores, and 4) Used uvloop event loop implementation for 2-4x higher throughput."
            },
            {
                "q": "Explain the mathematics and mechanics of Reciprocal Rank Fusion (RRF) in your Hybrid RAG pipeline.",
                "ideal_answer": "Dense embeddings excel at semantic similarity but miss exact keyword identifiers (e.g. error codes, SIM numbers), while BM25 excels at lexical precision but misses conceptual synonyms. RRF combines ranked lists without needing normalized scores: RRF_score(d) = sum(1 / (k + rank_i(d))) where k is a smoothing constant (typically k=60). Documents appearing near the top of both lists receive massive score boosts, increasing Recall@10 from 0.58 to 0.81."
            },
            {
                "q": "How does LangGraph manage stateful multi-agent execution, cycles, and human-in-the-loop approval gates?",
                "ideal_answer": "LangGraph defines a stateful computation graph where nodes are Python functions/agents and edges are conditional transitions. State is a TypedDict/Pydantic model persisted in checkpointers (Redis/PostgreSQL). If an action involves high financial risk (e.g., SIM reactivation or refund), the graph halts at an interrupt_before edge, storing state and dispatching a webhook to human support. Once approved, the graph resumes execution from the exact checkpoint."
            }
        ]
    },

    "P2": {
        "id": "P2",
        "code": "Track P2",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "cyan",
        "title": "Python Backend & Platform Engineer",
        "subtitle": "Distributed Concurrency, Microservices & Data Pipelines",
        "target_roles": [
            "Senior Python Backend Engineer",
            "Python Platform Engineer",
            "Distributed Systems Engineer (Python)",
            "FastAPI Backend Architect"
        ],
        "core_stack": [
            "Python 3.11", "FastAPI", "AsyncIO", "asyncpg", "PostgreSQL",
            "Apache Kafka", "Redis", "Celery", "Docker", "Kubernetes (AWS EKS)"
        ],
        "key_metrics": [
            "3,500+ RPS at 99.9% availability across distributed microservices",
            "45% p95 query latency reduction via asyncpg & index optimization",
            "Distributed task ingestion of 500K+ documents via Celery & Kafka",
            "Token-bucket rate limiting and circuit breakers preventing cascading outages"
        ],
        "experience_bullets": [
            "Engineered high-concurrency Python backend microservices using FastAPI, asyncio, and asyncpg, handling thousands of concurrent requests with sub-50ms p95 latencies.",
            "Designed event-driven message architectures with Apache Kafka, guaranteeing partitioned ordering and consumer idempotency across distributed worker nodes.",
            "Structured robust database schemas and connection pooling on PostgreSQL, eliminating query bottlenecks and deadlocks using partition pruning and optimized composite indexes.",
            "Implemented distributed task queues with Celery and Redis, incorporating retry policies, exponential backoff, and dead-letter queues."
        ],
        "top_interview_questions": [
            {
                "q": "How do you handle database connection pooling in high-concurrency async Python services?",
                "ideal_answer": "Default ORM pools can easily exhaust PostgreSQL connections if every coroutine acquires a connection. Used asyncpg.create_pool with min_size=20, max_size=50, max_queries=50000. Connections are acquired only for the exact duration of query execution using async with pool.acquire(), not held during external HTTP or LLM API calls. For horizontal scaling across multiple pods, deployed PgBouncer in transaction pooling mode."
            },
            {
                "q": "How do you implement distributed rate limiting with Redis without race conditions?",
                "ideal_answer": "Used the Token Bucket or Sliding Window Log algorithm implemented in an atomic Lua script executed via EVALSHA in Redis. The Lua script checks current token count against elapsed time, decrements tokens, and sets key TTL in a single atomic operation, preventing TOCTOU (time-of-check to time-of-use) race conditions across concurrent application pods."
            }
        ]
    },

    "P3": {
        "id": "P3",
        "code": "Track P3",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "fuchsia",
        "title": "GenAI, LLM & Agentic AI Engineer",
        "subtitle": "Multi-Agent Orchestration, Guardrails & Evaluation",
        "target_roles": [
            "Generative AI Engineer",
            "LLM Application Developer",
            "Agentic AI Systems Engineer",
            "LangGraph Engineer"
        ],
        "core_stack": [
            "LangGraph", "LangChain", "Multi-Agent Systems", "RAGAS", "TruLens",
            "Hybrid RAG", "Qdrant", "Redis Vector Search", "Pydantic", "Tool Calling"
        ],
        "key_metrics": [
            "Stateful LangGraph multi-agent orchestration with bounded reflection loops",
            "64% LLM cost reduction via 82% semantic cache hit rate",
            "Automated CI/CD quality evaluation gates benchmarking groundedness (>0.88)",
            "Recall@10 improvement from 0.58 to 0.81 via dense + BM25 hybrid retrieval"
        ],
        "experience_bullets": [
            "Orchestrated stateful multi-agent systems using LangGraph, incorporating bounded reflection cycles, dynamic tool dispatching, and fallback routing.",
            "Engineered hybrid RAG pipelines with vector databases (Qdrant, Redis) combining semantic embeddings and lexical search with cross-encoder rerankers.",
            "Built automated LLM evaluation gates into CI/CD pipelines using RAGAS and TruLens, measuring faithfulness, context precision, and hallucination rates before deployment.",
            "Enforced strict output schemas using Pydantic and function calling, eliminating unparseable model responses and prompt injection vulnerabilities."
        ],
        "top_interview_questions": [
            {
                "q": "How do you evaluate whether a RAG system is actually working before deploying to production?",
                "ideal_answer": "Used RAGAS metrics on a curated golden dataset of 200+ question-answer-context pairs: 1) Faithfulness / Groundedness: Is the answer derived solely from the retrieved context (preventing hallucinations)? 2) Context Recall: Did retrieval find all necessary information? 3) Context Precision: Is the retrieved chunk signal-to-noise ratio high? 4) Answer Relevance: Does the output directly answer the prompt? Automated this as a gating step in GitHub Actions CI."
            },
            {
                "q": "How do you prevent infinite execution loops in autonomous agent reflection cycles?",
                "ideal_answer": "In LangGraph, state tracks an iteration_count and max_iterations limit (typically 3). The conditional edge checks if iteration_count >= max_iterations, forcing a transition to a fallback/escalation node. Additionally, evaluate convergence: if reflection score does not improve between cycles, break the loop immediately."
            }
        ]
    },

    "P4": {
        "id": "P4",
        "code": "Track P4",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "violet",
        "title": "Applied ML & Inference Engineer",
        "subtitle": "Model Serving Optimization, ONNX Runtime & Semantic Search",
        "target_roles": [
            "Applied ML Engineer",
            "Machine Learning Engineer (Inference)",
            "NLP Engineer",
            "Embedding & Retrieval Engineer"
        ],
        "core_stack": [
            "PyTorch", "Hugging Face", "ONNX Runtime", "FAISS", "Cross-Encoders",
            "FastAPI", "Vector Embeddings", "Quantization (INT8/FP16)", "Latency Profiling"
        ],
        "key_metrics": [
            "45% inference latency cut (320ms to 175ms) via ONNX Runtime graph optimization",
            "Sub-50ms p95 semantic retrieval latency across large embedding spaces",
            "Recall@10 improvement from 0.58 to 0.81",
            "1,200 QPS load-tested multi-stage inference pipeline"
        ],
        "experience_bullets": [
            "Optimized deep learning transformer inference using ONNX Runtime with operator fusion and quantization, cutting p95 latency from 320ms to 175ms.",
            "Designed high-accuracy retrieval systems combining bi-encoders for candidate retrieval and cross-encoders for re-ranking.",
            "Engineered vector index architectures on FAISS and pgvector, evaluating Flat vs IVF vs HNSW trade-offs for latency and recall.",
            "Monitored inference drift and latency anomalies in production using Prometheus metrics and OpenTelemetry tracing."
        ],
        "top_interview_questions": [
            {
                "q": "Walk me through how ONNX Runtime optimization reduced inference latency by 45%.",
                "ideal_answer": "Exported PyTorch HuggingFace transformer to ONNX format. Applied ONNX Runtime graph optimizations: constant folding, redundant node elimination, and transformer-specific operator fusion (fusing Multi-Head Attention and LayerNorm into single CUDA kernels). Applied dynamic INT8 quantization to weights, reducing memory bandwidth pressure and accelerating matrix multiplications."
            },
            {
                "q": "What are the trade-offs between HNSW and IVFFlat vector index algorithms in FAISS?",
                "ideal_answer": "IndexFlatIP is exact but O(N) linear scan, unacceptable at scale. IndexIVFFlat clusters vectors into Voronoi cells; at query time it checks only nprobe closest centroids. Fast build time and low RAM, but sensitive to nprobe tuning. IndexHNSW builds a hierarchical navigable small-world graph; delivers incredible recall and lowest query latency (sub-5ms), but consumes 2-3x more RAM and has slower index build/insert times."
            }
        ]
    },

    "P5": {
        "id": "P5",
        "code": "Track P5",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "rose",
        "title": "Full Stack AI Web Developer",
        "subtitle": "React 19, Next.js 15, TypeScript & FastAPI Token Streaming",
        "target_roles": [
            "Full Stack AI Developer",
            "AI Full Stack Engineer",
            "Next.js / React AI Engineer",
            "Full Stack Engineer (React + Python)"
        ],
        "core_stack": [
            "React 19", "Next.js 15", "TypeScript", "Tailwind CSS", "FastAPI",
            "Server-Sent Events (SSE)", "WebSockets", "Token Streaming UX", "PostgreSQL"
        ],
        "key_metrics": [
            "Zero-flicker token streaming UX with smooth Markdown and syntax rendering",
            "Sub-400ms p95 end-to-end response times across web applications",
            "40% reduction in UI latency via server components and optimistic updates",
            "Stateless JWT auth with HttpOnly secure cookie persistence"
        ],
        "experience_bullets": [
            "Built responsive full-stack AI web applications pairing React 19/Next.js frontend with high-throughput Python FastAPI backends.",
            "Architected seamless SSE streaming interfaces, handling real-time token rendering, code block highlighting, and user interruption signals.",
            "Enforced end-to-end type safety between FastAPI Pydantic schemas and TypeScript client components.",
            "Designed accessible, mobile-first interfaces using Tailwind CSS with glassmorphic dark-mode aesthetics."
        ],
        "top_interview_questions": [
            {
                "q": "How do you implement client-side token cancellation when a user clicks 'Stop Generating'?",
                "ideal_answer": "Instantiate an AbortController in JavaScript. Pass its signal (abortController.signal) to the fetch() call opening the SSE stream. When user clicks 'Stop', call abortController.abort(), which immediately closes the TCP socket and cancels the ReadableStream reader. On the FastAPI backend, catch the ClientDisconnect exception to terminate the background LLM inference task."
            },
            {
                "q": "When should you use Next.js Server Components (RSC) vs Client Components in an AI chat application?",
                "ideal_answer": "Use Server Components for static layouts, fetching past session lists, and initial page shells (zero JavaScript bundle overhead, faster First Contentful Paint). Use Client Components ('use client') exclusively where interactivity and browser state are needed: message inputs, streaming token state, copy-to-clipboard buttons, and WebSocket/SSE event listeners."
            }
        ]
    },

    "P6": {
        "id": "P6",
        "code": "Track P6",
        "category": "python",
        "category_title": "Python & AI Production Track",
        "badge_color": "indigo",
        "title": "AI Infrastructure & MLOps Engineer",
        "subtitle": "High-Throughput Model Serving, vLLM, Ray & GPU Orchestration",
        "target_roles": [
            "AI Infrastructure Engineer",
            "MLOps Engineer",
            "High-Performance Model Serving Engineer",
            "Kubernetes GPU Engineer"
        ],
        "core_stack": [
            "vLLM", "Triton Inference Server", "Ray Distributed", "Kubernetes (AWS EKS)",
            "PagedAttention", "FP8 / INT8 Quantization", "Prometheus / Grafana", "Terraform"
        ],
        "key_metrics": [
            "High-throughput model serving with continuous batching and PagedAttention",
            "TokenOps Kubernetes gateway monitoring TTFT and TPOT latencies",
            "Zero-downtime rolling model updates on AWS EKS clusters",
            "Automated infrastructure provisioning using Terraform and Helm"
        ],
        "experience_bullets": [
            "Engineered scalable LLM serving infrastructure leveraging vLLM and Triton Inference Server, maximizing GPU utilization via continuous batching.",
            "Optimized KV-cache memory allocation using PagedAttention and FP8 quantization, increasing maximum concurrent request capacity by 3x.",
            "Deployed and scaled distributed model workers using Ray on Kubernetes (AWS EKS), integrating auto-scaling policies tied to queue depth.",
            "Implemented TokenOps observability tracking Time to First Token (TTFT) and Time Per Output Token (TPOT) with Prometheus and Grafana."
        ],
        "top_interview_questions": [
            {
                "q": "Explain how PagedAttention solves the KV-cache memory fragmentation bottleneck in LLM serving.",
                "ideal_answer": "In standard LLM serving, KV-cache memory is pre-allocated contiguously for the maximum sequence length (e.g. 2048 tokens). Because sequence lengths vary, 60-80% of GPU memory is wasted on internal and external fragmentation. PagedAttention borrows virtual memory paging from operating systems: it divides KV-cache into fixed-size physical blocks (e.g. 16 tokens). Logical blocks are mapped to non-contiguous physical blocks via a block table, eliminating fragmentation and enabling near-zero memory waste."
            },
            {
                "q": "What is the difference between TTFT and TPOT, and which architectural levers optimize each?",
                "ideal_answer": "TTFT (Time to First Token) is the prefill latency: how long until the model processes the prompt and generates token #1. It is compute-bound, optimized by prompt caching, flash-attention, tensor parallelism, and fast network routing. TPOT (Time per Output Token) is the decode latency: time between subsequent tokens. It is memory-bandwidth bound, optimized by continuous batching, PagedAttention, weight quantization (FP8/INT8), and speculative decoding."
            }
        ]
    }
}
def build_resume_system_prompt(track_id: str, mode: str = "full", custom_instructions: str = None) -> str:
    track = RESUME_TRACKS.get(track_id)
    if not track:
        return "You are an expert technical interviewer conducting a mock interview."

    bullets_text = "\n".join(f"- {b}" for b in track["experience_bullets"])
    metrics_text = "\n".join(f"- {m}" for m in track["key_metrics"])
    stack_text = ", ".join(track["core_stack"])

    mode_instructions = {
        "full": """
CONDUCTING A COMPLETE TECHNICAL INTERVIEW LOOP (4 Phases):
- Phase 1: Candidate Introduction & Role Overview (Ask candidate to introduce themselves and summarize their current work at Airtel International).
- Phase 2: Resume Deep-Dive & Metric Verification (Pick 1-2 major claims from the resume below, ask them to explain the architecture and how they achieved the metric).
- Phase 3: System Architecture / Design Scenario (Present a practical scenario requiring architectural design relevant to their stack).
- Phase 4: Algorithmic / Coding or Edge-Case Probing & Wrap-Up (Test edge cases, failure scenarios, and provide brief closing feedback).
""",
        "grill": """
CONDUCTING A "GRILL MY RESUME" BAR RAISER DEFENSE:
- You are a skeptical, elite-tier FAANG / Google Bar Raiser interviewer.
- You have scrutinized this candidate's exact resume below. You test whether they truly built these systems or are exaggerating.
- Immediately challenge their strongest claims (e.g., TPS numbers, RPS scale, memory reduction percentages, specific latency numbers, or cost savings).
- Probe failure modes: "What broke when traffic doubled?", "What happens if Kafka rebalances during a batch write?", "Why didn't you use X instead of Y?", "How did you measure p99 latency without observer bias?"
- Demand exact architectural specifics, data structures, and edge-case handling. Reject hand-waving politely but firmly.
""",
        "system_design": """
CONDUCTING A DEDICATED SYSTEM DESIGN ROUND:
- Present an open-ended, high-scale system design problem aligned with this track's domain.
- Guide the candidate through: Functional/Non-functional Requirements -> Capacity Estimation -> High-Level Architecture -> Deep Dive into bottlenecks -> Fault tolerance & data consistency.
- Expect ASCII diagrams, API signatures, database schema choices, and scaling strategies.
""",
        "coding": """
CONDUCTING A LIVE CODING & ALGORITHMIC ROUND:
- Present a realistic coding challenge (LeetCode Medium to Hard level) that tests algorithms, data structures, or concurrency.
- Ask for clarification and time/space complexity before they write code.
- Review their submitted code thoroughly for edge cases, clean syntax, and idiomatic best practices.
""",
        "behavioral": """
CONDUCTING A SENIOR / STAFF BEHAVIORAL & LEADERSHIP INTERVIEW (STAR Method):
- Ask probing behavioral questions on architectural disagreements, handling severe production outages, prioritizing technical debt vs product deadlines, and authoring cross-team RFCs.
- Enforce the STAR structure: Situation, Task, Action, Result. Require concrete details on what THE CANDIDATE specifically did.
"""
    }.get(mode, "Conduct a rigorous technical mock interview.")

    system_prompt = f"""You are conducting an interactive, professional mock interview specifically tailored to Ashish Ranjan's resume for:
TRACK: {track['title']} ({track['subtitle']})
TARGET ROLES: {", ".join(track['target_roles'])}
CATEGORY: {track['category'].upper()}

============================================================
CANDIDATE'S VERIFIED RESUME SPECIFICATION (SCRUTINIZE CAREFULLY):
Candidate Name: {CANDIDATE_PROFILE['name']}
Education: {CANDIDATE_PROFILE['education']['institution']} - {CANDIDATE_PROFILE['education']['degree']} ({CANDIDATE_PROFILE['education']['dates']}, GPA: {CANDIDATE_PROFILE['education']['gpa']})
Algorithmic Signal: {CANDIDATE_PROFILE['competitive_programming']['leetcode']} | {CANDIDATE_PROFILE['competitive_programming']['codeforces']}
Current Company: {CANDIDATE_PROFILE['companies']['airtel']['name']} ({CANDIDATE_PROFILE['companies']['airtel']['period']}) - {CANDIDATE_PROFILE['companies']['airtel']['context']}
Previous Company: {CANDIDATE_PROFILE['companies']['dolcera']['name']} ({CANDIDATE_PROFILE['companies']['dolcera']['period']}) - {CANDIDATE_PROFILE['companies']['dolcera']['context']}

CLAIMED CORE TECHNICAL STACK:
{stack_text}

CLAIMED KEY METRICS & IMPACT:
{metrics_text}

DOCUMENTED WORK EXPERIENCE BULLETS:
{bullets_text}
============================================================

INTERVIEW STYLE & MODE:
{mode_instructions}

CRITICAL RULES FOR THE INTERVIEWER:
1. Conduct the interview iteratively and conversationally. Speak in first person as the interviewer ("I see here that you...", "Could you walk me through...").
2. Ask ONE focused question or scenario at a time. Let the candidate respond before asking follow-ups.
3. If the candidate submits code, architecture designs, or ASCII diagrams, analyze it with real senior-engineer depth.
4. When the candidate asks for a hint, give progressive guidance (Nudge -> Direction -> Solution sketch).
5. If the candidate requests an ASCII diagram, draw a crisp ASCII component or dataflow diagram.
6. Calibrate your difficulty to top tech companies (Google, Meta, Uber, Stripe, Amazon).
"""
    if custom_instructions:
        system_prompt += f"\nADDITIONAL USER INSTRUCTIONS:\n{custom_instructions}\n"

    return system_prompt
