import pytest
from main import app
from src.router.scan_request import ScanRequest
from fastapi.testclient import TestClient
from src.database.redis import Redis_Controller

client = TestClient(app)


def mock_scan_request_variable_domain(domain: str):
    mock = {
        "session_id": "0",
        "domain": domain
    }
    return mock


def mock_scan_request_variable_session_id(session_id: str):
    mock = {
        "session_id": session_id,
        "domain": "example.com"
    }
    return mock


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_endpoint(self):
        """/api/ endpoint returns API information"""
        response = client.get("/api/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "CSAF Provider Scan API"
        assert data["version"] == "1.0.0"


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
        assert "redis_available" in data
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
        Redis_Controller().block_session_id_for_domain("12", "example.com")
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id("12")
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_start_scan_unblocked_session(self):
        """Fails with unblocked session id"""
        Redis_Controller().block_session_id_for_domain("12", "example.com")
        Redis_Controller().unblock_session_id_for_domain("12", "example.com")
        response = client.post(
            "/api/scan/start",
            json=mock_scan_request_variable_session_id("12")
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "INITIALIZED"
        assert data["domain"] == "example.com"
        assert "results_checker" in data


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
        with pytest.raises(ValueError, match="Invalid domain format"):
            ScanRequest(domain="not a valid domain!")


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
