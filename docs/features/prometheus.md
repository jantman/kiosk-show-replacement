# Prometheus Endpoint

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to add a Prometheus metrics endpoint to this Flask application. The metrics that we want to provide are as follows, all of which should use the display name as a tag/label as well as the display ID.

* display_info - metric using tag to provide the currently assigned slideshow (just an info metric that always returns an integer value)
* display_online - 1 or 0 metric for whether the display is online (1 is online)
* display width and height (resolution) metrics
* display rotation
* display last seen timestamp
* display heartbeat interval
* missed heartbeat count

And any other metrics that you think would be helpful for monitoring the health of the system, and we can collect without much additional effort.

---

## Implementation Plan

### Current State Analysis

The codebase already has a `/metrics` endpoint in `kiosk_show_replacement/metrics.py` that exposes:
- `http_requests_total` (counter) - by method, endpoint, status
- `http_request_duration_seconds` (histogram) - by endpoint
- `active_sse_connections` (gauge)
- `database_errors_total` (counter)
- `storage_errors_total` (counter)
- `display_heartbeat_age_seconds` (gauge) - per display

The existing infrastructure uses manual Prometheus text format generation (not the `prometheus_client` library). The metrics endpoint is registered as a Flask blueprint and is already functional.

### Proposed Metrics

All display metrics will include labels: `display_id`, `display_name`

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `display_info` | Gauge | display_id, display_name, slideshow_id, slideshow_name | Info metric (always 1) with slideshow assignment in labels |
| `display_online` | Gauge | display_id, display_name | 1 if online, 0 if offline |
| `display_resolution_width_pixels` | Gauge | display_id, display_name | Display width in pixels |
| `display_resolution_height_pixels` | Gauge | display_id, display_name | Display height in pixels |
| `display_rotation_degrees` | Gauge | display_id, display_name | Display rotation (0, 90, 180, 270) |
| `display_last_seen_timestamp_seconds` | Gauge | display_id, display_name | Unix timestamp of last heartbeat |
| `display_heartbeat_interval_seconds` | Gauge | display_id, display_name | Configured heartbeat interval |
| `display_missed_heartbeats` | Gauge | display_id, display_name | Number of missed heartbeats |

**Additional metrics for system health:**

| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `display_sse_connected` | Gauge | display_id, display_name | 1 if SSE connected, 0 if not |
| `display_is_active` | Gauge | display_id, display_name | 1 if active, 0 if inactive |
| `displays_total` | Gauge | - | Total number of displays |
| `displays_online_total` | Gauge | - | Number of online displays |
| `slideshows_total` | Gauge | - | Total number of slideshows |

### Milestones

#### Milestone 1 (PROM-M1): Add Display Metrics Function

**Prefix:** `PROM-M1`

**Tasks:**
1. Create `get_display_metrics()` function in `metrics.py` that queries all displays and generates Prometheus text format for all display-related metrics
2. Integrate the new function into the `/metrics` endpoint
3. Add unit tests for the new function

**Acceptance Criteria:**
- All display metrics are exposed at `/metrics` endpoint
- Metrics follow Prometheus naming conventions
- Labels are properly escaped for special characters
- Unit tests cover normal operation and edge cases (no displays, displays with null values)

#### Milestone 2 (PROM-M2): Add Summary Metrics

**Prefix:** `PROM-M2`

**Tasks:**
1. Create `get_summary_metrics()` function for aggregate counts
2. Add total display counts (all, online, active)
3. Add total slideshow count
4. Integrate into `/metrics` endpoint
5. Add unit tests

**Acceptance Criteria:**
- Summary metrics are exposed at `/metrics`
- Unit tests verify correct counts

#### Milestone 3 (PROM-M3): Acceptance Criteria

**Prefix:** `PROM-M3`

**Tasks:**
1. Update documentation (`docs/prometheus.rst` or similar) describing available metrics
2. Ensure all nox sessions pass
3. Move feature document to `docs/features/completed/`

**Acceptance Criteria:**
- Documentation is complete and accurate
- All tests pass
- Feature document moved to completed directory

---

## Progress

- [ ] Milestone 1: Add Display Metrics Function
- [ ] Milestone 2: Add Summary Metrics
- [ ] Milestone 3: Acceptance Criteria
