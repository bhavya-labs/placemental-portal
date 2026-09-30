import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.config import settings
from backend.app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from backend.app.routers.auth import login_rate_limiter
from backend.app.main import app

def test_security_hardening():
    print("=== Testing Phase 1 Security Hardening ===")
    
    # 1. Test .env and settings
    print(f"[1/5] Settings loaded: PROJECT_NAME = '{settings.PROJECT_NAME}'")
    print(f"      DATABASE_URL = '{settings.DATABASE_URL}'")
    print(f"      FRONTEND_ORIGIN = '{settings.FRONTEND_ORIGIN}'")
    print(f"      LOGIN_MAX_FAILED_ATTEMPTS = {settings.LOGIN_MAX_FAILED_ATTEMPTS}")
    assert settings.SECRET_KEY is not None and len(settings.SECRET_KEY) > 10, "SECRET_KEY invalid"
    assert "http://localhost:5173" in settings.FRONTEND_ORIGIN, "FRONTEND_ORIGIN missing dev origin"

    # 2. Test dynamic random salt password hashing
    print("[2/5] Testing password hashing with random salt...")
    p1 = get_password_hash("test_password_123")
    p2 = get_password_hash("test_password_123")
    assert p1 != p2, "Hashes must have different salts!"
    assert verify_password("test_password_123", p1), "Password 1 verification failed"
    assert verify_password("test_password_123", p2), "Password 2 verification failed"
    assert not verify_password("wrong_password", p1), "Invalid password verified as true!"
    # Verify legacy seed salt format compatibility
    legacy_hash = "f8a569cb23dbbc8d4809$e7f805a8d4a9cf41d9e7da1dfd2243d6c827ea3bcf773f32420f1883be12674c"
    # Even if password doesn't match legacy, function shouldn't crash
    assert verify_password("admin123", legacy_hash) in [True, False]
    print("      Random salt hashing verified!")

    # 3. Test Login Rate Limiter
    print("[3/5] Testing LoginRateLimiter sliding-window protection...")
    test_email = "test_lockout@college.edu"
    test_ip = "192.168.1.100"
    
    # Reset any existing test state
    login_rate_limiter.record_success(test_email, test_ip)
    
    # Record 4 failures (limit is 5)
    for i in range(settings.LOGIN_MAX_FAILED_ATTEMPTS - 1):
        remaining = login_rate_limiter.record_failure(test_email, test_ip)
        assert remaining == (settings.LOGIN_MAX_FAILED_ATTEMPTS - 1 - i)
    print(f"      4 failures recorded, {remaining} remaining.")
    
    # 5th failure should trigger lockout
    try:
        login_rate_limiter.record_failure(test_email, test_ip)
        assert False, "Should have raised 429 Too Many Requests!"
    except Exception as exc:
        assert hasattr(exc, "status_code") and exc.status_code == 429, f"Expected 429, got {exc}"
        print(f"      Lockout triggered as expected: {exc.detail}")

    # Subsequent check should still be locked out
    try:
        login_rate_limiter.check_rate_limit(test_email, test_ip)
        assert False, "Should have remained locked out!"
    except Exception as exc:
        assert hasattr(exc, "status_code") and exc.status_code == 429
        print(f"      Rate limit check confirms lockout active!")

    # Reset
    login_rate_limiter.record_success(test_email, test_ip)
    # Check rate limit should pass after success
    login_rate_limiter.check_rate_limit(test_email, test_ip)
    print("      Rate limiter cleared successfully on success reset!")

    # 4. Test CORS Middleware
    print("[4/5] Testing CORS middleware configuration...")
    cors_mw = None
    for mw in app.user_middleware:
        if "CORSMiddleware" in str(mw.cls):
            cors_mw = mw
            break
    assert cors_mw is not None, "CORSMiddleware not found in app.user_middleware"
    print(f"      CORS Middleware configured with allow_origins: {cors_mw.kwargs.get('allow_origins')}")

    # 5. Test Router Endpoints
    print("[5/5] Testing FastAPI routes count...")
    openapi_schema = app.openapi()
    paths = list(openapi_schema["paths"].keys())
    assert "/api/auth/login" in paths, "Missing /api/auth/login route"
    assert "/api/auth/token" in paths, "Missing /api/auth/token route"
    assert "/api/companies" in paths, "Missing /api/companies route"
    assert "/api/drives" in paths, "Missing /api/drives route"
    print(f"      Total registered API paths: {len(paths)}")

    print("\n>>> ALL PHASE 1 SECURITY AUDITS & TESTS PASSED! <<<\n")

if __name__ == "__main__":
    test_security_hardening()
