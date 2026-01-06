# Review Specific Commits Workflow

## When to Use This Workflow

Load this workflow when the user wants to:
- Review N most recent commits
- Review a specific commit by hash
- Review commits in a time range
- Check commit history quality

## Step-by-Step Instructions

### Step 1: Get Commit List

Fetch the commits to review:

**For recent commits:**
```
Call git_log tool with:
  repo_path: {workspace_path}
  max_count: 10  # or whatever number user specified
```

**For time range:**
```
Call git_log tool with:
  repo_path: {workspace_path}
  max_count: 50
  start_timestamp: "1 week ago"  # or specific date
  end_timestamp: "now"  # optional
```

**Supported timestamp formats:**
- Relative: "1 week ago", "yesterday", "2 days ago"
- Absolute: "2024-01-15", "Jan 15 2024"
- ISO 8601: "2024-01-15T14:30:25"

### Step 2: Get Commit Details

For each commit to review:

```
Call git_show tool with:
  repo_path: {workspace_path}
  revision: "abc123def"  # commit hash from git_log
```

This returns:
- Full commit message
- Author and timestamp
- Complete diff of changes

### Step 3: Explore Project Structure and Read Full Files

**Use `listDirectory` to explore project structure when needed:**
- See related files in the same folder as changed files
- Find test files, config files, or related modules
- Understand how the changed files fit into the project

**Use `readFile` to read full source files for context:**

**Why this is necessary:**
- `git_show` only shows the diff, not the full file context
- You need to understand how changes fit into the overall code
- Changes may reference variables/functions defined elsewhere
- Understanding the full file helps identify related issues

### Step 4: Analyze Each Commit

For every commit, evaluate:

1. **Commit Message Quality**
   - Is it descriptive and clear?
   - Does it follow conventional commits format?
   - Does it reference issue/ticket numbers?
   - Is it in imperative mood?

2. **Commit Scope**
   - Is it atomic (one logical change)?
   - Are unrelated changes mixed in?
   - Would build pass after this commit?

3. **Code Changes**
   - Apply standard review criteria
   - Check if changes match commit message
   - Look for debug code or unintended changes

## Commit Message Quality Checks

### Good Commit Message Format
```
type(scope): subject line under 50 chars

Body explaining WHY the change was made,
not just WHAT changed.

Closes #123
```

### Check For
- Subject line < 50 characters
- Imperative mood ("Add feature" not "Added feature")
- Body explains WHY, not just WHAT
- References issue/ticket number
- No typos or grammar errors

### Common Types
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation changes
- `test`: Test additions/changes
- `chore`: Maintenance tasks

## Output Structure

Present findings in this format:

```markdown
## Commit Review

### Commits Analyzed
| # | Hash | Author | Date | Message |
|---|------|--------|------|---------|
| 1 | abc123 | John | 2024-01-20 | Add user auth |
| 2 | def456 | Jane | 2024-01-19 | Fix login bug |

---

### Commit 1: abc123

**Message:** {full commit message}

**Author:** {name} <{email}>

**Date:** {timestamp}

**Files Changed:** {count} files (+{insertions} / -{deletions})

#### Commit Message Review
- Clear and descriptive
- Imperative mood
- Missing issue reference
- Subject line too long

#### Code Review

**Good:**
- {positive feedback with line numbers}

**Warnings:**
- Line {n}: {warning}
  Suggestion: {improvement}

**Issues:**
- Line {n}: {critical issue}
  Fix: {solution}

#### Commit Score: {score}/10

---

### Overall Summary

**Total Commits Reviewed:** {count}

**Average Score:** {score}/10

**Common Issues Found:**
1. {recurring issue}
2. {recurring issue}

**Recommendations:**
1. {actionable recommendation}
2. {actionable recommendation}
```

## Reviewing Single Commit

When user specifies one commit:

```
User: "Review commit abc123"

Actions:
1. Call git_show with revision="abc123"
2. Analyze that commit in detail
3. Provide comprehensive review
```

## Reviewing Time Range

When user specifies time period:

```
User: "Review commits from last week"

Actions:
1. Call git_log with start_timestamp="1 week ago"
2. For each commit, call git_show
3. Analyze all commits
4. Provide summary with patterns
```

## Common Commit Issues to Flag

### WIP Commits
```
WARNING: Found WIP commits that should be squashed:
- "WIP: working on auth"
- "WIP: more auth stuff"  
- "WIP: almost done"

Recommend: Squash into single meaningful commit before merging
```

### Oversized Commits
```
WARNING: Commit abc123 has 50+ files changed.

This makes it difficult to:
- Review effectively
- Bisect for bugs
- Revert if needed

Recommend: Split into smaller atomic commits
```

### Vague Messages
```
ISSUE: Commit messages lack context:
- "fix bug" - Which bug? What was the issue?
- "update" - Update what? Why?
- "changes" - What changes? Why were they needed?

Recommend: Rewrite with descriptive messages
```

### Secrets in History
```
CRITICAL: Found potential secrets in commit abc123:
- Line 12: API_KEY = "sk-abc123..."
- Line 45: password = "admin123"

IMMEDIATE ACTION REQUIRED:
1. Rotate compromised credentials NOW
2. Remove from git history using git-filter-branch
3. Force push to remote
4. Notify security team
```

### Mixed Changes
```
WARNING: Commit mixes unrelated changes:
- Feature implementation (auth system)
- Unrelated bug fix (typo in docs)
- Dependency update (package.json)

Recommend: Split into separate commits:
1. feat(auth): implement authentication
2. fix(docs): correct typo in README
3. chore(deps): update dependencies
```

## Tips for Commit Reviews

1. **Look for patterns** - Identify recurring issues across commits
2. **Check atomicity** - Each commit should be independently revertable
3. **Verify order** - Commits should have logical progression
4. **Flag WIP commits** - These should be squashed before merge
5. **Check for secrets** - Scan for accidentally committed credentials
6. **Assess message quality** - Good messages help future maintainers
