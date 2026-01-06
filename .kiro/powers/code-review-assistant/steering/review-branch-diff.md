# Review Branch Diff Workflow

## When to Use This Workflow

Load this workflow when the user wants to:
- Compare current branch with main/master/develop
- Perform pre-PR review
- Review feature branch before merging
- Check all changes in a branch

## Step-by-Step Instructions

### Step 1: Identify Branches

First, list available branches:

```
Call git_branch tool with:
  repo_path: {workspace_path}
  branch_type: "all"
```

**Determine:**
- Current branch (where user is now)
- Target branch to compare against (usually main, master, or develop)

If user doesn't specify target branch, ask them which branch to compare with.

### Step 2: Get Branch Diff

Compare current branch with target:

```
Call git_diff tool with:
  repo_path: {workspace_path}
  target: "main"  # or whatever target branch user specified
  context_lines: 5
```

**Note:** The `target` parameter is the branch to compare against. The diff shows changes from target → current branch.

### Step 3: Get Commit History

Fetch commits in the branch:

```
Call git_log tool with:
  repo_path: {workspace_path}
  max_count: 20
```

This helps understand the progression of changes.

### Step 4: Explore Project Structure and Read Full Files

**Use `listDirectory` to explore project structure when needed:**
- See related files in the same folder
- Find test files, config files, or related modules
- Understand how the changed files fit into the project
- Map dependencies between modules

**Use `readFile` to read full source files for context:**

**Why this is necessary:**
- Diff only shows changed lines, not the full picture
- You need to understand imports, dependencies, and class structure
- Changes may reference variables/functions defined elsewhere
- Breaking changes may affect other parts of the file

**Read files when:**
- Function changes reference other parts of the file
- You need to understand the class/module structure
- The change involves imports or dependencies
- You want to verify the change doesn't break existing code

### Step 5: Comprehensive Analysis

Analyze the entire diff considering:

1. **Scope** - Is this PR too large? Should it be split?
2. **Cohesion** - Are all changes related to the same feature/fix?
3. **Breaking changes** - Any API or interface changes?
4. **Dependencies** - New or removed dependencies?
5. **Tests** - Are there tests for new code?
6. **Documentation** - Is documentation updated?

## Review Checklist

Apply these checks:

### PR Readiness
- All changes related to one feature/fix?
- No unrelated changes mixed in?
- Commit messages meaningful?
- No debug code or console.log statements?
- No commented-out code?

### Architecture
- Changes follow existing patterns?
- Doesn't break existing functionality?
- API changes backward compatible?
- Database migrations reversible?

### Testing
- Tests for new code?
- Existing tests still pass?
- Edge cases covered?
- Integration points tested?

### Documentation
- README updated if needed?
- API docs updated?
- Inline comments for complex logic?
- CHANGELOG updated?

## Output Structure

Present findings in this format:

```markdown
## Branch Review: {current_branch} → {target_branch}

### Summary
- **Commits:** {count}
- **Files changed:** {count}
- **Total changes:** +{insertions} / -{deletions}

### Commit Overview
| Hash | Author | Message |
|------|--------|---------|
| abc123 | John | Add user authentication |
| def456 | John | Fix login validation |

### Changes by Category

#### New Files
- `path/to/file.py` - Brief description

#### Modified Files
- `path/to/file.py` - What changed

#### Deleted Files
- `path/to/file.py` - Why deleted

### Detailed Review

#### High Priority Issues
1. **[security]** `file.py:45`
   - Description of critical issue
   - Fix: Specific solution

#### Medium Priority Warnings
1. **[performance]** `file.py:23`
   - Description of concern
   - Suggestion: How to improve

#### Low Priority Suggestions
1. **[style]** `file.py:12`
   - Description of minor improvement
   - Consider: Alternative approach

### Breaking Changes
- List any breaking changes found
- Impact on existing code

### Dependencies
- Added: package-name==version (reason)
- Removed: package-name (reason)

### Overall Assessment

**PR Quality Score:** {score}/10

**Recommendation:**
- Ready to merge
- Approve with minor comments
- Request changes

### Required Actions Before Merge
1. Specific action item
2. Specific action item
```

## Comparing with Remote Branches

If user wants to compare with remote branch:

```
Call git_diff tool with:
  repo_path: {workspace_path}
  target: "origin/main"  # Note the "origin/" prefix
```

## Special Considerations

### Large PRs
If PR has 50+ files changed, flag this:
```
WARNING: This PR is very large (50+ files).
Consider splitting into smaller PRs for easier review:
- PR 1: Database schema changes
- PR 2: Backend API implementation
- PR 3: Frontend integration
```

### Unrelated Changes
Flag changes that don't belong:
```
WARNING: Found unrelated changes:
- package-lock.json (dependency update unrelated to feature)
- .gitignore (should be separate PR)

Recommend: Remove unrelated changes or create separate PR
```

### Missing Tests
If new code lacks tests:
```
ISSUE: New code without test coverage:
- src/auth/login.py (0% coverage)
- src/auth/permissions.py (0% coverage)

Recommend: Add tests before merging
```

## Tips for Branch Reviews

1. **Review commit by commit first** - Understand the flow of changes
2. **Check for conflicts** - Ensure branch is up-to-date with target
3. **Look for feature flags** - New features should be flagged
4. **Verify rollback plan** - Can changes be rolled back safely?
5. **Consider deployment** - Any special deployment requirements?
6. **Check for secrets** - No accidentally committed credentials
