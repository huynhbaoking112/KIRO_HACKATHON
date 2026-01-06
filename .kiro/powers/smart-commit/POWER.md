---
name: "smart-commit"
displayName: "Smart Commit"
description: "Auto-generate commit messages based on staged changes and branch naming convention. Supports format {author}/{action}/{name}: {summary}."
keywords: ["commit", "git", "staged", "message", "conventional"]
author: "Alex Huynh"
---

# Smart Commit

## Overview

This power automates the commit process by generating intelligent commit messages based on:
- **Branch naming convention**: `{author}/{action}/{name}` (e.g., `king/feat/auth`)
- **Staged changes**: Analyzes staged changes to create a meaningful summary

Commit message format: `{author}/{action}/{name}: {summary of changes}`

## Workflow

```
1. Check staged changes (git_status)
2. Get current branch name (git_status)
3. View staged diff (git_diff_staged)
4. If more context needed -> read full file
5. Generate commit message following format
6. User confirmation
7. Execute commit (git_commit)
```

## Branch Naming Convention

This power requires branches to follow the format:

```
{author}/{action}/{name}
```

| Part | Description | Examples |
|------|-------------|----------|
| `author` | Person making changes | `king`, `john`, `dev` |
| `action` | Type of change | `feat`, `fix`, `refactor`, `chore`, `docs` |
| `name` | Feature/bug name | `auth`, `login_bug`, `user_model` |

**Example branches:**
- `king/feat/auth` - Authentication feature
- `king/fix/login_bug` - Login bug fix
- `john/refactor/user_service` - User service refactor
- `dev/chore/update_deps` - Dependencies update

## Commit Message Format

```
{branch_name}: {summary}
```

**Examples:**
- `king/feat/auth: Add User model with email and password fields`
- `king/fix/login_bug: Fix null pointer exception in login validation`
- `john/refactor/user_service: Extract validation logic to separate method`

## Available Tools

This power uses Git MCP Server with these tools:

| Tool | Purpose |
|------|---------|
| `git_status` | Check staged changes and get branch name |
| `git_diff_staged` | View detailed staged changes |
| `git_diff` | View diff of specific files if needed |
| `git_commit` | Execute commit with message |
| `git_log` | View commit history (optional) |

## Step-by-Step Workflow

### Step 1: Check Staged Changes

First, check if any files are staged:

```
Tool: git_status
Args: { "repo_path": "." }
```

**Validation:**
- If no staged files -> Notify user to run `git add` first
- If staged files exist -> Continue to step 2
- Extract current branch name from output

### Step 2: Parse Branch Name

Extract parts from branch name:

```
Branch: king/feat/auth
-> author: king
-> action: feat  
-> name: auth
-> prefix: king/feat/auth
```

**Validation:**
- Branch must follow `{author}/{action}/{name}` format
- If format is incorrect -> Ask user for preferred prefix

### Step 3: View Staged Diff

Get detailed changes:

```
Tool: git_diff_staged
Args: { "repo_path": "." }
```

**Analyze diff to understand:**
- Which files are added/modified/deleted
- What are the main changes
- New logic being added

### Step 4: Read File Context (If Needed)

If diff lacks context, read the full file:

```
Tool: read_file (Kiro built-in)
```

**When to read more:**
- New file created and need to understand purpose
- Changes involve multiple functions
- Need to understand relationships between components

### Step 5: Generate Commit Message

Based on analysis, create commit message:

```
Format: {branch_name}: {summary}

Rules:
- Summary should be concise and clear (< 72 chars if possible)
- Describe WHAT changed, not HOW
- Use imperative mood: "Add", "Fix", "Update", not "Added", "Fixed"
```

**Good message examples:**
- `king/feat/auth: Add User model with validation`
- `king/feat/auth: Implement JWT token generation`
- `king/fix/login: Handle empty password case`

### Step 6: User Confirmation

Display commit message and ask user:

```
Suggested commit message:
---
king/feat/auth: Add User model with email and password validation
---

Options:
1. Commit with this message
2. Edit message
3. Cancel
```

### Step 7: Execute Commit

After user confirms:

```
Tool: git_commit
Args: {
  "repo_path": ".",
  "message": "king/feat/auth: Add User model with email and password validation"
}
```

## Example Session

**User:** "commit code"

**Agent:**
```
Checking staged changes...

Status:
- Branch: king/feat/auth
- Staged files:
  - app/domain/models/user.py (new)
  - app/domain/schemas/auth.py (modified)

Analyzing changes...

Suggested commit message:
---
king/feat/auth: Add User model and update auth schemas
---

Changes summary:
- Added User model with fields: id, email, hashed_password, is_active
- Updated AuthSchema to include user validation

Do you want to commit with this message? (yes/edit/no)
```

**User:** "yes"

**Agent:**
```
Committed successfully!

Commit: abc1234
Message: king/feat/auth: Add User model and update auth schemas
Files: 2 files changed
```

## Troubleshooting

### No staged files

**Problem:** `git_status` shows no staged files

**Solution:**
```bash
# Stage files first
git add <files>
# Or stage all
git add .
```

### Branch format incorrect

**Problem:** Branch name does not follow `{author}/{action}/{name}`

**Solution:**
- Agent will ask user for preferred prefix
- Or rename branch: `git branch -m new-branch-name`

### Diff too large

**Problem:** Too many staged changes, hard to summarize

**Solution:**
- Agent will focus on main changes
- May suggest splitting into smaller commits

## Best Practices

1. **Stage logically**: Only stage files related to one change
2. **Commit frequently**: Many small commits are better than one large commit
3. **Review before confirm**: Read the suggested message carefully
4. **Consistent naming**: Keep branch naming convention consistent

## Configuration

**No additional configuration required** - Power works immediately after Git MCP Server installation.

**Prerequisites:**
- Git installed
- Repository initialized (`git init`)
- Files staged (`git add`)

---

**MCP Server:** git (mcp-server-git)
**Installation:** `uvx mcp-server-git`
