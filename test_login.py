#!/usr/bin/env python3
"""
Test script to verify login and redirect functionality
"""

from app import create_app
from app.models import User
from app.extensions import db

app = create_app()

with app.app_context():
    # Test 1: Check if user exists
    print("=" * 50)
    print("TEST 1: Checking if test user exists")
    print("=" * 50)
    
    test_email = "rahul@example.com"
    user = User.query.filter_by(email=test_email).first()
    
    if user:
        print(f"✅ User found: {user.username} ({user.email})")
        print(f"   Role: {user.role}")
        print(f"   Active: {user.is_active}")
        print(f"   Verified: {user.is_verified}")
        
        # Test 2: Check password
        print("\n" + "=" * 50)
        print("TEST 2: Testing password verification")
        print("=" * 50)
        
        test_password = "password123"
        if user.check_password(test_password):
            print(f"✅ Password verification successful")
        else:
            print(f"❌ Password verification failed")
            
        # Test 3: Check student profile
        print("\n" + "=" * 50)
        print("TEST 3: Checking student profile")
        print("=" * 50)
        
        from app.models import Student
        student = Student.query.filter_by(user_id=user.id).first()
        
        if student:
            print(f"✅ Student profile found: {student.full_name}")
            print(f"   Phone: {student.phone}")
            print(f"   Status: {student.enrollment_status}")
        else:
            print(f"❌ No student profile found")
    else:
        print(f"❌ User not found with email: {test_email}")
        
    # Test 4: Check routes
    print("\n" + "=" * 50)
    print("TEST 4: Checking registered routes")
    print("=" * 50)
    
    user_routes = [rule for rule in app.url_map.iter_rules() if 'user' in rule.endpoint]
    print(f"Found {len(user_routes)} user routes:")
    for route in user_routes:
        print(f"  {route.endpoint}: {route.rule}")
        
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("If all tests passed, login should work correctly.")
    print("Try logging in at: http://127.0.0.1:5001/login")
    print(f"Email: {test_email}")
    print("Password: password123")
