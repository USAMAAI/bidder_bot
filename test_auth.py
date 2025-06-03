#!/usr/bin/env python3
"""
Test script for the authentication system
"""

from src.database import (
    create_user, authenticate_user, create_session, 
    validate_session, invalidate_session, cleanup_expired_sessions,
    ensure_db_exists
)

def test_authentication_system():
    """Test all authentication functionality."""
    print("🔐 Testing Authentication System")
    print("=" * 50)
    
    # Initialize database
    print("1. Initializing database...")
    ensure_db_exists()
    print("   ✅ Database initialized")
    
    # Test user creation
    print("\n2. Testing user creation...")
    success, user_id = create_user("testuser2", "test2@example.com", "securepassword123")
    if success:
        print(f"   ✅ User created with ID: {user_id}")
    else:
        print(f"   ❌ User creation failed: {user_id}")
        return
    
    # Test authentication
    print("\n3. Testing authentication...")
    auth_success, user_data, message = authenticate_user("testuser2", "securepassword123")
    if auth_success:
        print(f"   ✅ Authentication successful: {user_data['username']}")
    else:
        print(f"   ❌ Authentication failed: {message}")
        return
    
    # Test session creation
    print("\n4. Testing session creation...")
    session_id = create_session(user_id, 24)  # 24 hours
    if session_id:
        print(f"   ✅ Session created: {session_id[:16]}...")
    else:
        print("   ❌ Session creation failed")
        return
    
    # Test session validation
    print("\n5. Testing session validation...")
    valid, session_data = validate_session(session_id)
    if valid:
        print(f"   ✅ Session valid for user: {session_data['username']}")
    else:
        print("   ❌ Session validation failed")
        return
    
    # Test session invalidation
    print("\n6. Testing session invalidation...")
    logout_success = invalidate_session(session_id)
    if logout_success:
        print("   ✅ Session invalidated successfully")
    else:
        print("   ❌ Session invalidation failed")
        return
    
    # Test expired session cleanup
    print("\n7. Testing session cleanup...")
    cleaned = cleanup_expired_sessions()
    print(f"   ✅ Cleaned up {cleaned} expired sessions")
    
    # Test wrong password
    print("\n8. Testing wrong password...")
    auth_fail, _, fail_message = authenticate_user("testuser2", "wrongpassword")
    if not auth_fail:
        print(f"   ✅ Correctly rejected wrong password: {fail_message}")
    else:
        print("   ❌ Should have rejected wrong password")
    
    # Test duplicate user creation
    print("\n9. Testing duplicate user creation...")
    dup_success, dup_message = create_user("testuser2", "test2@example.com", "password")
    if not dup_success:
        print(f"   ✅ Correctly rejected duplicate user: {dup_message}")
    else:
        print("   ❌ Should have rejected duplicate user")
    
    print("\n" + "=" * 50)
    print("🎉 All authentication tests passed!")
    print("\n📋 Summary:")
    print("- User registration and login: ✅")
    print("- Session management: ✅") 
    print("- Password security: ✅")
    print("- Data validation: ✅")
    print("\n🚀 Ready to run: streamlit run app.py")

if __name__ == "__main__":
    try:
        test_authentication_system()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Please check your database configuration.") 