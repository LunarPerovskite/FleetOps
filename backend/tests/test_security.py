"""Test suite for security features

CSRF, XSS, rate limiting, security headers
"""

import pytest
import hashlib
import secrets

class TestSecurityHeaders:
    """Test security headers"""
    
    def test_csp_header(self, client):
        """Test Content-Security-Policy header"""
        response = client.get("/")
        
        assert "Content-Security-Policy" in response.headers
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp
    
    def test_xss_protection(self, client):
        """Test XSS protection headers"""
        response = client.get("/")
        
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "1; mode=block" in response.headers["X-XSS-Protection"]
    
    def test_hsts_header(self, client):
        """Test HSTS header"""
        response = client.get("/")
        
        assert "Strict-Transport-Security" in response.headers
        hsts = response.headers["Strict-Transport-Security"]
        assert "max-age=31536000" in hsts
    
    def test_referrer_policy(self, client):
        """Test Referrer-Policy header"""
        response = client.get("/")
        
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    
    def test_server_header_removed(self, client):
        """Test that Server header is removed"""
        response = client.get("/")
        
        assert "Server" not in response.headers

class TestCSRFProtection:
    """Test CSRF protection"""
    
    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        from app.core.security import generate_csrf_token
        
        token, hashed = generate_csrf_token()
        
        assert len(token) > 0
        assert len(hashed) > 0
        assert hashed == hashlib.sha256(token.encode()).hexdigest()
    
    def test_csrf_required_for_post(self, client):
        """Test CSRF required for POST requests"""
        response = client.post("/tasks", json={"title": "Test"})
        
        # Should fail without CSRF token
        assert response.status_code in [403, 401]

class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_blocks_excessive_requests(self, client):
        """Test rate limiting blocks excessive requests"""
        responses = []
        
        # Make 110 requests (over the 100/min limit)
        for _ in range(110):
            response = client.get("/dashboard/stats")
            responses.append(response.status_code)
        
        # At least some should be rate limited
        assert 429 in responses
    
    def test_rate_limit_allows_normal_requests(self, client):
        """Test rate limiting allows normal requests"""
        responses = []
        
        # Make 10 requests (under the limit)
        for _ in range(10):
            response = client.get("/dashboard/stats")
            responses.append(response.status_code)
        
        # All should succeed
        assert all(r == 200 or r == 401 for r in responses)

class TestPasswordHashing:
    """Test password hashing"""
    
    def test_password_hashing(self):
        """Test password hashing and verification"""
        from app.core.security import hash_password, verify_password
        
        password = "test_password_123"
        hashed = hash_password(password)
        
        # Verify correct password
        assert verify_password(password, hashed) == True
        
        # Verify wrong password fails
        assert verify_password("wrong_password", hashed) == False
    
    def test_password_hash_contains_salt(self):
        """Test password hash contains salt"""
        from app.core.security import hash_password
        
        hashed = hash_password("test")
        
        # Should contain salt separator
        assert "$" in hashed
        
        # Should have salt (32 hex chars) + hash
        parts = hashed.split("$")
        assert len(parts) == 2
        assert len(parts[0]) == 32  # Salt length

class TestInputSanitization:
    """Test input sanitization"""
    
    def test_xss_sanitization(self):
        """Test XSS input sanitization"""
        from app.core.security import sanitize_input
        
        malicious_input = '<script>alert("xss")</script>'
        sanitized = sanitize_input(malicious_input)
        
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
        assert "&lt;script&gt;" in sanitized or "&lt;" in sanitized
    
    def test_html_entities_escaped(self):
        """Test HTML entities are escaped"""
        from app.core.security import sanitize_input
        
        input_text = '<div>Hello &amp; World</div>'
        sanitized = sanitize_input(input_text)
        
        assert "<" not in sanitized or "&lt;" in sanitized
        assert ">" not in sanitized or "&gt;" in sanitized
    
    def test_whitespace_stripped(self):
        """Test whitespace is stripped"""
        from app.core.security import sanitize_input
        
        input_text = "  hello world  "
        sanitized = sanitize_input(input_text)
        
        assert sanitized == "hello world"

class TestCORSSecurity:
    """Test CORS configuration"""
    
    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.get(
            "/",
            headers={"Origin": "http://localhost:3000"}
        )
        
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_preflight_request(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/tasks",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
        )
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Methods" in response.headers
