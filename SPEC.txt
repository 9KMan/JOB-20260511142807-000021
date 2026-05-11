# AI-Powered Product Matching and Search MVP

## 1. Project Overview

**Client:** Upwork — AI-Native MVP Builder
**Goal:** Internal tool for a team to search, match, and deduplicate 2,000+ messy product records from multiple suppliers.
**Screening Question:** How to approach the first working MVP for 2,000 messy products (inconsistent names, missing specs, duplicate SKUs, different image formats, no standard categories).

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         MVP Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│  [Import]  CSV/Excel upload → Python parser → Normalize fields  │
│                                                                  │
│  [Dedupe]  TF-IDF similarity → cluster products → flag dupes    │
│                                                                  │
│  [Match]   OpenAI embeddings → cosine similarity → match scores │
│                                                                  │
│  [Search]  Embedding vector search → ranked results             │
│                                                                  │
│  [UI]      Flask API + React dashboard                          │
│            • Product table with search bar                       │
│            • Duplicate cluster viewer                             │
│            • Match confidence scores                             │
│            • Manual override / confirm actions                   │
│                                                                  │
│  [Data]    PostgreSQL — products, clusters, match_edges tables  │
└─────────────────────────────────────────────────────────────────┘
```

## 3. Core Workstreams

**Workstream 1: Data Import & Normalization**
- CSV/Excel parser with field mapping (configurable column names)
- Normalize: strip whitespace, lowercase, remove special chars from product names
- Handle missing specs: flag as `[MISSING]` instead of silently dropping
- Dedupe detection via TF-IDF + string similarity (Levenshtein)

**Workstream 2: Product Matching Engine**
- Generate OpenAI embeddings for product name + description
- Store in PostgreSQL with `pgvector` extension for similarity search
- Match score = cosine similarity between embedding vectors
- Cluster products: group items with match score > 0.85 threshold
- "Likely duplicate" flag for scores 0.7–0.85 (human review queue)

**Workstream 3: Search Interface**
- Vector similarity search: "find products similar to X"
- Keyword search fallback using PostgreSQL full-text search
- Filter by: supplier, category, match confidence, missing fields
- Export deduplication results as CSV

**Workstream 4: Dashboard (React)**
- Product list with search bar
- Duplicate cluster view: side-by-side product comparison
- Match confidence badge (HIGH/MEDIUM/LOW/REVIEW)
- "Confirm match" / "Not a match" action buttons → updates DB

## 4. Data Model

**products**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| supplier_id | VARCHAR | Source supplier |
| original_name | TEXT | Raw name from CSV |
| normalized_name | TEXT | Cleaned lowercase name |
| description | TEXT | Specs/description |
| category | VARCHAR | Assigned category or NULL |
| embedding | VECTOR(1536) | OpenAI ada-002 embedding |
| metadata | JSONB | Raw row + any extra fields |
| created_at | TIMESTAMP | |

**clusters**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| canonical_product_id | UUID | FK → products.id (representative) |
| size | INT | Number of products in cluster |
| created_at | TIMESTAMP | |

**match_edges**
| Column | Type | Notes |
|--------|------|-------|
| id | UUID | PK |
| product_a_id | UUID | FK → products.id |
| product_b_id | UUID | FK → products.id |
| similarity_score | FLOAT | 0.0–1.0 |
| status | VARCHAR | pending/confirmed/rejected |

## 5. API Design

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/import | Upload CSV, returns import job ID |
| GET | /api/products | List products with pagination + search |
| GET | /api/products/{id} | Single product details |
| GET | /api/clusters | List duplicate clusters |
| GET | /api/clusters/{id} | Cluster detail with all members |
| POST | /api/match-edges | Confirm/reject a match |
| POST | /api/search | Vector search: `{query, limit}` → matched products |
| GET | /api/stats | Dashboard stats: total products, clusters, match rate |

## 6. Technical Decisions

1. **pgvector over Pinecone/Milvus** — MVP scope doesn't justify external vector DB; pgvector in existing PostgreSQL is sufficient for <10K products.
2. **TF-IDF for dedupe, embeddings for matching** — TF-IDF is fast and effective for string dedupe; embeddings capture semantic similarity for matching different products with same purpose.
3. **Flask over FastAPI** — Simpler for MVP, less boilerplate for a one-page internal tool.
4. **React without a framework** — Plain React (Vite) for the dashboard; no Next.js complexity needed for an internal tool.
5. **No authentication in V1** — Internal tool behind VPN/credentials; add auth in V2 if exposed externally.

## 7. Out of Scope

- Image processing / image format normalization
- Automated category assignment (AI or rule-based)
- Real-time sync with supplier APIs
- User authentication / multi-tenancy
- Mobile UI

## 8. Success Metrics

- Import 2,000 products from CSV in < 5 minutes
- Deduplication cluster recall > 90% (spot-checked manually)
- Search latency < 500ms for similarity queries
- "Confirm match" / "Reject match" actions persist correctly in DB
- CSV export of deduplication results works end-to-end