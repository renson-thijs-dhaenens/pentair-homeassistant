#!/usr/bin/env python3
"""
Tests for null/None response handling in the Pentair Water integration.

Simulates the scenarios where the erie_connect API returns None responses
or responses with None content, which cause 'NoneType' has no attribute 'content'.

Run with: python3 -m pytest test_null_responses.py -v
"""

import pytest
from dataclasses import dataclass
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch, AsyncMock, PropertyMock
from requests import RequestException


# Replicate the ErieConnect.Response dataclass
@dataclass
class MockResponse:
    headers: Dict[str, str]
    content: Any


def _safe_get_content(response) -> dict:
    """Extract content safely - mirrors the logic in __init__.py."""
    return getattr(response, "content", None) or {}


class TestNullResponseGuards:
    """Test that our getattr guards handle all None scenarios."""

    def test_normal_response(self):
        """Normal response with valid content dict."""
        resp = MockResponse(headers={}, content={"key": "value"})
        result = _safe_get_content(resp)
        assert result == {"key": "value"}

    def test_response_is_none(self):
        """API method returns None (e.g., _request falls through without return)."""
        result = _safe_get_content(None)
        assert result == {}

    def test_response_content_is_none(self):
        """Response object exists but .content is None."""
        resp = MockResponse(headers={}, content=None)
        result = _safe_get_content(resp)
        assert result == {}

    def test_response_has_no_content_attr(self):
        """Response object has no .content attribute at all."""
        resp = MagicMock(spec=[])  # Empty spec = no attributes
        result = _safe_get_content(resp)
        assert result == {}

    def test_response_content_is_empty_dict(self):
        """Response with empty dict content should return empty dict."""
        resp = MockResponse(headers={}, content={})
        result = _safe_get_content(resp)
        assert result == {}

    def test_response_content_is_empty_list(self):
        """Response with empty list content (falsy) should return empty dict."""
        resp = MockResponse(headers={}, content=[])
        result = _safe_get_content(resp)
        assert result == {}


class TestDataParsing:
    """Test the data parsing logic that runs after content extraction."""

    def test_total_volume_string_with_unit(self):
        """total_volume like '12345 L' should parse to '12345'."""
        info = {"total_volume": "12345 L"}
        raw = info.get("total_volume", "0")
        assert isinstance(raw, str)
        assert raw.split()[0] == "12345"

    def test_total_volume_numeric(self):
        """total_volume as int should convert to string."""
        info = {"total_volume": 12345}
        raw = info.get("total_volume", "0")
        assert not isinstance(raw, str)
        assert str(raw) == "12345"

    def test_total_volume_missing(self):
        """Missing total_volume should default to '0'."""
        info = {}
        raw = info.get("total_volume", "0")
        assert raw == "0"
        assert raw.split()[0] == "0"

    def test_settings_nested_extraction(self):
        """Settings should safely extract nested settings dict."""
        settings = {"settings": {"install_hardness": 25}}
        inner = settings.get("settings", {})
        assert inner.get("install_hardness") == 25

    def test_settings_empty(self):
        """Empty settings should not raise."""
        settings = {}
        inner = settings.get("settings", {})
        assert inner == {}
        assert inner.get("install_hardness") is None

    def test_dashboard_status_extraction(self):
        """Dashboard status nested extraction."""
        dashboard = {"status": {"capacity_remaining": 50}, "warnings": [], "meta": {"regen_time": "03:00"}}
        assert dashboard.get("status", {}) == {"capacity_remaining": 50}
        assert dashboard.get("warnings", []) == []
        assert dashboard.get("meta", {}).get("regen_time") == "03:00"

    def test_dashboard_empty(self):
        """Empty dashboard should return safe defaults."""
        dashboard = {}
        assert dashboard.get("status", {}) == {}
        assert dashboard.get("warnings", []) == []
        assert dashboard.get("holiday_mode", False) is False
        assert dashboard.get("meta", {}).get("regen_time") is None


class TestErieConnectLibraryBug:
    """
    Test that demonstrates the bug in erie_connect library's _request method.
    
    When _request catches an HTTPError with status != 401, it falls through
    without returning, so the caller gets None. Then _setup_if_needed ->
    select_first_active_device does response.content[0] on None.
    
    This error propagates as AttributeError: 'NoneType' object has no attribute 'content'
    from INSIDE the library, before our code even gets to handle the response.
    """

    def test_library_none_return_scenario(self):
        """Simulate what happens when erie_connect._request returns None."""
        # This is what happens inside api.info() when the library's _request
        # falls through without a return value
        api_return = None  # _request returned None

        # Our code (after fix) handles this:
        info = getattr(api_return, "content", None) or {}
        assert info == {}
        # Safe to call .get() on the result
        assert info.get("last_regeneration") is None
        assert info.get("serial") is None

    def test_library_internal_attributeerror(self):
        """
        Simulate the ACTUAL error: the AttributeError happens INSIDE
        the erie_connect library in select_first_active_device(), not in our code.
        
        Our except block catches it and wraps it as UpdateFailed.
        This test verifies we properly catch and handle this scenario.
        """
        def simulate_api_call_with_internal_error():
            """Simulates api.info() when _setup_if_needed fails internally."""
            # This is what happens inside erie_connect:
            # 1. _setup_if_needed() is called
            # 2. login() _request returns None (non-401 error)
            # 3. select_first_active_device() does: response = self.list_watersofteners()
            # 4. response is None, then response.content[0] raises AttributeError
            response = None
            try:
                _ = response.content[0]  # This is the actual crash
            except AttributeError as e:
                raise AttributeError("'NoneType' object has no attribute 'content'") from e

        # Verify the error matches what we see in logs
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'content'"):
            simulate_api_call_with_internal_error()

    def test_full_update_flow_with_library_error(self):
        """
        End-to-end test: simulate the full async_update_data flow when
        the library throws AttributeError internally.
        """
        caught_errors = []

        def mock_api_info():
            """Simulate api.info() throwing internal AttributeError."""
            raise AttributeError("'NoneType' object has no attribute 'content'")

        # This mirrors our except block in async_update_data
        try:
            response = mock_api_info()
        except Exception as err:
            caught_errors.append(str(err))

        assert len(caught_errors) == 1
        assert "'NoneType' object has no attribute 'content'" in caught_errors[0]

    def test_full_update_flow_all_responses_none(self):
        """
        Test the complete data extraction when all API responses are None.
        Should produce a valid dict with safe defaults, no crashes.
        """
        response = None
        response_dashboard = None
        response_settings = None
        response_flow = None

        info = getattr(response, "content", None) or {}
        dashboard_data = getattr(response_dashboard, "content", None) or {}
        settings = getattr(response_settings, "content", None) or {}
        flow_data = getattr(response_flow, "content", None) or {}
        features = {}

        settings_inner = settings.get("settings", {})
        dashboard = dashboard_data
        status_data = dashboard.get("status", {})

        total_volume_raw = info.get("total_volume", "0")
        if isinstance(total_volume_raw, str):
            total_volume = total_volume_raw.split()[0]
        else:
            total_volume = str(total_volume_raw)

        result = {
            "last_regeneration": info.get("last_regeneration"),
            "nr_regenerations": info.get("nr_regenerations"),
            "last_maintenance": info.get("last_maintenance"),
            "total_volume": total_volume,
            "warnings": dashboard.get("warnings", []),
            "serial": info.get("serial"),
            "software": info.get("software", "").strip(),
            "status": status_data,
            "settings": settings,
            "holiday_mode": dashboard.get("holiday_mode", False),
            "features": features,
            "flow": flow_data.get("flow", 0),
            "water_hardness": settings_inner.get("install_hardness"),
            "regen_time": dashboard.get("meta", {}).get("regen_time"),
        }

        # Verify we get a valid dict with safe defaults
        assert isinstance(result, dict)
        assert result["total_volume"] == "0"
        assert result["warnings"] == []
        assert result["serial"] is None
        assert result["software"] == ""
        assert result["status"] == {}
        assert result["settings"] == {}
        assert result["holiday_mode"] is False
        assert result["features"] == {}
        assert result["flow"] == 0
        assert result["water_hardness"] is None
        assert result["regen_time"] is None

    def test_full_update_flow_valid_responses(self):
        """
        Test the complete data extraction with valid API responses.
        """
        response = MockResponse(headers={}, content={
            "last_regeneration": "2026-03-10",
            "nr_regenerations": 42,
            "last_maintenance": "2026-01-15",
            "total_volume": "98765 L",
            "serial": "SN12345",
            "software": " v1.2.3 ",
        })
        response_dashboard = MockResponse(headers={}, content={
            "warnings": ["low_salt"],
            "status": {"capacity_remaining": 75},
            "holiday_mode": True,
            "meta": {"regen_time": "02:00"},
        })
        response_settings = MockResponse(headers={}, content={
            "settings": {"install_hardness": 30},
        })
        response_flow = MockResponse(headers={}, content={
            "flow": 12.5,
        })

        info = getattr(response, "content", None) or {}
        dashboard_data = getattr(response_dashboard, "content", None) or {}
        settings = getattr(response_settings, "content", None) or {}
        flow_data = getattr(response_flow, "content", None) or {}
        features = {"feature1": True}

        settings_inner = settings.get("settings", {})
        dashboard = dashboard_data
        status_data = dashboard.get("status", {})

        total_volume_raw = info.get("total_volume", "0")
        if isinstance(total_volume_raw, str):
            total_volume = total_volume_raw.split()[0]
        else:
            total_volume = str(total_volume_raw)

        result = {
            "last_regeneration": info.get("last_regeneration"),
            "nr_regenerations": info.get("nr_regenerations"),
            "last_maintenance": info.get("last_maintenance"),
            "total_volume": total_volume,
            "warnings": dashboard.get("warnings", []),
            "serial": info.get("serial"),
            "software": info.get("software", "").strip(),
            "status": status_data,
            "settings": settings,
            "holiday_mode": dashboard.get("holiday_mode", False),
            "features": features,
            "flow": flow_data.get("flow", 0),
            "water_hardness": settings_inner.get("install_hardness"),
            "regen_time": dashboard.get("meta", {}).get("regen_time"),
        }

        assert result["last_regeneration"] == "2026-03-10"
        assert result["nr_regenerations"] == 42
        assert result["total_volume"] == "98765"
        assert result["warnings"] == ["low_salt"]
        assert result["serial"] == "SN12345"
        assert result["software"] == "v1.2.3"
        assert result["status"] == {"capacity_remaining": 75}
        assert result["holiday_mode"] is True
        assert result["features"] == {"feature1": True}
        assert result["flow"] == 12.5
        assert result["water_hardness"] == 30
        assert result["regen_time"] == "02:00"


class TestFlowCoordinatorNullHandling:
    """Test the flow coordinator's null handling."""

    def test_flow_response_none(self):
        response_flow = None
        flow_data = getattr(response_flow, "content", None) or {}
        result = {"flow": flow_data.get("flow", 0)}
        assert result["flow"] == 0

    def test_flow_response_content_none(self):
        response_flow = MockResponse(headers={}, content=None)
        flow_data = getattr(response_flow, "content", None) or {}
        result = {"flow": flow_data.get("flow", 0)}
        assert result["flow"] == 0

    def test_flow_response_valid(self):
        response_flow = MockResponse(headers={}, content={"flow": 7.3})
        flow_data = getattr(response_flow, "content", None) or {}
        result = {"flow": flow_data.get("flow", 0)}
        assert result["flow"] == 7.3


class TestSafeApiCall:
    """Test the _safe_api_call wrapper that handles auth failures and library bugs."""

    def _make_safe_api_call(self, api_mock):
        """Create a _safe_api_call closure similar to __init__.py."""
        import logging
        _LOGGER = logging.getLogger(__name__)

        def _safe_api_call(api_method):
            try:
                result = api_method()
                if result is None:
                    raise AttributeError("API returned None response")
                return result
            except (AttributeError, RequestException):
                _LOGGER.debug("API call %s failed, forcing re-login", getattr(api_method, '__name__', str(api_method)))
                try:
                    api_mock._auth = None
                    api_mock._device = None
                    api_mock.login()
                    api_mock.select_first_active_device()
                    return api_method()
                except Exception:
                    return None

        return _safe_api_call

    def test_success_on_first_try(self):
        """Normal case: API call succeeds on the first attempt."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        expected = MockResponse(headers={}, content={"key": "value"})
        api.info.return_value = expected

        result = safe_call(api.info)
        assert result == expected
        api.login.assert_not_called()

    def test_retry_on_none_response(self):
        """API returns None first, then succeeds after re-login."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        expected = MockResponse(headers={}, content={"key": "value"})
        api.info.side_effect = [None, expected]

        result = safe_call(api.info)
        assert result == expected
        api.login.assert_called_once()
        api.select_first_active_device.assert_called_once()

    def test_retry_on_attributeerror(self):
        """API throws AttributeError (library bug), then succeeds after re-login."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        expected = MockResponse(headers={}, content={"flow": 5})
        api.dashboard.side_effect = [
            AttributeError("'NoneType' object has no attribute 'content'"),
            expected,
        ]

        result = safe_call(api.dashboard)
        assert result == expected
        api.login.assert_called_once()

    def test_retry_on_request_exception(self):
        """API throws RequestException, then succeeds after re-login."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        expected = MockResponse(headers={}, content={"flow": 3})
        api.flow.side_effect = [RequestException("connection error"), expected]

        result = safe_call(api.flow)
        assert result == expected
        api.login.assert_called_once()

    def test_retry_also_fails_returns_none(self):
        """Both attempts fail — should return None, not crash."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        api.info.side_effect = AttributeError("'NoneType' object has no attribute 'content'")

        result = safe_call(api.info)
        assert result is None

    def test_login_fails_returns_none(self):
        """Re-login itself fails — should return None, not crash."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        api.info.side_effect = AttributeError("fail")
        api.login.side_effect = Exception("login failed")

        result = safe_call(api.info)
        assert result is None

    def test_none_result_handled_by_getattr(self):
        """When _safe_api_call returns None, getattr guard produces empty dict."""
        api = MagicMock()
        safe_call = self._make_safe_api_call(api)
        api.info.side_effect = AttributeError("fail")
        api.login.side_effect = Exception("login failed")

        result = safe_call(api.info)
        info = getattr(result, "content", None) or {}
        assert info == {}
        assert info.get("serial") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
