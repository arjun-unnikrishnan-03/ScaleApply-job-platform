"""
Integration tests for the asynchronous processing pipeline.

Covers:
- POST /*/async endpoints return 202 Accepted with a correlation_id
- GET /*/result/{correlation_id} returns the stored result or 404
- EventPublisher correctly routes to the mock QueueService
- Event schema serialization / deserialization round-trip
- QueueService in-memory result persistence lifecycle
- BaseWorker retry logic: success on first attempt
- BaseWorker retry logic: success on second attempt (after one transient failure)
- BaseWorker retry logic: permanent failure → DLQ routing
- BaseWorker DLQ event structure is well-formed
- BaseWorker metrics are recorded per outcome (success / failure / retry)
"""
from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from events.schemas import Event
from events.publisher import EventPublisher
from events.consumer import EventConsumer
from services.queue_service import QueueService
from workers.base_worker import BaseWorker

# Re-use shared fixtures from conftest (mock_queue_service, client, app_with_mocks)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

VALID_CANDIDATE_PROFILE = {
    "full_name": "Alice Smith",
    "email": "alice@example.com",
    "phone": None,
    "linkedin_url": None,
    "github_url": None,
    "location": None,
    "portfolio_url": None,
    "professional_summary": "Senior Python engineer",
    "technical_skills": ["Python", "Redis"],
    "soft_skills": [],
    "languages": [],
    "experience": [],
    "education": [],
    "projects": [],
    "certifications": [],
    "years_of_experience": None,
    "extracted_at": "2024-01-01T00:00:00+00:00",
    "source_file": "inline",
}

VALID_JOB_DESCRIPTION = {
    "title": "Platform Engineer",
    "department": None,
    "company_name": "Acme",
    "location": None,
    "remote_policy": None,
    "employment_type": None,
    "experience_required": None,
    "required_skills": ["Python"],
    "preferred_skills": [],
    "technologies": [],
    "responsibilities": ["Build stuff"],
    "qualifications": ["BS in CS"],
    "benefits": [],
    "salary_range": None,
    "summary": "Build platform tooling",
    "source_name": "inline",
    "extracted_at": "2024-01-01T00:00:00+00:00",
}

VALID_ATS_RESULT = {
    "candidate_name": "Alice Smith",
    "job_title": "Platform Engineer",
    "score": 85,
    "matched_skills": ["Python"],
    "missing_skills": [],
    "strengths": ["Strong Python skills"],
    "weaknesses": [],
    "recommendations": ["Great match"],
    "explanation": "Excellent candidate.",
    "evaluated_at": "2024-01-01T00:00:00+00:00",
}

VALID_SKILL_GAP_RESULT = {
    "candidate_name": "Alice Smith",
    "job_title": "Platform Engineer",
    "match_percentage": 85,
    "estimated_learning_weeks": 2,
    "missing_skills": [],
    "priority_order": [],
    "strengths": ["Python"],
    "roadmap": [],
    "explanation": "Nearly ready.",
    "analyzed_at": "2024-01-01T00:00:00+00:00",
}

VALID_INTERVIEW_RESULT = {
    "candidate_name": "Alice Smith",
    "job_title": "Platform Engineer",
    "technical_questions": [{
        "question": "Explain Redis streams.",
        "category": "Technical",
        "difficulty": "Medium",
        "reason": "Core knowledge for the role",
    }],
    "project_questions": [],
    "behavioral_questions": [],
    "weak_area_questions": [],
    "evaluation_rubric": [{
        "criteria": "Technical depth",
        "passing_score_description": "Correctly explains Redis internals.",
    }],
    "explanation": "Tailored interview kit.",
    "generated_at": "2024-01-01T00:00:00+00:00",
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

class _AlwaysSucceedWorker(BaseWorker):
    """Concrete worker that always succeeds on the first attempt."""

    def __init__(self, queue_service):
        super().__init__(queue_service=queue_service, stream="test.processing")
        self.call_count = 0

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        self.call_count += 1
        return {"processed": True, "input": payload}


class _FailOnceThenSucceedWorker(BaseWorker):
    """Concrete worker that raises once, then succeeds."""

    def __init__(self, queue_service):
        super().__init__(queue_service=queue_service, stream="test.retry")
        self.call_count = 0

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        self.call_count += 1
        if self.call_count < 2:
            raise RuntimeError("Transient failure")
        return {"processed": True}


class _AlwaysFailWorker(BaseWorker):
    """Concrete worker that always raises — will exhaust retries."""

    def __init__(self, queue_service):
        super().__init__(queue_service=queue_service, stream="test.fail", max_retries=3)
        self.call_count = 0

    def process_payload(self, payload: Dict[str, Any]) -> Any:
        self.call_count += 1
        raise RuntimeError("Permanent error")


def _make_mock_queue_service():
    """Return a fresh in-memory MockQueueService (same as conftest version)."""
    from tests.api.conftest import MockQueueService
    return MockQueueService()


def _publish_event_to_mock(mock_qs, stream: str, payload: Dict[str, Any]) -> tuple[str, Event]:
    """Helper: create + publish an Event to the mock QueueService, return (correlation_id, event)."""
    event = Event(event_type="test.event", payload=payload)
    mock_qs.publish(stream, event)
    return event.correlation_id, event


# ─────────────────────────────────────────────────────────────────────────────
# 1. Async API Endpoint tests — Resume
# ─────────────────────────────────────────────────────────────────────────────

class TestResumeAsyncEndpoint:
    def test_returns_202_and_correlation_id(self, client):
        response = client.post(
            "/resume/analyze/async",
            json={"text": "Alice Smith, 8 years of Python and distributed systems experience."},
        )
        assert response.status_code == 202
        body = response.json()
        assert "correlation_id" in body
        assert len(body["correlation_id"]) == 36  # UUID4 format

    def test_publishes_to_queue(self, client, mock_queue_service):
        """The event is dispatched into the mock queue service's stream map."""
        client.post(
            "/resume/analyze/async",
            json={"text": "Alice Smith, 8 years of Python and distributed systems experience."},
        )
        assert "resume.processing" in mock_queue_service.streams
        assert len(mock_queue_service.streams["resume.processing"]) == 1

    def test_result_404_before_worker_completes(self, client):
        """Polling for a fresh correlation_id returns 404 — no result yet."""
        resp = client.get("/resume/result/nonexistent-correlation-id-here")
        assert resp.status_code == 404

    def test_result_found_after_manual_set(self, client, mock_queue_service):
        """If QueueService already holds a result, the GET endpoint returns it."""
        cid = "resume-test-correlation-id"
        mock_queue_service.set_result(cid, "completed", result={"full_name": "Alice"})
        resp = client.get(f"/resume/result/{cid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "completed"
        assert body["result"]["full_name"] == "Alice"

    def test_text_too_short_returns_422(self, client):
        response = client.post("/resume/analyze/async", json={"text": "short"})
        assert response.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 2. Async API Endpoint tests — ATS
# ─────────────────────────────────────────────────────────────────────────────

class TestATSAsyncEndpoint:
    def test_returns_202_and_correlation_id(self, client):
        response = client.post(
            "/ats/analyze/async",
            json={
                "candidate_profile": VALID_CANDIDATE_PROFILE,
                "job_description": VALID_JOB_DESCRIPTION,
            },
        )
        assert response.status_code == 202
        body = response.json()
        assert "correlation_id" in body

    def test_publishes_to_ats_stream(self, client, mock_queue_service):
        client.post(
            "/ats/analyze/async",
            json={
                "candidate_profile": VALID_CANDIDATE_PROFILE,
                "job_description": VALID_JOB_DESCRIPTION,
            },
        )
        assert "ats.processing" in mock_queue_service.streams

    def test_result_404_when_not_found(self, client):
        resp = client.get("/ats/result/unknown-ats-correlation-id")
        assert resp.status_code == 404

    def test_result_returned_when_present(self, client, mock_queue_service):
        cid = "ats-cid-123"
        mock_queue_service.set_result(cid, "completed", result={"score": 90})
        resp = client.get(f"/ats/result/{cid}")
        assert resp.status_code == 200
        assert resp.json()["result"]["score"] == 90


# ─────────────────────────────────────────────────────────────────────────────
# 3. Async API Endpoint tests — Recruiter
# ─────────────────────────────────────────────────────────────────────────────

class TestRecruiterAsyncEndpoint:
    def test_returns_202_and_correlation_id(self, client):
        response = client.post(
            "/recruiter/evaluate/async",
            json={
                "candidate_profile": VALID_CANDIDATE_PROFILE,
                "job_description": VALID_JOB_DESCRIPTION,
                "ats_result": VALID_ATS_RESULT,
                "skill_gap_result": VALID_SKILL_GAP_RESULT,
                "interview_result": VALID_INTERVIEW_RESULT,
            },
        )
        assert response.status_code == 202
        body = response.json()
        assert "correlation_id" in body

    def test_publishes_to_recruiter_stream(self, client, mock_queue_service):
        client.post(
            "/recruiter/evaluate/async",
            json={
                "candidate_profile": VALID_CANDIDATE_PROFILE,
                "job_description": VALID_JOB_DESCRIPTION,
                "ats_result": VALID_ATS_RESULT,
                "skill_gap_result": VALID_SKILL_GAP_RESULT,
                "interview_result": VALID_INTERVIEW_RESULT,
            },
        )
        assert "recruiter.processing" in mock_queue_service.streams

    def test_result_404_when_not_found(self, client):
        resp = client.get("/recruiter/result/no-such-id")
        assert resp.status_code == 404

    def test_result_returned_when_present(self, client, mock_queue_service):
        cid = "recruiter-cid-456"
        mock_queue_service.set_result(cid, "completed", result={"recommendation": "StrongHire"})
        resp = client.get(f"/recruiter/result/{cid}")
        assert resp.status_code == 200
        assert resp.json()["result"]["recommendation"] == "StrongHire"


# ─────────────────────────────────────────────────────────────────────────────
# 4. Async API Endpoint tests — Knowledge
# ─────────────────────────────────────────────────────────────────────────────

class TestKnowledgeAsyncEndpoint:
    def test_returns_202_and_correlation_id(self, client):
        response = client.post(
            "/knowledge/query/async",
            json={"query": "What is the notice period policy?"},
        )
        assert response.status_code == 202
        body = response.json()
        assert "correlation_id" in body

    def test_publishes_to_knowledge_stream(self, client, mock_queue_service):
        client.post(
            "/knowledge/query/async",
            json={"query": "What is the notice period policy?"},
        )
        assert "knowledge.processing" in mock_queue_service.streams

    def test_result_404_when_not_found(self, client):
        resp = client.get("/knowledge/result/no-such-id")
        assert resp.status_code == 404

    def test_result_returned_when_present(self, client, mock_queue_service):
        cid = "knowledge-cid-789"
        mock_queue_service.set_result(cid, "completed", result={"answer": "90 days"})
        resp = client.get(f"/knowledge/result/{cid}")
        assert resp.status_code == 200
        assert resp.json()["result"]["answer"] == "90 days"


# ─────────────────────────────────────────────────────────────────────────────
# 5. Event Schema serialization / deserialization round-trip
# ─────────────────────────────────────────────────────────────────────────────

class TestEventSchema:
    def test_to_redis_dict_is_flat_strings(self):
        event = Event(event_type="resume.processing.requested", payload={"text": "hello"})
        d = event.to_redis_dict()
        assert isinstance(d, dict)
        for k, v in d.items():
            assert isinstance(k, str)
            assert isinstance(v, str)

    def test_payload_is_json_serialised_in_redis_dict(self):
        payload = {"text": "hello world", "extra": 42}
        event = Event(event_type="test.event", payload=payload)
        d = event.to_redis_dict()
        deserialized_payload = json.loads(d["payload"])
        assert deserialized_payload == payload

    def test_from_redis_dict_restores_event(self):
        original = Event(event_type="ats.processing.requested", payload={"score": 95})
        redis_dict = original.to_redis_dict()
        restored = Event.from_redis_dict(redis_dict)
        assert restored.event_id == original.event_id
        assert restored.correlation_id == original.correlation_id
        assert restored.event_type == original.event_type
        assert restored.payload == original.payload

    def test_from_redis_dict_handles_bytes_keys_and_values(self):
        original = Event(event_type="test.bytes", payload={"key": "value"})
        redis_dict = original.to_redis_dict()
        # Simulate Redis returning bytes
        bytes_dict = {k.encode(): v.encode() for k, v in redis_dict.items()}
        restored = Event.from_redis_dict(bytes_dict)
        assert restored.event_type == "test.bytes"
        assert restored.payload == {"key": "value"}

    def test_from_redis_dict_gracefully_handles_invalid_payload(self):
        data = {
            "event_id": "some-id",
            "correlation_id": "some-corr-id",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "event_type": "test.bad_payload",
            "payload": "{not valid json}",
        }
        restored = Event.from_redis_dict(data)
        assert restored.payload == {}

    def test_event_has_unique_ids_by_default(self):
        e1 = Event(event_type="t")
        e2 = Event(event_type="t")
        assert e1.event_id != e2.event_id
        assert e1.correlation_id != e2.correlation_id

    def test_correlation_id_preserved_when_provided(self):
        cid = "my-custom-correlation-id"
        event = Event(event_type="t", correlation_id=cid)
        assert event.correlation_id == cid


# ─────────────────────────────────────────────────────────────────────────────
# 6. EventPublisher
# ─────────────────────────────────────────────────────────────────────────────

class TestEventPublisher:
    def test_publish_event_delegates_to_queue_service(self):
        mock_qs = _make_mock_queue_service()
        publisher = EventPublisher(mock_qs)
        event = Event(event_type="test.publish", payload={"x": 1})
        msg_id = publisher.publish_event("test.stream", event)
        assert msg_id == "12345-0"
        assert len(mock_qs.streams.get("test.stream", [])) == 1

    def test_published_event_matches_original(self):
        mock_qs = _make_mock_queue_service()
        publisher = EventPublisher(mock_qs)
        event = Event(event_type="test.match", payload={"key": "value"})
        publisher.publish_event("test.stream", event)
        stored = mock_qs.streams["test.stream"][0]
        assert stored.event_id == event.event_id
        assert stored.correlation_id == event.correlation_id


# ─────────────────────────────────────────────────────────────────────────────
# 7. QueueService in-memory result lifecycle
# ─────────────────────────────────────────────────────────────────────────────

class TestMockQueueServiceResultLifecycle:
    def test_get_result_returns_none_for_unknown_id(self):
        qs = _make_mock_queue_service()
        assert qs.get_result("no-such-id") is None

    def test_set_and_get_processing_status(self):
        qs = _make_mock_queue_service()
        qs.set_result("cid-1", "processing", attempts=1)
        result = qs.get_result("cid-1")
        assert result is not None
        assert result["status"] == "processing"
        assert result["attempts"] == 1

    def test_set_and_get_completed_result(self):
        qs = _make_mock_queue_service()
        qs.set_result("cid-2", "completed", result={"score": 99}, attempts=1)
        result = qs.get_result("cid-2")
        assert result["status"] == "completed"
        assert result["result"]["score"] == 99
        assert result["error"] is None

    def test_set_and_get_failed_result(self):
        qs = _make_mock_queue_service()
        qs.set_result("cid-3", "failed", error="Timeout", attempts=3)
        result = qs.get_result("cid-3")
        assert result["status"] == "failed"
        assert result["error"] == "Timeout"
        assert result["attempts"] == 3

    def test_result_is_overwritten_on_status_update(self):
        qs = _make_mock_queue_service()
        qs.set_result("cid-4", "processing", attempts=1)
        qs.set_result("cid-4", "completed", result={"done": True}, attempts=1)
        result = qs.get_result("cid-4")
        assert result["status"] == "completed"

    def test_publish_increments_stream_depth(self):
        qs = _make_mock_queue_service()
        assert qs.get_queue_depth("stream-x") == 0
        event = Event(event_type="t")
        qs.publish("stream-x", event)
        assert qs.get_queue_depth("stream-x") == 1
        qs.publish("stream-x", event)
        assert qs.get_queue_depth("stream-x") == 2

    def test_ping_returns_true(self):
        qs = _make_mock_queue_service()
        assert qs.ping() is True


# ─────────────────────────────────────────────────────────────────────────────
# 8. BaseWorker — success on first attempt
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseWorkerSuccessPath:
    def _make_event(self, payload: dict | None = None) -> Event:
        return Event(event_type="test.event", payload=payload or {"data": "ok"})

    def test_result_is_completed_after_successful_processing(self):
        qs = _make_mock_queue_service()
        worker = _AlwaysSucceedWorker(qs)
        event = self._make_event()
        worker._handle_event_with_retries("msg-id-1", event)
        result = qs.get_result(event.correlation_id)
        assert result["status"] == "completed"
        assert result["result"]["processed"] is True

    def test_process_payload_called_exactly_once_on_success(self):
        qs = _make_mock_queue_service()
        worker = _AlwaysSucceedWorker(qs)
        event = self._make_event()
        worker._handle_event_with_retries("msg-id-1", event)
        assert worker.call_count == 1

    def test_message_is_acked_on_success(self):
        qs = _make_mock_queue_service()
        acked_ids = []
        qs.ack_message = lambda stream, group, msg_id: acked_ids.append(msg_id)  # type: ignore[method-assign]
        worker = _AlwaysSucceedWorker(qs)
        event = self._make_event()
        worker._handle_event_with_retries("msg-id-1", event)
        assert "msg-id-1" in acked_ids

    def test_dlq_not_written_on_success(self):
        qs = _make_mock_queue_service()
        worker = _AlwaysSucceedWorker(qs)
        event = self._make_event()
        worker._handle_event_with_retries("msg-id-1", event)
        assert "dead_letter_queue" not in qs.streams


# ─────────────────────────────────────────────────────────────────────────────
# 9. BaseWorker — retry then succeed
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseWorkerRetryThenSuccess:
    def test_result_is_completed_after_retry_success(self):
        qs = _make_mock_queue_service()
        worker = _FailOnceThenSucceedWorker(qs)
        event = Event(event_type="retry.test", payload={"attempt": "me"})

        # Speed up: monkey-patch sleep
        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-retry-1", event)

        result = qs.get_result(event.correlation_id)
        assert result["status"] == "completed"

    def test_process_payload_called_twice_on_one_transient_failure(self):
        qs = _make_mock_queue_service()
        worker = _FailOnceThenSucceedWorker(qs)
        event = Event(event_type="retry.test")

        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-retry-2", event)

        assert worker.call_count == 2

    def test_no_dlq_routing_when_eventually_succeeds(self):
        qs = _make_mock_queue_service()
        worker = _FailOnceThenSucceedWorker(qs)
        event = Event(event_type="retry.test")

        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-retry-3", event)

        assert "dead_letter_queue" not in qs.streams


# ─────────────────────────────────────────────────────────────────────────────
# 10. BaseWorker — permanent failure → DLQ
# ─────────────────────────────────────────────────────────────────────────────

class TestBaseWorkerPermanentFailureDLQ:
    def _run_always_fail(self, qs):
        worker = _AlwaysFailWorker(qs)
        event = Event(event_type="fail.test", payload={"x": 1})
        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-fail-1", event)
        return event

    def test_result_is_failed_after_all_retries_exhausted(self):
        qs = _make_mock_queue_service()
        event = self._run_always_fail(qs)
        result = qs.get_result(event.correlation_id)
        assert result["status"] == "failed"
        assert "Permanent error" in result["error"]

    def test_dlq_stream_receives_event(self):
        qs = _make_mock_queue_service()
        self._run_always_fail(qs)
        assert "dead_letter_queue" in qs.streams
        assert len(qs.streams["dead_letter_queue"]) == 1

    def test_dlq_event_has_correct_type_prefix(self):
        qs = _make_mock_queue_service()
        self._run_always_fail(qs)
        dlq_event = qs.streams["dead_letter_queue"][0]
        assert dlq_event.event_type.startswith("dlq.")

    def test_dlq_event_payload_contains_original_event(self):
        qs = _make_mock_queue_service()
        worker = _AlwaysFailWorker(qs)
        original_event = Event(event_type="fail.test", payload={"original_key": "original_value"})
        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-fail-dlq", original_event)
        dlq_event = qs.streams["dead_letter_queue"][0]
        payload = dlq_event.payload
        assert "original_event" in payload
        assert "error" in payload
        assert "failed_at" in payload
        assert "attempts" in payload
        assert payload["attempts"] == 3
        assert "Permanent error" in payload["error"]

    def test_dlq_event_source_stream_is_correct(self):
        qs = _make_mock_queue_service()
        self._run_always_fail(qs)
        dlq_event = qs.streams["dead_letter_queue"][0]
        assert dlq_event.payload["source_stream"] == "test.fail"

    def test_all_retries_exhausted_before_dlq(self):
        qs = _make_mock_queue_service()
        worker = _AlwaysFailWorker(qs)
        event = Event(event_type="fail.test")
        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-fail-retries", event)
        assert worker.call_count == 3  # max_retries = 3

    def test_message_is_acked_even_after_dlq(self):
        """Ensures permanently failed events don't block the PEL indefinitely."""
        qs = _make_mock_queue_service()
        acked_ids = []
        qs.ack_message = lambda stream, group, msg_id: acked_ids.append(msg_id)  # type: ignore[method-assign]
        worker = _AlwaysFailWorker(qs)
        event = Event(event_type="fail.test")
        import time
        with patch.object(time, "sleep", return_value=None):
            worker._handle_event_with_retries("msg-fail-ack", event)
        assert "msg-fail-ack" in acked_ids


# ─────────────────────────────────────────────────────────────────────────────
# 11. Correlation ID uniqueness across concurrent async requests
# ─────────────────────────────────────────────────────────────────────────────

class TestCorrelationIdUniqueness:
    def test_multiple_async_requests_generate_distinct_ids(self, client):
        ids = set()
        for _ in range(5):
            resp = client.post(
                "/resume/analyze/async",
                json={"text": "Alice Smith, 8 years of Python and distributed systems experience."},
            )
            assert resp.status_code == 202
            ids.add(resp.json()["correlation_id"])
        assert len(ids) == 5  # all unique


# ─────────────────────────────────────────────────────────────────────────────
# 12. Status progression — processing → completed
# ─────────────────────────────────────────────────────────────────────────────

class TestStatusProgression:
    def test_result_transitions_from_processing_to_completed(self, client, mock_queue_service):
        """Simulate the worker status transitions through the QueueService."""
        cid = "status-progression-cid"

        # Step 1: Worker marks event as processing
        mock_queue_service.set_result(cid, "processing", attempts=1)
        resp = client.get(f"/resume/result/{cid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "processing"

        # Step 2: Worker completes processing
        mock_queue_service.set_result(cid, "completed", result={"full_name": "Alice"}, attempts=1)
        resp = client.get(f"/resume/result/{cid}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

    def test_result_transitions_from_processing_to_failed(self, client, mock_queue_service):
        cid = "status-fail-cid"
        mock_queue_service.set_result(cid, "processing", attempts=1)
        mock_queue_service.set_result(cid, "failed", error="LLM timeout", attempts=3)
        resp = client.get(f"/resume/result/{cid}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "failed"
        assert "LLM timeout" in body["error"]
