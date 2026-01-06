---
name: "code-review-assistant"
displayName: "Code Review Assistant"
description: "AI-powered code review using Git MCP server. Review uncommitted changes, branch diffs, or specific commits with detailed feedback on code quality, bugs, security, and best practices."
keywords: ["code-review", "git-diff", "pull-request", "code-quality", "review"]
author: "Alex Huynh"
---

# Code Review Assistant

## Overview

This power enables you to perform comprehensive code reviews using Git MCP server tools.

**IMPORTANT: When the user requests a code review, ALWAYS ask them to choose the review type first:**

1. **Uncommitted Changes** - Review work in progress (unstaged/staged changes)
2. **Branch Comparison** - Compare two branches (e.g., feature vs main)
3. **Commit History** - Review specific commits or recent commit history

After the user selects a review type, load the appropriate steering file and analyze changes with detailed feedback on:

- **Code Quality** - Clean code, readability, maintainability
- **Potential Bugs** - Logic errors, edge cases, null checks
- **Security Issues** - SQL injection, XSS, hardcoded secrets
- **Performance** - N+1 queries, unnecessary loops, memory leaks
- **Best Practices** - Design patterns, SOLID principles, conventions

## Available Steering Files

Load the appropriate steering file based on what the user wants to review:

| Steering File | When to Load |
|---------------|--------------|
| `review-uncommitted.md` | User wants to review uncommitted changes (work in progress) |
| `review-branch-diff.md` | User wants to compare branches (pre-PR review) |
| `review-commits.md` | User wants to review specific commits or commit history |

## MCP Tools Available

Use these tools from `mcp-server-git`:

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `git_status` | Check working directory status | Start of uncommitted review |
| `git_diff_unstaged` | Get unstaged changes | Review work in progress |
| `git_diff_staged` | Get staged changes | Review changes ready to commit |
| `git_diff` | Compare branches/commits | Branch comparison |
| `git_log` | Get commit history | List commits to review |
| `git_show` | Get specific commit details | Review individual commits |
| `git_branch` | List branches | Identify available branches |

## Reading Files and Exploring Project Structure

**IMPORTANT:** Diff output alone is often NOT enough for a proper code review. You need to understand the full context.

### Use `listDirectory` tool to explore project structure when:
- You need to understand the project layout
- You want to see related files in the same folder
- You need to find test files, config files, or related modules
- The change affects multiple areas and you need to map the codebase

### Use `readFile` tool to read full files when:
- The diff shows changes to a function but you need to see the full function
- You need to understand imports and dependencies
- The change references variables/functions defined elsewhere in the file
- You want to check if similar patterns exist elsewhere in the file
- The change affects class methods and you need to see the full class

**Example workflow:**
1. Get diff using git tools → See what files changed
2. Use `listDirectory` to explore related folders if needed → Understand project structure
3. Use `readFile` to read the full changed files → Understand full context
4. Analyze changes with complete understanding → Provide accurate review

## Review Criteria to Apply

When analyzing code changes, check for:

### 1. Code Quality
- Naming conventions (variables, functions, classes)
- Code duplication (DRY principle)
- Function/method length and complexity
- Comments and documentation quality

### 2. Potential Bugs
- Null/undefined checks
- Error handling (try-catch blocks)
- Edge cases handling
- Type mismatches
- Race conditions

### 3. Security
- Input validation
- SQL injection vulnerabilities
- XSS vulnerabilities
- Hardcoded credentials/secrets
- Sensitive data exposure

### 4. Performance
- N+1 query problems
- Unnecessary loops or iterations
- Memory leaks
- Inefficient algorithms
- Missing caching opportunities

### 5. Best Practices
- SOLID principles adherence
- Design patterns usage
- Framework conventions
- Testing coverage
- Error messages quality

## Standard Output Format

Structure your review output as follows:

```
## Summary
- Files changed: X
- Insertions: +Y
- Deletions: -Z

## Findings

### Good Practices
- [file:line] Description of what was done well

### Warnings
- [file:line] Description of potential issue
  Suggestion: How to improve

### Issues
- [file:line] Description of problem
  Fix: Recommended solution

### Suggestions
- [file:line] Optional improvement ideas
```

## Workflow Selection

Determine which workflow to use based on user request:

**Uncommitted changes keywords:**
- "review my changes"
- "check uncommitted"
- "review work in progress"
- "check what I changed"

→ Load `review-uncommitted.md`

**Branch diff keywords:**
- "compare with main"
- "review branch"
- "pre-PR review"
- "diff between branches"

→ Load `review-branch-diff.md`

**Commit review keywords:**
- "review commits"
- "check commit history"
- "review last N commits"
- "show commit abc123"

→ Load `review-commits.md`

## Important Notes

- **ALWAYS ask user to choose review type first** if they haven't specified
- Present the 3 options clearly: Uncommitted Changes, Branch Comparison, or Commit History
- Always use workspace path as `repo_path` parameter for git tools
- Set `context_lines: 5` for better diff context
- Prioritize security issues over style issues
- Be constructive - provide solutions, not just criticism
- Consider the programming language when applying review criteria

## Error Handling

If git tools return errors:

- **"Repository not found"** → Inform user workspace is not a git repository
- **"No changes detected"** → Inform user there are no changes to review
- **"Branch not found"** → Ask user to verify branch name
- **"Invalid revision"** → Ask user to provide valid commit hash

---