"""
Unit tests for AlertService business logic.

These tests cover:
  - severity_from_score thresholds
  - Alert lifecycle state-machine (assign → acknowledge → resolve → reopen)
  - Role-based action authorisation

Database calls are mocked — no real PostgreSQL connection required.

Run with:
    pytest backend/tests/test_alert_service.py -v
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from tests.import_isolation import activate_service

# Allow imports from the alertes service package
activate_service("alertes")

# Patch database before importing service
import shared.database
with patch("shared.database.get_db_connection"):
    with patch("redis.from_url"):
        from services.alert_service import AlertService
        from services.exceptions import (
            AlertNotFoundException,
            InvalidStatusTransitionException,
            TechnicianNotEligibleException,
            UnauthorizedActionException,
        )
        from models.models import Alert, Technician


# ── Helpers ─────────────────────────────────────────────────────────────────

def make_service():
    with patch("redis.from_url"):
        svc = AlertService.__new__(AlertService)
        svc.redis_client = MagicMock()
        return svc


def make_alert(**kwargs):
    defaults = dict(
        id=1, plant_id=1, machine="moteur", defect="degradation_roulement",
        anomaly_score=0.75, confidence=0.9, severity="Majeure",
        status="open", assigned_to=None, assigned_by=None,
        acknowledged=False, created_at=None, resolved_at=None,
    )
    defaults.update(kwargs)
    alert = Alert.__new__(Alert)
    for k, v in defaults.items():
        setattr(alert, k, v)
    return alert


def make_technician(user_id=10, machines=None, plant_id=1):
    tech = Technician.__new__(Technician)
    tech.id       = user_id
    tech.role     = "technicien"
    tech.machines = machines or ["moteur"]
    tech.plant_id = plant_id
    return tech


def make_user(role="admin", sub=5, plant_id=1):
    return {"role": role, "sub": str(sub), "plant_id": plant_id}


# ── severity_from_score ─────────────────────────────────────────────────────

class TestSeverityFromScore:
    svc = make_service()

    @pytest.mark.parametrize("score,expected", [
        (0.0,  None),
        (0.39, None),
        (0.40, "Mineure"),
        (0.64, "Mineure"),
        (0.65, "Majeure"),
        (0.84, "Majeure"),
        (0.85, "Critique"),
        (1.0,  "Critique"),
    ])
    def test_thresholds(self, score, expected):
        assert self.svc.severity_from_score(score) == expected


# ── assign_alert ────────────────────────────────────────────────────────────

class TestAssignAlert:
    def _svc_with_mocks(self, alert, technician=None):
        svc = make_service()
        svc._get_alert_for_update = MagicMock(return_value=alert)
        svc._validate_technician_for_alert = MagicMock()
        svc._apply_alert_update = MagicMock(return_value=alert)
        svc._upsert_intervention = MagicMock()
        svc.get_technician = MagicMock(return_value=technician or make_technician())
        return svc

    def test_superviseur_can_assign(self):
        alert = make_alert()
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="superviseur", sub=5)

        with patch("shared.database.get_db_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_ctx.cursor.return_value.__enter__.return_value = MagicMock()
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)

            # Should not raise
            svc.assign_alert(1, {"assigned_to": 10}, user)

    def test_technicien_cannot_assign(self):
        alert = make_alert()
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="technicien", sub=10)

        with pytest.raises(UnauthorizedActionException):
            svc.assign_alert(1, {"assigned_to": 10}, user)

    def test_missing_assigned_to_raises(self):
        alert = make_alert()
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with pytest.raises(InvalidStatusTransitionException):
            svc.assign_alert(1, {}, user)


# ── acknowledge_alert ───────────────────────────────────────────────────────

class TestAcknowledgeAlert:
    def _svc_with_mocks(self, alert):
        svc = make_service()
        svc._get_alert_for_update = MagicMock(return_value=alert)
        svc._apply_alert_update   = MagicMock(return_value=alert)
        return svc

    def test_assigned_technician_can_acknowledge(self):
        alert = make_alert(status="assigned", assigned_to=10)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="technicien", sub=10)

        with patch("shared.database.get_db_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_ctx.cursor.return_value.__enter__.return_value = MagicMock()
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            svc.acknowledge_alert(1, {"acknowledged": True}, user)

    def test_different_technician_cannot_acknowledge(self):
        alert = make_alert(status="assigned", assigned_to=10)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="technicien", sub=99)

        with pytest.raises(UnauthorizedActionException):
            svc.acknowledge_alert(1, {"acknowledged": True}, user)

    def test_admin_cannot_acknowledge(self):
        alert = make_alert(status="assigned", assigned_to=10)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with pytest.raises(UnauthorizedActionException):
            svc.acknowledge_alert(1, {"acknowledged": True}, user)


# ── resolve_alert ───────────────────────────────────────────────────────────

class TestResolveAlert:
    def _svc_with_mocks(self, alert):
        svc = make_service()
        svc._get_alert_for_update = MagicMock(return_value=alert)
        svc._apply_alert_update   = MagicMock(return_value=alert)
        return svc

    def test_admin_can_resolve_acknowledged(self):
        alert = make_alert(status="acknowledged", acknowledged=True)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with patch("shared.database.get_db_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_ctx.cursor.return_value.__enter__.return_value = MagicMock()
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            svc.resolve_alert(1, {}, user)

    def test_cannot_resolve_unacknowledged(self):
        alert = make_alert(status="assigned", acknowledged=False)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with pytest.raises(InvalidStatusTransitionException):
            svc.resolve_alert(1, {}, user)

    def test_technicien_cannot_resolve(self):
        alert = make_alert(status="acknowledged", acknowledged=True)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="technicien", sub=10)

        with pytest.raises(UnauthorizedActionException):
            svc.resolve_alert(1, {}, user)


# ── reopen_alert ─────────────────────────────────────────────────────────────

class TestReopenAlert:
    def _svc_with_mocks(self, alert):
        svc = make_service()
        svc._get_alert_for_update = MagicMock(return_value=alert)
        svc._apply_alert_update   = MagicMock(return_value=alert)
        return svc

    def test_admin_can_reopen_resolved(self):
        alert = make_alert(status="resolved", acknowledged=True)
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with patch("shared.database.get_db_connection") as mock_conn:
            mock_conn.return_value.__enter__ = MagicMock(return_value=MagicMock())
            mock_conn.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx = MagicMock()
            mock_conn.return_value.__enter__.return_value = mock_ctx
            mock_ctx.cursor.return_value.__enter__.return_value = MagicMock()
            mock_ctx.cursor.return_value.__exit__ = MagicMock(return_value=False)
            svc.reopen_alert(1, {}, user)

    def test_cannot_reopen_non_resolved(self):
        alert = make_alert(status="open")
        svc   = self._svc_with_mocks(alert)
        user  = make_user(role="admin", sub=5)

        with pytest.raises(InvalidStatusTransitionException):
            svc.reopen_alert(1, {}, user)
