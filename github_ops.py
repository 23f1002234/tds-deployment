from app.github_ops import _get_env
from github import Github


def push_files(repo_name: str, files: dict) -> str:
    """
    Create/update 'main' with the given files and return the new commit SHA.
    files: {"path/filename": "utf-8 text content", ...}
    """
    user, token = _get_env()
    if not token:
        raise RuntimeError("GITHUB_TOKEN not set (push_files)")

    gh = Github(token)
    repo = gh.get_repo(f"{user}/{repo_name}")

    # Try to get current 'main' to decide if this is an update or initial commit
    try:
        ref = repo.get_git_ref("heads/main")
        base_commit = repo.get_git_commit(ref.object.sha)
        base_tree = base_commit.tree
        parents = [base_commit]
        message = "Update application"
    except Exception:
        # No branch/commit yet: initial commit
        base_tree = None
        parents = []
        message = "Initial commit"
        ref = None  # will create it below

    # Create blobs & tree entries
    tree_entries = []
    for path, content in files.items():
        # Text content in UTF-8
        blob = repo.create_git_blob(content, "utf-8")
        tree_entries.append({"path": path, "mode": "100644", "type": "blob", "sha": blob.sha})

    # New tree from entries (+ base_tree when updating)
    new_tree = repo.create_git_tree(tree=tree_entries, base_tree=base_tree)

    # Commit pointing to that tree
    commit = repo.create_git_commit(message, new_tree, parents)

    # Update or create 'main' ref to point to the new commit
    if ref:
        ref.edit(commit.sha)
    else:
        repo.create_git_ref(ref="refs/heads/main", sha=commit.sha)

    # 🔴 IMPORTANT: return the commit SHA
    return commit.sha
