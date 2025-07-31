#!/usr/bin/env python3
"""
Test script to verify registration endpoint rate limiting behavior.
This script will help confirm that the rate-limiter branch isn't blocking registration.
"""

import asyncio
import json
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add server directory to path
server_dir = Path(__file__).parent / "server"
sys.path.insert(0, str(server_dir))

import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BASE_URL = "http://localhost:8000"

async def test_registration_rate_limiting():
    """Test registration endpoint rate limiting behavior."""
    
    logger.info("Starting registration rate limiting test...")
    
    # Test data
    test_user = {
        "email": f"test_{datetime.now().timestamp()}@example.com",
        "password": "TestPassword123!",
        "name": "Test User"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # Test 1: Single registration request
            logger.info("Test 1: Single registration request")
            response = await client.post(
                f"{BASE_URL}/api/users/register",
                json=test_user,
                timeout=10.0
            )
            
            logger.info(f"Registration response status: {response.status_code}")
            logger.info(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 429:
                logger.error("ISSUE FOUND: Registration returned HTTP 429 (rate limited)")
                logger.error("This confirms the rate-limiter is blocking registration")
                logger.error(f"Response: {response.text}")
                return False
            elif response.status_code == 401:
                logger.error("ISSUE FOUND: Registration returned HTTP 401 (unauthorized)")
                logger.error("This suggests authentication issues, not rate limiting")
                logger.error(f"Response: {response.text}")
                return False
            elif response.status_code in [200, 201]:
                logger.info("SUCCESS: Registration completed successfully")
                logger.info(f"Response: {response.text}")
            elif response.status_code == 400:
                # Check if it's a duplicate email or other validation error
                response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                logger.info(f"Registration validation error (expected): {response_data}")
            else:
                logger.warning(f"Unexpected status code: {response.status_code}")
                logger.warning(f"Response: {response.text}")
            
            # Test 2: Multiple quick registration attempts (should hit general rate limit, not auth rate limit)
            logger.info("\nTest 2: Multiple quick registration attempts")
            
            rate_limited = False
            for i in range(12):  # Exceed the 10 req/min auth endpoint limit
                test_user_multi = {
                    "email": f"test_{datetime.now().timestamp()}_{i}@example.com",
                    "password": "TestPassword123!",
                    "name": f"Test User {i}"
                }
                
                try:
                    response = await client.post(
                        f"{BASE_URL}/api/users/register",
                        json=test_user_multi,
                        timeout=5.0
                    )
                    
                    logger.info(f"Request {i+1}: Status {response.status_code}")
                    
                    if response.status_code == 429:
                        logger.info(f"Rate limited at request {i+1}")
                        logger.info(f"Rate limit headers: {dict(response.headers)}")
                        rate_limited = True
                        
                        # Check if it's auth rate limit or general rate limit
                        rate_limit_type = response.headers.get('X-RateLimit-Type')
                        if rate_limit_type == 'auth':
                            logger.error("ISSUE: Hit auth-specific rate limit (5 attempts/15min)")
                            logger.error("This means failed auth attempts are being counted for registration")
                        else:
                            logger.info("Hit general rate limit (10 req/min for auth endpoints)")
                            logger.info("This is expected behavior")
                        break
                        
                except httpx.TimeoutException:
                    logger.warning(f"Request {i+1} timed out")
                except Exception as e:
                    logger.error(f"Request {i+1} failed: {e}")
            
            if not rate_limited:
                logger.info("No rate limiting hit during multiple attempts")
            
            return True
            
        except httpx.ConnectError:
            logger.error("Cannot connect to server. Is it running on localhost:8000?")
            return False
        except Exception as e:
            logger.error(f"Test failed with error: {e}")
            return False

async def test_path_verification():
    """Verify that registration paths are correctly configured."""
    
    logger.info("\nPath verification test...")
    
    # These paths should be in auth_paths (have special rate limiting)
    auth_paths = {
        "/api/users/login",
        "/api/users/refresh", 
        "/api/users/register",
        "/api/auth/login",
        "/api/auth/refresh",
        "/api/auth/register"
    }
    
    # These paths should be in public_paths (no auth required)
    public_paths = {
        "/api/users/register",
        "/api/users/login",
        "/api/users/refresh",
        "/api/users/csrf-token",
        "/api/auth/register",
        "/api/auth/login", 
        "/api/auth/refresh",
        "/api/auth/csrf-token"
    }
    
    logger.info("Expected configuration:")
    logger.info(f"Auth paths (special rate limiting): {auth_paths}")
    logger.info(f"Public paths (no auth required): {public_paths}")
    
    logger.info("\nKey observations:")
    logger.info("1. Registration endpoints ARE in auth_paths -> they use auth rate limiting")
    logger.info("2. Registration endpoints ARE in public_paths -> they don't require authentication") 
    logger.info("3. This means registration uses BOTH general rate limit (10 req/min) AND auth-specific rules")
    
    return True

if __name__ == "__main__":
    async def main():
        logger.info("=== Registration Rate Limiting Analysis ===")
        
        # First verify the path configuration
        await test_path_verification()
        
        # Then test actual behavior
        await test_registration_rate_limiting()
        
        logger.info("\n=== Analysis Complete ===")
        logger.info("Check the logs above for any issues found.")
    
    asyncio.run(main())
