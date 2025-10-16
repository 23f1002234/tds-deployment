# app/main.py
import os
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from dotenv import load_dotenv
import requests
from pathlib import Path

from .validator import validate_request, verify_secret
from .storage import init_storage, load_tasks, save_tasks
from .github_ops import create_repo, push_files, enable_pages
from .ai import generate_code, generate_updates

# Load the .env from the project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="LLM Deployment API (Python)")

@app.get("/favicon.ico")
def favicon():
    # 1x1 transparent PNG
    data = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc```\x00"
            b"\x00\x00\x05\x00\x01\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")
    return Response(content=data, media_type="image/png")


@app.on_event("startup")
def on_startup():
    init_storage()
    print("✓ Storage initialized")
    print("✓ Server ready at http://localhost:8000")
    print("✓ Endpoint: POST /api/build")


@app.get("/")
def health():
    return {
        "status": "online",
        "message": "FastAPI server is running",
        "endpoint": "/api/build (POST only)",
        "ts": time.time()
    }


@app.post("/api/build")
async def build(request: Request):
    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    ok, err = validate_request(body)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    if not verify_secret(body["secret"]):
        raise HTTPException(status_code=401, detail="Invalid secret")

    # immediate ack
    ack = {
        "status": "accepted",
        "task": body["task"],
        "round": body["round"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    # run background
    import asyncio
    asyncio.create_task(process_task(body))

    return JSONResponse(content=ack, status_code=200)


async def process_task(data: dict):
    email = data["email"]
    task = data["task"]
    round_ = data["round"]
    nonce = data["nonce"]
    brief = data["brief"]
    checks = data["checks"]
    evaluation_url = data["evaluation_url"]
    attachments = data.get("attachments", [])

    tasks = load_tasks()

    try:
        if round_ == 1:
            print(f"[Round 1] Starting task: {task}")
            
            # 1) generate files
            print("  → Generating code with LLM...")
            files = generate_code(brief, checks, attachments)

            # 2) create repo
            print("  → Creating GitHub repository...")
            repo_name = f"{task}-{int(time.time())}"
            repo_url = create_repo(repo_name)
            print(f"  ✓ Repo created: {repo_url}")

            # 3) push files
            print("  → Pushing files to repo...")
            commit_sha = push_files(repo_name, files)
            print(f"  ✓ Committed: {commit_sha[:7]}")

            # 4) enable pages
            print("  → Enabling GitHub Pages...")
            pages_url = enable_pages(repo_name)
            print(f"  ✓ Pages live: {pages_url}")

            # persist
            tasks[task] = {
                "email": email,
                "repoName": repo_name,
                "repoUrl": repo_url,
                "pagesUrl": pages_url,
                "commitSha": commit_sha,
                "round1": {
                    "brief": brief,
                    "checks": checks,
                    "nonce": nonce,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                }
            }
            save_tasks(tasks)
            print("  ✓ Task saved to storage")

            # 5) notify eval
            print("  → Notifying evaluation API...")
            notify_eval(evaluation_url, {
                "email": email,
                "task": task,
                "round": 1,
                "nonce": nonce,
                "repo_url": repo_url,
                "commit_sha": commit_sha,
                "pages_url": pages_url
            })
            print(f"[Round 1] ✓ Completed: {task}")

        elif round_ == 2:
            print(f"[Round 2] Starting task: {task}")
            info = tasks.get(task)
            if not info:
                raise RuntimeError(f"No round 1 info found for task: {task}")

            # 1) generate updates
            print("  → Generating updated code...")
            updated_files = generate_updates(info, brief, checks, attachments)

            # 2) push
            print("  → Pushing updates to repo...")
            commit_sha = push_files(info["repoName"], updated_files)
            print(f"  ✓ Committed: {commit_sha[:7]}")

            # optional: small wait for pages redeploy
            print("  → Waiting for Pages to redeploy...")
            time.sleep(30)

            # persist
            info["round2"] = {
                "brief": brief,
                "checks": checks,
                "nonce": nonce,
                "commitSha": commit_sha,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
            save_tasks(tasks)
            print("  ✓ Task updated in storage")

            # 3) notify eval
            print("  → Notifying evaluation API...")
            notify_eval(evaluation_url, {
                "email": email,
                "task": task,
                "round": 2,
                "nonce": nonce,
                "repo_url": info["repoUrl"],
                "commit_sha": commit_sha,
                "pages_url": info["pagesUrl"]
            })
            print(f"[Round 2] ✓ Completed: {task}")

    except Exception as e:
        print(f"[ERROR] Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()


def notify_eval(url: str, payload: dict):
    delays = [1, 2, 4, 8, 16]  # seconds
    for i, d in enumerate(delays, start=1):
        try:
            r = requests.post(
                url, 
                json=payload, 
                headers={"Content-Type": "application/json"}, 
                timeout=30
            )
            print(f"  [notify_eval] attempt {i} → status {r.status_code}")
            if r.status_code == 200:
                print("  ✓ Evaluation notified successfully")
                return
            else:
                print(f"  ✗ Response: {r.text[:200]}")
        except Exception as e:
            print(f"  ✗ Notify error: {e}")
        
        if i < len(delays):
            print(f"  → Retrying in {d}s...")
            time.sleep(d)
    
    print("  ✗ Failed to notify evaluation after all retries")