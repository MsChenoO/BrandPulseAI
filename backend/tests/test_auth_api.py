#!/usr/bin/env python3
"""
Test authentication API endpoints
Phase 5: Authentication Testing
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"


async def test_auth_flow():
    """Test the complete authentication flow"""

    async with httpx.AsyncClient() as client:
        print("=" * 80)
        print("Testing Authentication API")
        print("=" * 80)

        # Test data
        test_user = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpassword123"
        }

        # ====================================================================
        # 1. Register a new user
        # ====================================================================
        print("\n1️⃣  Testing user registration (POST /auth/register)")
        print("-" * 80)

        try:
            response = await client.post(
                f"{API_BASE_URL}/auth/register",
                json=test_user
            )

            if response.status_code == 201:
                data = response.json()
                print(f"✅ Registration successful!")
                print(f"   User ID: {data['user']['id']}")
                print(f"   Email: {data['user']['email']}")
                print(f"   Username: {data['user']['username']}")
                print(f"   Token: {data['access_token'][:50]}...")

                access_token = data["access_token"]
            else:
                print(f"❌ Registration failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return

        except Exception as e:
            print(f"❌ Error during registration: {e}")
            return

        # ====================================================================
        # 2. Login with the registered user
        # ====================================================================
        print("\n2️⃣  Testing user login (POST /auth/login)")
        print("-" * 80)

        try:
            response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": test_user["email"],
                    "password": test_user["password"]
                }
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Login successful!")
                print(f"   User ID: {data['user']['id']}")
                print(f"   Email: {data['user']['email']}")
                print(f"   Username: {data['user']['username']}")
                print(f"   Token: {data['access_token'][:50]}...")

                login_token = data["access_token"]
            else:
                print(f"❌ Login failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return

        except Exception as e:
            print(f"❌ Error during login: {e}")
            return

        # ====================================================================
        # 3. Get current user information
        # ====================================================================
        print("\n3️⃣  Testing get current user (GET /auth/me)")
        print("-" * 80)

        try:
            response = await client.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": f"Bearer {login_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                print(f"✅ Get current user successful!")
                print(f"   User ID: {data['id']}")
                print(f"   Email: {data['email']}")
                print(f"   Username: {data['username']}")
                print(f"   Is Active: {data['is_active']}")
                print(f"   Created At: {data['created_at']}")
            else:
                print(f"❌ Get current user failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return

        except Exception as e:
            print(f"❌ Error getting current user: {e}")
            return

        # ====================================================================
        # 4. Test invalid credentials
        # ====================================================================
        print("\n4️⃣  Testing invalid credentials (POST /auth/login)")
        print("-" * 80)

        try:
            response = await client.post(
                f"{API_BASE_URL}/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "wrongpassword"
                }
            )

            if response.status_code == 401:
                print(f"✅ Invalid credentials correctly rejected!")
                print(f"   Status: {response.status_code}")
            else:
                print(f"❌ Expected 401, got: {response.status_code}")

        except Exception as e:
            print(f"❌ Error testing invalid credentials: {e}")

        # ====================================================================
        # 5. Test invalid token
        # ====================================================================
        print("\n5️⃣  Testing invalid token (GET /auth/me)")
        print("-" * 80)

        try:
            response = await client.get(
                f"{API_BASE_URL}/auth/me",
                headers={"Authorization": "Bearer invalid_token_123"}
            )

            if response.status_code == 401:
                print(f"✅ Invalid token correctly rejected!")
                print(f"   Status: {response.status_code}")
            else:
                print(f"❌ Expected 401, got: {response.status_code}")

        except Exception as e:
            print(f"❌ Error testing invalid token: {e}")

        print("\n" + "=" * 80)
        print("✅ All authentication tests completed!")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_auth_flow())
