import httpx
import time

BASE = "http://localhost:8001/api/v1"

print("1. Login...")
r = httpx.post(f"{BASE}/auth/login", json={
    "email": "debug_auth@knowledgeos.ai",
    "password": "SecurePass123!"
})
if r.status_code != 200:
    print(f"Login failed: {r.text}")
    exit(1)
    
tokens = r.json()
headers = {"Authorization": f"Bearer {tokens['access_token']}"}

print("2. Create Workspace...")
r_ws = httpx.post(f"{BASE}/workspaces/", json={
    "name": "Doc Upload Test",
    "description": "Testing the ingestion pipeline"
}, headers=headers)
if r_ws.status_code not in (200, 201):
    print(f"Workspace creation failed: {r_ws.text}")
    exit(1)
    
workspace_id = r_ws.json()["id"]
print(f"   Workspace ID: {workspace_id}")

print("3. Upload Document...")
files = {'file': ('test.txt', b"Knowledge OS is an enterprise AI platform. It supports semantic search, RAG, and more. This is a short test document to ensure chunking and embeddings are generated properly.", 'text/plain')}
r_upload = httpx.post(f"{BASE}/documents/upload?workspace_id={workspace_id}", headers=headers, files=files)
if r_upload.status_code != 201:
    print(f"Upload failed: {r_upload.text}")
    exit(1)

doc_id = r_upload.json()["id"]
print(f"   Document ID: {doc_id}")
print(f"   Status: {r_upload.json()['status']}")

print("4. Wait for processing...")
for i in range(10):
    time.sleep(2)
    r_doc = httpx.get(f"{BASE}/documents/{doc_id}", headers=headers)
    if r_doc.status_code != 200:
        print(f"   GET failed: {r_doc.text}")
        break
    doc = r_doc.json()
    print(f"   Status: {doc['status']}")
    if doc['status'] in ('completed', 'failed'):
        print(f"   Chunk count: {doc['chunk_count']}")
        if doc.get('error_message'):
            print(f"   Error: {doc['error_message']}")
        break

print("\nDone.")
