# Ryūshi Product Vision Spec

## Purpose

Ryūshi is a self-hosted, reader-agnostic knowledge layer for RSS and other information sources. Its purpose is to reduce
information overload by turning streams of articles into a curated, searchable, tagged, and summarized knowledge
timeline that can be consumed in different clients and exported into other systems.

Ryūshi is not intended to replace every RSS reader. Instead, it sits above existing readers such as FreshRSS and
Miniflux, ingests selected content through their APIs and webhooks, enriches it with AI-assisted processing, and stores
only the most relevant results as durable knowledge items.

## Product Vision

Ryūshi helps users move from “too many unread items” to “a focused personal flow of knowledge.” It combines selective
ingestion, summarization, tagging, prioritization, and digest generation into one open, extensible system that can later
support multiple frontends and integrations.

The long-term vision is “Raycast for information”: a system that lets users collect, search, filter, and act on
knowledge across feeds, topics, and sources instead of passively consuming every incoming article. In this model,
articles become structured knowledge items that can be explored by timeline, topic, tag, and
priority.

## Problem Statement

RSS readers are excellent at collecting content, but they often leave users with a large unread backlog and limited help
in identifying what is actually important. AI-oriented readers such as Folo show the appeal of summaries,
categorization, and digest-style reading, but Ryūshi aims to provide this in a self-hosted and reader-agnostic
architecture rather than as a tightly coupled reader product.

Many knowledge tools also focus more on manual organization than on automated ingestion and processing. Ryūshi addresses
this gap by acting as an ETL-style layer for personal knowledge: extracting items from upstream readers, transforming
them into structured knowledge objects, and loading only the valuable results into its own
store.

## Product Principles

- Self-hosted first: the system should run locally or on a private server and keep user data under the user’s control.
- Reader-agnostic: ingestion should work with FreshRSS first and Miniflux next, using their documented APIs and webhook
  mechanisms.
- Selective storage: Ryūshi should not become a full archive of every feed item; it should persist only selected or
  sufficiently relevant items.
- AI-assisted, not AI-dependent: AI should improve summaries, tags, and prioritization, but the system should still have
  a deterministic baseline via rules and filters.
- Modular by design: adapters, processing, storage, and outputs should be separated so that new inputs and outputs can
  be added later without redesigning the core.
- Open and integratable: the core should expose a clean API and predictable data model so that additional clients,
  plugins, and automations can be built around it.

## Core User Value

Ryūshi gives users a smaller set of higher-quality items to read, review, and reuse. Instead of browsing every feed
manually, users get a focused timeline of relevant knowledge items enriched with summaries, tags, and priority
labels.

The system also creates leverage beyond reading. Once items are structured and tagged, they can power topic-based
filtering, later AI features, digests, and exports to other tools without requiring the user to reprocess the same
content manually.

## Primary Users

### Knowledge-focused RSS users

These users already follow blogs, newsletters, or technical sources through RSS but want help reducing noise and
surfacing the most valuable material. They are likely to use self-hosted readers such as FreshRSS or Miniflux and care
about control, privacy, and extensibility.

### Personal knowledge management users

These users maintain a second-brain workflow and want a bridge between incoming information and their long-term
knowledge system. They do not only want to read articles; they want selected items to become reusable knowledge objects.

### Builders and tinkerers

These users want an open system that can be extended with workflows, plugins, and local AI models. They are likely to
combine Ryūshi with tools such as Ollama, ntfy, Markdown-based notes, or automation systems.

## Scope Definition

## In Scope for MVP

- FreshRSS ingestion through the Google Reader compatible API.
- Miniflux support through REST API and/or webhooks as the second adapter path.
- Local or self-hosted AI processing for summary, tag suggestion, and priority classification, with Ollama as an example
  deployment path.
- A persistent knowledge store for selected items only.
- Basic item model with title, source, URL, summary, tags, priority, timestamps, and status.
- A timeline view and a daily digest output.
- Tag-based filtering and search.

## Out of Scope for MVP

- Full feed management and reader replacement.
- Multi-user collaboration and permissions.
- Advanced knowledge graph or vector database capabilities.
- Broad plugin marketplace.
- Many downstream integrations such as Notion, Obsidian, or task managers.
- Fully autonomous agents or MCP orchestration.

## MVP Definition

The MVP proves one end-to-end flow: a new article arrives in FreshRSS or Miniflux, Ryūshi ingests it, extracts or
normalizes the content, generates a short summary, proposes tags, assigns a priority level, and stores it only if it
meets the configured relevance threshold.

The stored item then appears in a timeline and can also be included in a daily digest. This flow demonstrates the core
promise of Ryūshi: transforming feed noise into a manageable knowledge stream.

## Functional Requirements

### Inputs

- Connect to FreshRSS using the Google Reader compatible API to fetch subscriptions and article streams.
- Connect to Miniflux using REST API access and webhook events for entry activity.
- Support polling first, with webhook-driven ingestion where available.
- Allow simple source-level filters, such as feed, category, or keyword selection.

### Processing

- Normalize incoming article metadata into a common internal item format.
- Extract fuller article text where possible if the feed content is incomplete.
- Generate a concise summary.
- Suggest 3–5 tags.
- Classify priority into at least `must-read`, `skim`, and `noise`.
- Apply configurable thresholds to decide whether an item is persisted.

### Storage

- Persist only selected knowledge items, not the full upstream feed corpus.
- Store original source metadata so items remain traceable to their upstream reader and source.
- Support many-to-many tags to allow future topic clustering and filtering.

### Outputs

- Timeline view ordered by time and filterable by tag or priority.
- Daily digest in Markdown or notification-friendly text.
- Basic API access for future clients and exports.

## Non-Functional Requirements

- Self-hostable with a lightweight local deployment path.
- Modular architecture with clear boundaries between adapters, processing, storage, and outputs.
- Reasonable local-first privacy assumptions, especially when using local models such as Ollama.
- Deterministic fallback behavior when AI is unavailable.
- Extensible data model for future topic models, semantic search, and additional outputs.

## Information Architecture

Ryūshi’s core data flow should follow this model:

1. **Ingest**: Pull or receive article data from FreshRSS or Miniflux.
2. **Normalize**: Convert source-specific data into a common internal schema.
3. **Enrich**: Generate summary, tags, and priority.
4. **Select**: Keep only relevant items based on rules or scores.
5. **Persist**: Save as knowledge items with source traceability.
6. **Deliver**: Expose via timeline, digest, and later APIs or external outputs.

## Conceptual Data Model

| Entity           | Purpose                                           |
|------------------|---------------------------------------------------|
| `source`         | Upstream reader/feed/category definition          |
| `raw_item`       | Temporary representation of incoming source data  |
| `knowledge_item` | Persisted curated item with summary and priority  |
| `tag`            | User-facing topic or classification label         |
| `item_tag`       | Many-to-many mapping between item and tag         |
| `digest`         | Daily or weekly grouped output                    |
| `processing_run` | Optional trace of ingestion and enrichment events |

## Priority Model

Ryūshi should begin with a simple three-level priority model:

| Priority    | Meaning                                                    |
|-------------|------------------------------------------------------------|
| `must-read` | High-value item worth direct attention                     |
| `skim`      | Useful item worth scanning or saving                       |
| `noise`     | Low-value item that should not clutter the knowledge store |

This model is intentionally simple so users can understand and trust the system early. It also creates a clear boundary
for selective persistence and digest generation.

## Tagging Model

Tags are a core part of the Ryūshi product vision. They serve as both a user-facing organization layer and a bridge to
future AI features such as topic clustering, semantic grouping, and better search.

The MVP should support:

- AI-suggested tags.
- Manual correction later.
- Filtering timeline views by one or more tags.
- Using tags as a first approximation of “topics.”

## API Direction

Ryūshi should expose a clean application API around its curated data rather than mirroring the upstream reader APIs.
This API should center on knowledge items, tags, priorities, timeline queries, and digest retrieval.

For MVP, a simple HTTP API is sufficient. Over time, this can evolve into a richer query layer once the internal model
stabilizes.

## Success Criteria

The MVP is successful if a user can:

- Connect at least one upstream reader source.
- Receive automatically processed items without manual copy/paste.
- See a timeline with fewer but more relevant entries.
- Filter those entries by tags or priority.
- Receive a useful daily digest.

## Risks and Open Questions

- Full-text extraction quality may vary depending on source structure.
- AI-generated tags and summaries may need confidence scores or manual correction paths.
- Polling versus webhooks may differ in reliability across reader systems.
- The product boundary between “AI layer” and “reader replacement” must remain clear to avoid scope creep.
- A future decision is needed on whether Android, web, or digest output becomes the primary first client.

## Positioning Statement

Ryūshi is a self-hosted, reader-agnostic AI layer for RSS and knowledge workflows. It turns selected articles from tools
like FreshRSS and Miniflux into summarized, tagged, prioritized knowledge items that can be explored through a timeline
and digests instead of an overwhelming unread list.
