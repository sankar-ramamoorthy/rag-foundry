# OCR Architecture & Design Decisions

## Context

As part of **IS4 – Image Ingestion**, the ingestion service must support
extracting text from images and feeding that text into the ingestion pipeline:

```

image → OCR → text → chunking → embedding → vector store

```

Multiple OCR engines are available (e.g., Tesseract, PaddleOCR, cloud OCRs),
each with different tradeoffs in accuracy, performance, and operational
complexity.

This document records the **design options considered**, the **decision taken**, and
the **rationale** behind that decision.

---

## Goals

The OCR design must:

- Keep the ingestion service **simple and stable**
- Avoid coupling OCR choices to API contracts
- Allow **future OCR engines** without refactoring the pipeline
- Avoid operational complexity during early development
- Remain compatible with Docker-based integration testing

Non-goals:

- GPU optimization
- Layout-aware OCR (bounding boxes, coordinates)
- Confidence scoring
- OCR microservices

---

## Design Options Considered

### Option 1: One Docker Container per OCR Engine

**Description**

Each OCR engine runs in its own Docker container with a dedicated API.
The ingestion service calls the appropriate OCR service based on configuration.

**Pros**
- Strong isolation between OCR engines
- GPU-specific containers possible
- Independent scaling

**Cons**
- High operational complexity
- Multiple services to deploy and test
- Increased CI and Docker orchestration cost
- Overkill for early-stage ingestion

**Decision**
❌ Rejected

---

### Option 2: OCR as an External Third-Party Service Only

**Description**

All OCR is delegated to external APIs (cloud OCR providers).

**Pros**
- Minimal local dependencies
- No OCR runtime management

**Cons**
- External dependency for core ingestion
- Cost and rate limits
- Harder to test deterministically
- Reduced offline / local dev capability

**Decision**
❌ Rejected

---

### Option 3: Pluggable OCR Engines Inside the Ingestion Service (Chosen)

**Description**

OCR engines are implemented as **pluggable internal adapters** inside the
`ingestion_service`, selected via configuration and hidden behind a stable
interface.

```

OCRExtractor (interface)
├─ TesseractOCR
├─ PaddleOCR (future)
└─ RemoteOCRClient (future)

````

Only **text output** is exposed to the rest of the system.

**Pros**
- Simple operational model (single service)
- Matches existing embedder / chunker patterns
- Easy to test locally and in Docker
- OCR engines are replaceable without API changes
- Future-ready for GPU or remote OCR

**Cons**
- OCR libraries share the same container
- Heavy dependencies may increase image size (manageable)

**Decision**
✅ Accepted

---

## Final Design Decision

### Core Principle

> **OCR is a pluggable leaf dependency behind a stable text-only interface.**

The ingestion pipeline never depends on:

- OCR engine internals
- Image formats
- OCR confidence scores
- Layout metadata

It only consumes extracted text.

---

## OCR Interface Contract

All OCR engines must implement the same internal interface:

```python
class OCRExtractor:
    name: str

    def extract_text(self, image_bytes: bytes) -> str:
        """Return extracted text, or an empty string."""
````

### Guarantees

* Always returns a string
* Empty or unreadable images return `""`
* OCR-specific failures are handled internally
* The pipeline never crashes due to OCR

---

## OCR Selection

OCR engines are selected by **name**, via configuration or request override.

Example:

```env
OCR_PROVIDER=tesseract
```

Optional API override (future-safe):

```json
{
  "ocr_provider": "tesseract"
}
```

If an OCR provider is requested but unavailable:

* The request fails fast with a clear error
* No partial ingestion occurs

---

## Docker Strategy

### Current State

* Single Docker container: `ingestion_service`
* OCR engines installed as libraries
* CPU-only execution
* Tesseract implemented first

### Future State

If GPU-based OCR is required:

* OCR may run in a separate container or node pool
* Ingestion service uses a `RemoteOCRClient`
* **OCR interface remains unchanged**

---

## Production Upgrade & Change Management

### Adding a New OCR Engine

* Implement new adapter
* Register in OCR factory
* Build and deploy new image
* No API or pipeline changes required

### Switching Default OCR

* Update configuration
* Redeploy ingestion service
* Existing data remains valid

### Rollback

* Revert configuration
* Redeploy
* No data corruption or reprocessing required

---

## Failure Semantics

| Scenario                  | Behavior                         |
| ------------------------- | -------------------------------- |
| Text detected             | Normal ingestion                 |
| Blank / low-quality image | Empty text → no chunks           |
| OCR error                 | Controlled failure or empty text |
| OCR unavailable           | Clear configuration error        |

In all cases:

* Ingestion lifecycle remains consistent
* Status tracking remains correct

---

## Summary

This design:

* Keeps OCR **replaceable**
* Keeps ingestion **stable**
* Avoids premature microservices
* Aligns with existing embedder abstractions
* Allows gradual evolution toward GPU or cloud OCR

The system remains **simple now**, while staying **flexible later**.
