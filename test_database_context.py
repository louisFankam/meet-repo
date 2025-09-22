#!/usr/bin/env python3
"""
Test script to verify database session context is working properly
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.services import UserService
from model.database import db
from model.models import User
from flask import Flask

def test_database_access():
    """Test database access without Flask app context"""
    print("Testing database access without Flask app context...")
    
    try:
        user = UserService.get_user_by_email('Dominiquelouis15+1@gmail.com')
        print(f"User found without app context: {user}")
        return user is not None
    except Exception as e:
        print(f"Error accessing database without app context: {e}")
        return False

def test_database_access_with_context():
    """Test database access with Flask app context"""
    print("Testing database access with Flask app context...")
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/meet_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            user = UserService.get_user_by_email('Dominiquelouis15+1@gmail.com')
            print(f"User found with app context: {user}")
            if user:
                print(f"User details: ID={user.id}, Email={user.email}, Name={user.first_name} {user.last_name}")
            return user is not None
        except Exception as e:
            print(f"Error accessing database with app context: {e}")
            return False

def test_direct_query():
    """Test direct database query"""
    print("Testing direct database query...")
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/meet_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        try:
            user = User.query.filter_by(email='test@example.com').first()
            print(f"Direct query result: {user}")
            if user:
                print(f"User details: ID={user.id}, Email={user.email}, Name={user.first_name} {user.last_name}")
            return user is not None
        except Exception as e:
            print(f"Error with direct query: {e}")
            return False

if __name__ == '__main__':
    print("=" * 60)
    print("DATABASE SESSION CONTEXT TEST")
    print("=" * 60)
    
    # Test 1: Without app context (should fail gracefully)
    print("\n1. Testing without Flask app context:")
    success1 = test_database_access()
    
    # Test 2: With app context (should work)
    print("\n2. Testing with Flask app context:")
    success2 = test_database_access_with_context()
    
    # Test 3: Direct query (should work)
    print("\n3. Testing direct database query:")
    success3 = test_direct_query()
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Test 1 (no context): {'PASS' if not success1 else 'FAIL'} - Expected to fail gracefully")
    print(f"Test 2 (with context): {'PASS' if success2 else 'FAIL'} - Expected to work")
    print(f"Test 3 (direct query): {'PASS' if success3 else 'FAIL'} - Expected to work")
    print("=" * 60)