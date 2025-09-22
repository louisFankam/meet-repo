#!/usr/bin/env python3
"""
Test script to simulate web requests and verify database session context
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model.services import UserService
from model.database import db
from model.models import User
from flask import Flask, request, jsonify
import json

def create_test_app():
    """Create a test Flask app"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/meet_db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    db.init_app(app)
    
    @app.route('/test-login')
    def test_login():
        """Test login endpoint"""
        email = request.args.get('email')
        password = request.args.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        user = UserService.get_user_by_email(email)
        
        if user and user.check_password(password):
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.full_name
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
    
    @app.route('/test-user/<int:user_id>')
    def test_user_by_id(user_id):
        """Test get user by ID endpoint"""
        user = UserService.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.full_name
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
    
    return app

def test_web_requests():
    """Test web requests"""
    print("Testing web requests...")
    
    app = create_test_app()
    
    with app.test_client() as client:
        print("\n1. Testing login with valid credentials:")
        response = client.get('/test-login?email=Dominiquelouis15+1@gmail.com&password=test123')
        data = json.loads(response.data)
        print(f"Status: {response.status_code}")
        print(f"Response: {data}")
        
        print("\n2. Testing login with invalid credentials:")
        response = client.get('/test-login?email=Dominiquelouis15+1@gmail.com&password=wrongpassword')
        data = json.loads(response.data)
        print(f"Status: {response.status_code}")
        print(f"Response: {data}")
        
        print("\n3. Testing get user by ID:")
        response = client.get('/test-user/1')
        data = json.loads(response.data)
        print(f"Status: {response.status_code}")
        print(f"Response: {data}")
        
        print("\n4. Testing get user by invalid ID:")
        response = client.get('/test-user/999')
        data = json.loads(response.data)
        print(f"Status: {response.status_code}")
        print(f"Response: {data}")

if __name__ == '__main__':
    print("=" * 60)
    print("WEB REQUEST CONTEXT TEST")
    print("=" * 60)
    
    test_web_requests()
    
    print("\n" + "=" * 60)
    print("WEB REQUEST TEST COMPLETED")
    print("=" * 60)