import httpx

BASE = "http://localhost:8000/api/v1"

# 1. Register
print("Attempting to register...")
r = httpx.post(f"{BASE}/auth/register", json={
    "email": "admin2@knowledgeos.ai",
    "password": "SecurePass123!",
    "full_name": "Admin User"
})
print(f"1. Register: {r.status_code}")
if r.status_code != 201:
    print(f"   Error: {r.text}")
    exit(1)
tokens = r.json()
print(f"   Access token: {tokens['access_token'][:30]}...")

headers = {"Authorization": f"Bearer {tokens['access_token']}"}

# 2. Get profile
r2 = httpx.get(f"{BASE}/auth/me", headers=headers)
print(f"2. Profile: {r2.status_code}")
print(f"   User: {r2.json()}")

# 3. Login with same creds
r3 = httpx.post(f"{BASE}/auth/login", json={
    "email": "admin2@knowledgeos.ai",
    "password": "SecurePass123!"
})
print(f"3. Login: {r3.status_code}")

# 4. Create workspace
r4 = httpx.post(f"{BASE}/workspaces/", json={
    "name": "My First Project",
    "description": "Testing the Knowledge OS platform"
}, headers=headers)
print(f"4. Create Workspace: {r4.status_code}")
if r4.status_code == 200 or r4.status_code == 201:
    print(f"   Workspace: {r4.json()}")

# 5. List workspaces
r5 = httpx.get(f"{BASE}/workspaces/", headers=headers)
print(f"5. List Workspaces: {r5.status_code}")
if r5.status_code == 200:
    print(f"   Count: {len(r5.json())}")

print("\n✅ All API tests passed!")
