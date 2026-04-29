# FreshRSS AI Intelligence Pipeline — Product Vision Spec

## Purpose

This product turns a self-hosted FreshRSS instance into an AI-assisted intelligence system for curated reading, weekly
digests, and higher-signal article discovery. FreshRSS remains the system of record for subscriptions and reading, while
an external worker reads articles through the Google Reader compatible API, enriches them with AI-derived metadata, and
publishes the resulting outputs back into the reading workflow.

## Product Vision

The system should help transform a large stream of RSS items into a smaller set of actionable insights. Instead of only
collecting feeds, it should classify articles, detect notable signals, generate readable digests, and publish those
results in a standard feed format that can be consumed again by FreshRSS and also by other readers such as Inoreader.

The long-term vision is a local-first intelligence layer on top of RSS. Raw content ingestion stays in FreshRSS, AI
processing can run locally or in the cloud, and output remains portable through open standards such as Atom or RSS and
through write-back tags on original articles.

## Product Goals

- Use FreshRSS as the single source of truth for subscribed feeds and article retrieval.
- Read input articles through the Google Reader compatible API rather than screen scraping or database coupling.
- Run AI processing that can assign tags, identify trends, produce digests, and generate higher-level intelligence
  reports.
- Publish result feeds in a standard format that can be subscribed to in both FreshRSS and Inoreader.
- Write selected AI labels or states back to original FreshRSS articles through supported API flows, using token-based
  write operations where needed.
- Keep the architecture local-first, modular, and easy to evolve from MVP to a more capable pipeline.

## Non-Goals

- Replacing FreshRSS as the primary feed reader or subscription manager.
- Building a proprietary reader UI for the first phase.
- Depending on Inoreader as a core system component; Inoreader is only a potential consumer of the published output
  feed.
- Full autonomous decision-making on behalf of the user, such as deleting feeds or changing subscriptions automatically.

## Core Use Cases

### Weekly digest

The system should summarize the most important developments across selected feeds over the last seven days and publish
the output as a feed entry. This digest should be readable inside FreshRSS and portable to other readers via a standard
feed URL.

### Monthly insights

The system should identify the most notable findings, recurring themes, and surprising developments from a longer time
window such as the last month. This output is more analytical than a digest and may become its own report-style feed.

### Article intelligence tagging

The system should assign AI-derived labels to individual articles, such as topical tags, signal strength, or whether an
item belongs in a digest. These tags should be visible and usable inside FreshRSS through its Google Reader compatible
API model for tags and write actions.

### High-signal monitoring

The system should identify unusual or especially important items and optionally publish them to a dedicated high-signal
feed. This supports fast scanning without losing the original article context.

## Users and Environment

The target environment is a self-hosted, automation-friendly setup centered on FreshRSS. The intended user values
privacy, local control, open standards, and composable infrastructure over SaaS convenience.[cite:46]

The system must therefore prefer:

- local deployment,
- open feed formats,
- API-driven integration,
- low operational coupling to proprietary services.

## System Context

FreshRSS acts as the ingestion and reading layer and provides Google Reader compatible API access for article retrieval,
tag listing, and token-based write operations.

An external worker reads candidate articles from FreshRSS, normalizes them, sends them to an AI processor, receives
structured outputs such as tags and summaries, and then writes results back in two ways:

- as article-level tags on original entries in FreshRSS,
- as generated Atom or RSS feeds containing digests and reports that can be subscribed to by FreshRSS and
  Inoreader.[cite:33]

## High-Level Requirements

### Functional requirements

- Authenticate against FreshRSS using the Google Reader compatible API.
- Read articles from one or more defined streams, such as reading list, categories, or specific
  feeds.
- Normalize article data into an internal schema with stable identifiers.
- Send selected article content to an AI model for classification and summarization.
- Store AI results per article, including tags, importance, and digest eligibility.
- Write supported AI tags back to FreshRSS entries through API write actions.
- Generate at least one standards-compliant output feed, preferably Atom, for weekly digests.
- Optionally generate additional feeds such as monthly insights or high-signal alerts.
- Ensure the produced feeds are consumable by multiple feed readers, not just FreshRSS.

### Non-functional requirements

- Local-first deployment with optional cloud AI backends.
- Modular architecture so that the AI provider can be swapped without redesigning the pipeline.
- Idempotent processing so articles are not repeatedly tagged or duplicated in output feeds.
- Clear separation between ingestion, inference, publishing, and write-back.
- Robust handling of partial failures, such as AI timeout, API failure, or feed publishing issues.

## Architecture Overview

| Layer          | Responsibility                                                                         |
|----------------|----------------------------------------------------------------------------------------|
| FreshRSS       | Feed ingestion, subscription management, human reading interface, API source of truth. |
| Ingest worker  | Reads articles from FreshRSS API, filters by stream/time window, normalizes records.   |
| AI processor   | Produces tags, summaries, trend clusters, digest candidates, and report content.       |
| State store    | Tracks processed entries, hashes, assigned tags, and report membership.                |
| Feed publisher | Writes Atom or RSS output feeds for digest and reports.                                |
| Tag writer     | Applies AI-derived labels back to FreshRSS articles via API write operations.          |

## Key Data Flows

### Ingestion flow

1. Authenticate to FreshRSS through the Google Reader compatible API.
2. Request articles from configured streams or categories.
3. Normalize returned items into an internal representation.
4. Skip items already processed, unless content changed.

### Intelligence flow

1. Extract title, source, URL, publication date, and article content or summary.
2. Send selected fields to a local or cloud AI model.
3. Receive structured outputs such as topical tags, signal level, summary text, and digest relevance.
4. Persist the result for later feed generation and write-back.

### Publishing flow

1. Group relevant results by reporting window, such as weekly or monthly.
2. Generate HTML content blocks suitable for Atom or RSS entries.
3. Publish feed files at stable URLs.
4. Subscribe those URLs in FreshRSS and optionally Inoreader.

### Write-back flow

1. Request a FreshRSS write token where required.
2. Apply selected labels to original article IDs using tag edit endpoints.
3. Record success or failure in the local state store to avoid duplicate writes.

## Proposed Output Types

| Output                | Description                                                                | Primary consumer           |
|-----------------------|----------------------------------------------------------------------------|----------------------------|
| AI article tags       | Labels such as topic, importance, or digest inclusion on original entries. | FreshRSS UI and automation |
| Weekly digest feed    | Periodic summary of the most important developments from the last week.    | FreshRSS, Inoreader        |
| Monthly insights feed | More analytical feed with notable findings and recurring themes.           | FreshRSS, Inoreader        |
| High-signal feed      | Stream of especially important or unusual items.                           | FreshRSS, Inoreader        |

## Tagging Strategy

AI-generated tags should be namespaced to avoid collisions with human tags. A predictable scheme such as
`ai/topic/security`, `ai/signal/high`, or `ai/report/weekly` makes downstream filtering easier.

The first version should keep the tag model intentionally small:

- topic tags,
- signal or importance tags,
- digest eligibility tags,
- optional review-required tag.

## Deployment Principles

The preferred deployment model is local and containerized. FreshRSS already runs as the ingestion platform, while the
worker, state store, and feed publisher can run as separate containers or as a small combined service.

The system should support two AI backends without architectural change:

- local inference endpoint,
- cloud inference endpoint.

The choice of backend should only affect configuration, not overall system behavior.

## MVP Scope

The first usable version should include:

- FreshRSS as the only ingestion source,
- article retrieval through the Google Reader compatible API,
- AI tagging of articles,
- a single published Atom feed for weekly digests,
- write-back of selected AI tags to FreshRSS,
- a small local state database for deduplication and job bookkeeping.

The MVP should avoid premature complexity such as many report types, advanced ranking models, or multi-reader-specific
behavior.

## Future Extensions

After the MVP, the system could grow toward:

- monthly intelligence reports,
- source-level trust or weighting rules,
- topic-specific digest feeds,
- user feedback loops that refine tagging quality,
- richer ranking based on novelty, relevance, and repeated cross-source confirmation,
- optional integration with automation tools such as n8n for orchestration.

## Acceptance Criteria

The product vision is satisfied when all of the following are true:

- FreshRSS remains the canonical source for feed ingestion and article retrieval.
- Articles can be read through the Google Reader compatible API and processed by an AI service.
- The system can write useful AI labels back to articles in FreshRSS through supported API flows.
- The system can publish a standards-compliant digest feed that can be subscribed to by FreshRSS and
  Inoreader.
- The overall design stays local-first, modular, and portable.
