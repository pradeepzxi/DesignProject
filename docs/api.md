# API Documentation: Link Integrity Management Framework

Base URL: `http://localhost:8000/api`

Interactive OpenAPI Documentation: `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc).

---

## 1. System Health

### `GET /health`
Returns system health, environment status, and database connectivity.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "environment": "development",
  "database": "sqlite_connected"
}
```

---

## 2. Document Management

### `POST /api/documents/upload`
Uploads a document (`.pdf` or `.docx`), persists the original file safely in `/data/documents/`, extracts embedded hyperlinks with structural context, and generates audit logs.

- **Content-Type**: `multipart/form-data`
- **Request Body**:
  - `file`: Binary file payload (max 50 MB, `.pdf` or `.docx`)

**Response `201 Created`**:
```json
{
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "filename": "HR_Leave_Policy_2024.pdf",
  "file_type": "pdf",
  "file_size": 204850,
  "upload_timestamp": "2026-09-24T16:15:30Z",
  "version": 1,
  "processing_status": "PARSED",
  "document_title": "Enterprise Employee Leave and Absence Policy 2024",
  "storage_path": "./data/documents/20260924_161530_HR_Leave_Policy_2024.pdf",
  "links_count": 11,
  "valid_links_count": 0,
  "broken_links_count": 0,
  "last_scanned_at": null
}
```

---

### `GET /api/documents`
Lists all uploaded documents with summary statistics.

- **Query Parameters**:
  - `skip` (int, default: 0)
  - `limit` (int, default: 100)

**Response `200 OK`**:
```json
[
  {
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "filename": "HR_Leave_Policy_2024.pdf",
    "file_type": "pdf",
    "file_size": 204850,
    "upload_timestamp": "2026-09-24T16:15:30Z",
    "version": 1,
    "processing_status": "COMPLETED",
    "document_title": "Enterprise Employee Leave and Absence Policy 2024",
    "storage_path": "./data/documents/20260924_161530_HR_Leave_Policy_2024.pdf",
    "links_count": 11,
    "valid_links_count": 4,
    "broken_links_count": 5,
    "last_scanned_at": "2026-09-24T16:20:10Z"
  }
]
```

---

### `GET /api/documents/{id}`
Retrieves detailed information for a specific document, including all associated links and the latest scan run.

**Response `200 OK`**:
```json
{
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "filename": "HR_Leave_Policy_2024.pdf",
  "file_type": "pdf",
  "file_size": 204850,
  "document_title": "Enterprise Employee Leave and Absence Policy 2024",
  "processing_status": "COMPLETED",
  "links_count": 11,
  "valid_links_count": 4,
  "broken_links_count": 5,
  "links": [
    {
      "link_id": "e4d7a12b-89bc-4e12-a10f-219cb84f8841",
      "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
      "original_url": "https://httpbin.org/status/404",
      "normalized_url": "https://httpbin.org/status/404",
      "status": "BROKEN_404",
      "status_code": 404,
      "final_url": "https://httpbin.org/status/404",
      "response_time_ms": 112.4,
      "content_type": null,
      "last_checked": "2026-09-24T16:20:15Z",
      "error_message": "HTTP 404: Not Found on remote server",
      "page_number": 1,
      "location_description": "Page 1, Section '1.0 Annual and Sick Leave Entitlements'"
    }
  ],
  "latest_scan": {
    "scan_id": "f882190c-3331-4191-88aa-21049281aef1",
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "started_at": "2026-09-24T16:20:00Z",
    "completed_at": "2026-09-24T16:20:18Z",
    "total_links": 11,
    "valid_links": 4,
    "broken_links": 5,
    "redirected_links": 2,
    "failed_links": 0,
    "scan_status": "COMPLETED"
  }
}
```

---

### `POST /api/documents/{id}/scan`
Initiates an asynchronous validation scan for all hyperlinks embedded in the target document.

**Response `200 OK`**:
```json
{
  "scan_id": "f882190c-3331-4191-88aa-21049281aef1",
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "started_at": "2026-09-24T16:20:00Z",
  "completed_at": "2026-09-24T16:20:18Z",
  "total_links": 11,
  "valid_links": 4,
  "broken_links": 5,
  "redirected_links": 2,
  "failed_links": 0,
  "scan_status": "COMPLETED"
}
```

---

### `DELETE /api/documents/{id}`
Deletes the document, cascading deletion across links and contexts.

**Response `204 No Content`**

---

## 3. Hyperlinks & Context

### `GET /api/links`
Retrieves hyperlinks across the repository with flexible filtering.

- **Query Parameters**:
  - `document_id` (string, optional)
  - `status` (string, optional): e.g. `VALID`, `BROKEN_404`, `REDIRECT`, `TIMEOUT`
  - `broken_only` (bool, default: false)
  - `search` (string, optional)
  - `skip` (int, default: 0)
  - `limit` (int, default: 100)

**Response `200 OK`**:
```json
[
  {
    "link_id": "e4d7a12b-89bc-4e12-a10f-219cb84f8841",
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "original_url": "https://httpbin.org/status/404",
    "normalized_url": "https://httpbin.org/status/404",
    "status": "BROKEN_404",
    "status_code": 404,
    "final_url": "https://httpbin.org/status/404",
    "response_time_ms": 112.4,
    "content_type": null,
    "last_checked": "2026-09-24T16:20:15Z",
    "error_message": "HTTP 404: Not Found on remote server",
    "page_number": 1,
    "location_description": "Page 1, Section '1.0 Annual and Sick Leave Entitlements'",
    "document_title": "Enterprise Employee Leave and Absence Policy 2024",
    "document_filename": "HR_Leave_Policy_2024.pdf"
  }
]
```

---

### `GET /api/links/{id}`
Retrieves a single link with its complete linguistic, positional, and syntactic context.

**Response `200 OK`**:
```json
{
  "link_id": "e4d7a12b-89bc-4e12-a10f-219cb84f8841",
  "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "original_url": "https://httpbin.org/status/404",
  "normalized_url": "https://httpbin.org/status/404",
  "status": "BROKEN_404",
  "status_code": 404,
  "final_url": "https://httpbin.org/status/404",
  "response_time_ms": 112.4,
  "content_type": null,
  "last_checked": "2026-09-24T16:20:15Z",
  "error_message": "HTTP 404: Not Found on remote server",
  "page_number": 1,
  "location_description": "Page 1, Section '1.0 Annual and Sick Leave Entitlements'",
  "document_title": "Enterprise Employee Leave and Absence Policy 2024",
  "document_filename": "HR_Leave_Policy_2024.pdf",
  "context": {
    "context_id": "c19028fa-4182-4144-88aa-91928014aef1",
    "link_id": "e4d7a12b-89bc-4e12-a10f-219cb84f8841",
    "anchor_text": "statutory sick leave schedule",
    "surrounding_text": "For statutory sick leave guidelines, review the standard statutory sick leave schedule.",
    "paragraph_text": "Employees are granted 25 days of paid annual leave. For statutory sick leave guidelines, review the standard statutory sick leave schedule. Inquiries regarding family leave must be submitted through the personnel portal.",
    "section_heading": "1.0 Annual and Sick Leave Entitlements",
    "document_title": "Enterprise Employee Leave and Absence Policy 2024",
    "url_tokens": {
      "domain": "httpbin.org",
      "path": "/status/404",
      "filename": "404",
      "path_segments": ["status", "404"],
      "query_keys": [],
      "terms": ["httpbin", "status"]
    },
    "keywords": ["leave", "sick", "statutory", "schedule", "entitlements", "annual"]
  }
}
```

---

### `POST /api/links/{id}/validate`
Forces immediate real-time re-validation of a single hyperlink, bypassing the cache.

**Response `200 OK`**: LinkDetailResponse (same as `GET /api/links/{id}`)

---

## 4. Telemetry & Analytics

### `GET /api/stats/overview`
Aggregated repository telemetry and distributions for the research dashboard.

**Response `200 OK`**:
```json
{
  "total_documents": 10,
  "scanned_documents": 10,
  "total_links": 110,
  "valid_links": 48,
  "broken_links": 45,
  "redirected_links": 17,
  "failed_links": 12,
  "pending_links": 0,
  "status_distribution": [
    { "name": "Valid", "value": 48, "percentage": 43.6, "color": "#10B981" },
    { "name": "Broken 404", "value": 25, "percentage": 22.7, "color": "#EF4444" },
    { "name": "Redirect", "value": 17, "percentage": 15.5, "color": "#3B82F6" }
  ],
  "failure_distribution": [
    { "name": "Broken 404", "value": 25, "percentage": 55.6, "color": "#EF4444" },
    { "name": "Server Error 5Xx", "value": 8, "percentage": 17.8, "color": "#DC2626" },
    { "name": "Timeout", "value": 4, "percentage": 8.9, "color": "#F59E0B" }
  ],
  "recent_activity": [
    {
      "id": "78b19...",
      "timestamp": "2026-09-24T16:20:18Z",
      "action_type": "SCAN_COMPLETED",
      "document_id": "9b1deb4d...",
      "status": "COMPLETED",
      "reason": "Scan finished: 4 valid, 5 broken, 2 redirected",
      "actor": "SYSTEM"
    }
  ]
}
```

---

## 5. Audit Trail

### `GET /api/audit-logs`
Lists immutable audit events chronologically for experimental verification.

- **Query Parameters**:
  - `document_id` (string, optional)
  - `limit` (int, default: 50)

**Response `200 OK`**:
```json
[
  {
    "audit_id": "11928014-aef1-4191-88aa-f882190c3331",
    "timestamp": "2026-09-24T16:20:18Z",
    "document_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "link_id": null,
    "action_type": "SCAN_COMPLETED",
    "old_url": null,
    "new_url": null,
    "status": "COMPLETED",
    "reason": "Scan finished: 4 valid, 5 broken, 2 redirected",
    "confidence_score": null,
    "actor": "SYSTEM"
  }
]
```
