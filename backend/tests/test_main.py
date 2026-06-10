# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

import pytest
import asyncio
from main import app
from src.router.scan_request import ScanRequest
from fastapi.testclient import TestClient
from src.database.valkey import Valkey_Controller
from src.slots.domain_task import Domain_Task

client = TestClient(app)


def mock_scan_request_variable_domain(domain: str):
    mock = {
        "session_id": "0",
        "domain": domain,
        "clear_any_running": True,
    }
    return mock


def mock_scan_request_variable_session_id(session_id: str):
    mock = {
        "session_id": session_id,
        "domain": "example.com",
        "clear_any_running": True,
    }
    return mock

def mock_scan_request_variable_shortening_options(start_at, max_lines: int, prioritize_newest_lines: bool):
    mock = {
        "session_id": "0",
        "domain": "example2.com",
        "clear_any_running": True,
        "start_at_line": start_at,
        "max_lines": max_lines,
        "prioritize_newest_lines": prioritize_newest_lines,
    }
    return mock

async def scan_example_domain():
    task = Domain_Task.create("example2.com", "0")
    task.get_data(True).enable_validator_cache = False

    await asyncio.create_task(task.run_checker())



class TestInformationEndpoint:
    """Tests for the information endpoint"""

    def test_information_endpoint(self):
        """/api/information endpoint returns API information"""
        response = client.get("/api/information")
        assert response.status_code == 200
        data = response.json()
        assert "csaf_checker_version" in data
        assert "csaf_validator_version" in data
        assert "csaf_provider_version" in data
        assert "docs" in data
        assert "openapi" in data


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check(self):
        """health endpoint returns expected fields"""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "free_slots" in data
        assert "total_slots" in data
        assert "csaf_checker_available" in data
        assert "valkey_available" in data
        assert "validator_available" in data
        assert data["status"] in ("healthy", "unhealthy")

    def test_health_check_without_binary(self):
        """health endpoint returns 503 when csaf_checker binary is unavailable"""
        from unittest.mock import patch, AsyncMock
        with patch("src.router.router.CSAF_BINARY_PATH", "/nonexistent/path"):
            response = client.get("/api/health")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["csaf_checker_available"] is False
            assert "csaf_checker binary is not available" in data["errors"]


class TestScanStartEndpointDomains:
    """Tests for the /scan/start endpoint"""

    def test_start_scan_success(self):
        """Just a valid domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("example.com")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "INITIALIZED"
        assert data["domain"] == "example.com"
        assert "results_checker" in data

    def test_start_scan_with_whitespace(self):
        """Whitespace is trimmed from domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("  example.com  ")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["domain"] == "example.com"

    def test_start_scan_empty_domain(self):
        """Fails with empty domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_whitespace_only_domain(self):
        """Fails with whitespace-only domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("    ")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_blocked_domain(self):
        """Fails with blocked domain"""
        Valkey_Controller().block_domain("example.com")
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("example.com")
        )
        Valkey_Controller().unblock_domain("example.com")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_invalid_domain_with_protocol(self):
        """Fails with protocol in domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("https://example.com")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_invalid_domain_with_path(self):
        """Fail with path in domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("example.com/path")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_invalid_domain_special_chars(self):
        """Fails with special characters"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("example$.com")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_invalid_domain_spaces(self):
        """Fails with spaces in domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain("example domain.com")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_missing_domain_field(self):
        """Fails without domain field"""
        response = client.post(
            "/api/scan/start",
            json={}
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_null_domain(self):
        """Fails with null domain"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_domain(None)
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_invalid_json(self):
        """Fails with invalid JSON"""
        response = client.post(
            "/api/scan/start",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

class TestScanStartEndpointSessionId:

    def test_start_scan_success(self):
        """Just a valid session id"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id("0")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "INITIALIZED"
        assert data["domain"] == "example.com"
        assert "results_checker" in data

    def test_start_scan_empty_session(self):
        """Fails with empty session id"""
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id(None)
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_blocked_session(self):
        """Fails with blocked session id"""
        Valkey_Controller().block_session_id_for_domain("12", "example.com")
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id("12")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_unblocked_session(self):
        """Fails with unblocked session id"""
        Valkey_Controller().block_session_id_for_domain("12", "example.com")
        Valkey_Controller().unblock_session_id_for_domain("12", "example.com")
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id("12")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "INITIALIZED"
        assert data["domain"] == "example.com"
        assert "results_checker" in data

class TestOutputOptions:
    """Tests different output shortening options"""

    @pytest.mark.asyncio
    async def test_start_at(self):
        await scan_example_domain()

        """Different start points should result in the same output that is offset"""
        normalResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 10, False)
        )
        normalResponseData = normalResponse.json()

        offsetResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(5, 10, False)
        )
        offsetResponseData = offsetResponse.json()

        assert normalResponse.status_code == 201
        assert offsetResponse.status_code == 201
        assert normalResponseData["runtime_output"][5] == offsetResponseData["runtime_output"][0]

    @pytest.mark.asyncio
    async def test_prioritize_latest(self):
        await scan_example_domain()

        """Testing priotization parameter"""
        fullResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 1000, True)
        )
        fullResponseData = fullResponse.json()

        prioritizeNewestResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 1, True)
        )
        prioritizeNewestResponseData = prioritizeNewestResponse.json()

        prioritizeOldestResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 1, False)
        )
        prioritizeOldestResponseData = prioritizeOldestResponse.json()

        assert fullResponse.status_code == 201
        assert prioritizeNewestResponse.status_code == 201
        assert prioritizeOldestResponse.status_code == 201
        assert len(fullResponseData["runtime_output"]) < 1000 ## If this fails, test another domain with shorter output
        assert len(fullResponseData["runtime_output"]) > 0 ## If this fails, test another domain with output
        assert fullResponseData["runtime_output"][0] == prioritizeOldestResponseData["runtime_output"][0]
        assert fullResponseData["runtime_output"][0] != prioritizeNewestResponseData["runtime_output"][0]
        assert prioritizeOldestResponseData["runtime_output"][0] != prioritizeNewestResponseData["runtime_output"][0]
        assert fullResponseData["runtime_output"][len(fullResponseData["runtime_output"]) - 1] == prioritizeNewestResponseData["runtime_output"][0]

    @pytest.mark.asyncio
    async def test_max_lines(self):
        await scan_example_domain()

        """Max lines determines amount of output lines"""
        shortResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 4, True)
        )
        shortResponseData = shortResponse.json()

        assert shortResponse.status_code == 201
        assert len(shortResponseData["runtime_output"]) == 4

    @pytest.mark.asyncio
    async def test_max_lines_maximum(self):
        await scan_example_domain()

        """Max lines set to -1 should output all lines. Tests whether -1 is functionally the same as using max possible lines"""
        minusOneResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, -1, True)
        )
        minusOneData = minusOneResponse.json()

        maxLinesResponse = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_shortening_options(0, 2147483647, True)
        )
        maxLinesData = maxLinesResponse.json()

        assert minusOneResponse.status_code == 201
        assert maxLinesResponse.status_code == 201
        assert len(maxLinesData["runtime_output"]) == len(minusOneData["runtime_output"])


class TestDomainValidation:
    """Tests for domain validation logic"""

    def test_validate_simple_domain(self):
        """validation of simple domain"""
        request = ScanRequest(session_id="0", domain="example.com")
        assert request.domain == "example.com"

    def test_validate_domain_with_subdomain(self):
        """validation of domain with subdomain"""
        request = ScanRequest(session_id="0", domain="www.example.com")
        assert request.domain == "www.example.com"

    def test_validate_domain_strips_whitespace(self):
        """validation strips whitespace"""
        request = ScanRequest(session_id="0", domain="  example.com  ")
        assert request.domain == "example.com"

    def test_validate_domain_rejects_empty(self):
        """validation rejects empty domain"""
        with pytest.raises(ValueError, match="Domain cannot be empty"):
            ScanRequest(domain="")

    def test_validate_domain_rejects_invalid_format(self):
        """validation rejects invalid domain format"""
        with pytest.raises(ValueError, match="Invalid domain/PMD format. Please enter a valid Domain or PMD URL. Domains require a non-zero length extension. PMDs must start with 'https://' and end with '/provider-metadata.json'"):
            ScanRequest(domain="not a valid domain")

    def test_validate_pmd_url_normalizes_hostname_only(self):
        """validation lowercases PMD hostname but preserves path case"""
        request = ScanRequest(session_id="0", domain="HTTPS://Example.COM/CSAF/provider-metadata.json")
        assert request.domain == "https://example.com/CSAF/provider-metadata.json"

    def test_validate_pmd_url_normalizes_idn_hostname(self):
        """validation converts IDN hostname in PMD to Punycode"""
        request = ScanRequest(session_id="0", domain="https://püñi.example/strange/path/provider-metadata.json")
        assert request.domain == "https://xn--pi-zja7b.example/strange/path/provider-metadata.json"


class TestOpenAPIDocumentation:
    """Tests for OpenAPI/Swagger documentation"""

    def test_openapi_json_endpoint(self):
        """OpenAPI JSON schema is accessible"""
        response = client.get("/api/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "CSAF Provider Scan API"

    def test_swagger_ui_endpoint(self):
        """Swagger UI is accessible"""
        response = client.get("/api/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_redoc_endpoint(self):
        """ReDoc documentation is accessible"""
        response = client.get("/api/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_openapi_has_scan_endpoint(self):
        """OpenAPI schema includes scan endpoint"""
        response = client.get("/api/openapi.json")
        data = response.json()
        assert "/api/scan/start" in data["paths"]
        assert "post" in data["paths"]["/api/scan/start"]

    def test_scan_endpoint_has_proper_metadata(self):
        """scan endpoint has proper OpenAPI metadata"""
        response = client.get("/api/openapi.json")
        data = response.json()
        scan_endpoint = data["paths"]["/api/scan/start"]["post"]
        assert "summary" in scan_endpoint
        assert "description" in scan_endpoint
        assert "tags" in scan_endpoint
        assert "scan" in scan_endpoint["tags"]
