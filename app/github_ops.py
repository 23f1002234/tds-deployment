# app/github_ops.py
import os
import time
import requests
from github import Github, InputGitTreeElement
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

def _get_env():
    username = os.getenv("GITHUB_USERNAME")
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set")
    if not username:
        raise RuntimeError("GITHUB_USERNAME not set")
    return username, token

def create_repo(repo_name: str) -> str:
    username, token = _get_env()
    gh = Github(token)
    user = gh.get_user()
    repo = user.create_repo(
        name=repo_name, 
        description="Auto-generated application",
        private=False, 
        auto_init=True  # Initialize with README to avoid empty repo
    )
    # Wait a moment for initialization
    time.sleep(2)
    return repo.html_url


def push_files(repo_name: str, files: dict) -> str:
    """
    Commit multiple text files to main. Returns commit sha.
    files = {"index.html": "<html>...", "README.md": "..."}
    """
    username, token = _get_env()
    gh = Github(token)
    repo = gh.get_repo(f"{username}/{repo_name}")

    # Wait for repo to be ready (if just created)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            ref = repo.get_git_ref("heads/main")
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Waiting for repo to initialize... (attempt {attempt + 1})")
                time.sleep(2)
            else:
                raise RuntimeError(f"Repository not ready after {max_retries} attempts: {e}")

    # Get the current commit
    base_commit = repo.get_git_commit(ref.object.sha)
    base_tree = base_commit.tree

    # Create blobs and tree elements using InputGitTreeElement
    tree_elems = []
    for path, content in files.items():
        blob = repo.create_git_blob(content, "utf-8")
        # Use InputGitTreeElement class instead of dict
        tree_elem = InputGitTreeElement(
            path=path,
            mode="100644",
            type="blob",
            sha=blob.sha
        )
        tree_elems.append(tree_elem)

    # Create new tree
    new_tree = repo.create_git_tree(tree=tree_elems, base_tree=base_tree)
    
    # Create commit
    commit = repo.create_git_commit(
        message="Update application",
        tree=new_tree,
        parents=[base_commit]
    )
    
    # Update reference
    ref.edit(commit.sha)
    
    return commit.sha


def enable_pages(repo_name: str) -> str:
    """
    Enable GitHub Pages for main branch at root and wait until it's live.
    Returns the public pages URL.
    """
    username, token = _get_env()
    pages_url = f"https://{username}.github.io/{repo_name}/"
    api = f"https://api.github.com/repos/{username}/{repo_name}/pages"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "llm-deployment-py",
    }
    payload = {"source": {"branch": "main", "path": "/"}}

    print(f"Enabling GitHub Pages...")
    r = requests.post(api, json=payload, headers=headers, timeout=30)
    
    # If already exists, keep going
    if r.status_code not in (201, 204):
        if "already" not in r.text.lower():
            print(f"Pages enable response: {r.status_code} - {r.text[:200]}")
            # Don't raise, continue anyway

    # Poll until 200 OK (up to ~2 min)
    print(f"Waiting for GitHub Pages to deploy at {pages_url}...")
    for i in range(24):
        try:
            resp = requests.get(pages_url, timeout=8)
            if resp.status_code == 200:
                print(f"✓ Pages live after {i*5} seconds")
                break
        except Exception:
            pass
        if i < 23:  # Don't sleep on last iteration
            time.sleep(5)
    else:
        print(f"Warning: Pages may not be fully deployed yet after 2 minutes")

    return pages_url

__all__ = ["create_repo", "push_files", "enable_pages"]