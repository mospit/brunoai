#!/usr/bin/env python3
"""
Manual test script to verify registration works without AuthenticationMiddleware.

This script tests the registration endpoint directly by running the server
and making an HTTP request.
"""

import requests
import json
import time
import subprocess
import sys
import signal
import os
from threading import Thread

# Configuration
SERVER_URL = "http://localhost:8000"
REGISTRATION_ENDPOINT = f"{SERVER_URL}/api/users/register"
HEALTH_ENDPOINT = f"{SERVER_URL}/health"

def start_server():
    """Start the FastAPI server."""
    print("Starting server...")
    # Start the server using uvicorn
    cmd = [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    
    # Use shell=True on Windows to handle process properly
    return subprocess.Popen(
        cmd,
        cwd=os.getcwd(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True if os.name == 'nt' else False
    )

def wait_for_server(max_attempts=30, delay=1):
    """Wait for the server to be ready."""
    print(f"Waiting for server to start at {SERVER_URL}...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                print(f"✅ Server is ready! (attempt {attempt + 1})")
                return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1}: Server not ready yet ({e})")
        
        time.sleep(delay)
    
    print(f"❌ Server failed to start after {max_attempts} attempts")
    return False

def test_registration_without_middleware():
    """Test user registration without AuthenticationMiddleware."""
    print("\n=== Testing Registration WITHOUT AuthenticationMiddleware ===")
    
    registration_data = {
        "email": "manual-test@example.com",
        "name": "Manual Test User",
        "password": "ValidPassword123"
    }
    
    print(f"Testing registration with data: {registration_data}")
    
    try:
        response = requests.post(
            REGISTRATION_ENDPOINT,
            json=registration_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Registration worked WITHOUT AuthenticationMiddleware!")
            print("🔍 CONCLUSION: The bug is confirmed to be in AuthenticationMiddleware path matching")
            
            try:
                response_data = response.json()
                print(f"Response data: {json.dumps(response_data, indent=2)}")
                
                # Verify expected fields
                assert "id" in response_data, "Missing user ID in response"
                assert response_data["email"] == registration_data["email"], "Email mismatch"
                assert response_data["name"] == registration_data["name"], "Name mismatch"
                assert response_data["is_active"] is True, "User should be active"
                
                print("✅ All response validations passed")
                
            except Exception as e:
                print(f"⚠️  Response validation error: {e}")
                print(f"Raw response: {response.text}")
                
        else:
            print("❌ FAILURE: Registration failed even WITHOUT AuthenticationMiddleware")
            print("🔍 CONCLUSION: The bug is NOT in AuthenticationMiddleware path matching")
            print(f"Error details: {response.text}")
            
            # Try to parse error response
            try:
                error_data = response.json()
                print(f"Error JSON: {json.dumps(error_data, indent=2)}")
            except:
                print("Could not parse error response as JSON")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
        
    return response.status_code == 200

def main():
    """Main test execution."""
    print("=" * 60)
    print("MANUAL REGISTRATION TEST - WITHOUT AuthenticationMiddleware")
    print("=" * 60)
    
    # Check if main.py has the middleware commented out
    with open("main.py", "r") as f:
        main_content = f.read()
        
    if "# app.add_middleware(\n#     AuthenticationMiddleware\n# )" not in main_content:
        print("❌ ERROR: AuthenticationMiddleware is not commented out in main.py")
        print("Please ensure the middleware is commented out before running this test")
        return False
        
    print("✅ Confirmed: AuthenticationMiddleware is commented out in main.py")
    
    # Start server
    server_process = start_server()
    
    try:
        # Wait for server to be ready
        if not wait_for_server():
            print("❌ Failed to start server")
            return False
            
        # Test registration
        success = test_registration_without_middleware()
        
        if success:
            print("\n" + "=" * 60)
            print("🎉 TEST RESULT: REGISTRATION WORKS WITHOUT MIDDLEWARE")
            print("🔍 CONCLUSION: Bug is confirmed in AuthenticationMiddleware")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ TEST RESULT: REGISTRATION STILL FAILS")
            print("🔍 CONCLUSION: Bug is NOT in AuthenticationMiddleware")
            print("=" * 60)
            
        return success
        
    finally:
        # Clean up server process
        print("\nShutting down server...")
        try:
            if os.name == 'nt':  # Windows
                server_process.terminate()
            else:  # Unix/Linux/Mac
                server_process.send_signal(signal.SIGTERM)
            
            # Wait for graceful shutdown
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
                server_process.wait()
                
            print("Server shutdown complete")
            
        except Exception as e:
            print(f"Error during server shutdown: {e}")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
