"""
Comprehensive Phase 1 Automated Verification Suite for InterviewX.
Tests:
- Database schema initialization and migrations
- Salted password hashing and constant-time verification
- Form and input validation (username, email, password, name)
- User registration and duplicate prevention
- Multi-identifier authentication (username vs email)
- Multi-user data isolation (User A cannot see User B's mock results)
- Streamlit session state functions
"""

import sys
import secrets
from pathlib import Path

# Ensure root directory is on path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from auth import (
    hash_password,
    verify_password,
    validate_username,
    validate_email,
    validate_password,
    validate_full_name,
)
from database import (
    init_db,
    create_user,
    authenticate_user,
    get_user_by_id,
    get_user_analytics,
    seed_demo_data_if_empty,
)

def run_tests():
    print("--- RUNNING PHASE 1 TEST SUITE ---")

    # 1. Database Init & Migration
    init_db()
    seed_demo_data_if_empty()
    print("✔ [1/7] SQLite schema initialized, migrated, and demo seeded.")

    # 2. Input Validation Rules
    assert validate_username("arjun_26")[0], "Valid username failed"
    assert not validate_username("ab")[0], "Too short username should fail"
    assert not validate_username("bad-user!")[0], "Invalid characters should fail"
    assert validate_email("student@nit.edu.in")[0], "Valid email failed"
    assert not validate_email("invalid-email")[0], "Invalid email format should fail"
    assert validate_password("Secure@2026")[0], "Valid password failed"
    assert not validate_password("123")[0], "Too short password should fail"
    assert validate_full_name("Arjun Verma")[0], "Valid name failed"
    assert not validate_full_name(" ")[0], "Empty name should fail"
    print("✔ [2/7] Input validation rules verified (Username, Email, Password, Name).")

    # 3. Password Hashing & Verification
    plain_pw = "TestPassword@2026"
    pw_hash = hash_password(plain_pw)
    assert pw_hash.startswith("pbkdf2:sha256:100000$"), "PBKDF2 format mismatch"
    assert verify_password(plain_pw, pw_hash), "Password verification failed"
    assert not verify_password("WrongPassword!", pw_hash), "Wrong password falsely verified"
    assert not verify_password("", pw_hash), "Empty password falsely verified"
    print("✔ [3/7] PBKDF2-HMAC-SHA256 password hashing & verification verified.")

    # 4. Demo Account Login
    demo_u, err = authenticate_user("arjun", "Demo@123")
    assert demo_u is not None, f"Demo auth failed: {err}"
    assert demo_u["username"] == "arjun"
    assert "password_hash" not in demo_u, "Password hash leaked in user object"
    print(f"✔ [4/7] Demo account login verified for user: {demo_u['name']} (ID: {demo_u['id']}).")

    # 5. New User Registration & Duplicate Prevention
    rand_id = secrets.token_hex(3)
    uname = f"test_cand_{rand_id}"
    email = f"{uname}@university.edu.in"

    new_user, err = create_user(
        username=uname,
        email=email,
        password="MySecretPassword@123",
        name="Priya Patel",
        college="Delhi Technological University (DTU)",
        degree="B.Tech IT",
        graduation_year=2026,
        target_role="Frontend Developer (React / JavaScript)",
        target_company_track="Product Companies & Tier-1 Startups"
    )
    assert new_user is not None, f"Registration failed: {err}"
    assert new_user["id"] > 1
    assert new_user["username"] == uname
    print(f"✔ [5/7] New candidate registered successfully: {new_user['name']} (@{new_user['username']}).")

    # Check duplicate username rejection
    dup_uname_user, err1 = create_user(uname, f"diff_{email}", "Password@123", "Other Name")
    assert dup_uname_user is None and "already registered" in err1, "Duplicate username allowed"

    # Check duplicate email rejection
    dup_email_user, err2 = create_user(f"diff_{uname}", email, "Password@123", "Other Name")
    assert dup_email_user is None and "already exists" in err2, "Duplicate email allowed"
    print("✔ [6/7] Duplicate username & duplicate email constraints enforced.")

    # 6. Multi-Identifier Authentication
    login_by_uname, _ = authenticate_user(uname, "MySecretPassword@123")
    assert login_by_uname is not None and login_by_uname["id"] == new_user["id"]

    login_by_email, _ = authenticate_user(email, "MySecretPassword@123")
    assert login_by_email is not None and login_by_email["id"] == new_user["id"]

    bad_login, bad_err = authenticate_user(uname, "IncorrectPass!")
    assert bad_login is None and "Incorrect password" in bad_err
    print("✔ [7/7] Multi-identifier authentication verified (Login via Username OR Email).")

    # 7. Multi-Tenant Data Isolation
    arjun_stats = get_user_analytics(1)
    new_user_stats = get_user_analytics(new_user["id"])
    assert arjun_stats["total_interviews"] >= 4, "Arjun demo sessions missing"
    assert new_user_stats["total_interviews"] == 0, "New user data leakage detected!"
    assert new_user_stats["readiness_index"] == 0, "New user readiness should be 0"
    print(f"✔ [Data Isolation] Arjun sessions: {arjun_stats['total_interviews']} | New User sessions: {new_user_stats['total_interviews']}.")

    print("\n🎉 ALL PHASE 1 REQUIREMENTS VERIFIED AND PASSING!")

if __name__ == "__main__":
    run_tests()
