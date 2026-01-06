# Review Uncommitted Changes Workflow

## When to Use This Workflow

Load this workflow when the user wants to review:
- Uncommitted changes (work in progress)
- Staged changes (ready to commit)
- Modified files before committing

## Step-by-Step Instructions

### Step 1: Check Repository Status

Start by checking what has changed:

```
Call git_status tool with:
  repo_path: {workspace_path}
```

**Analyze the output to determine:**
- Are there unstaged changes? → Proceed to Step 2
- Are there staged changes? → Proceed to Step 3
- No changes? → Inform user there's nothing to review

### Step 2: Get Unstaged Changes

If unstaged changes exist:

```
Call git_diff_unstaged tool with:
  repo_path: {workspace_path}
  context_lines: 5
```

This returns the diff of modified files not yet staged.

### Step 3: Get Staged Changes

If staged changes exist:

```
Call git_diff_staged tool with:
  repo_path: {workspace_path}
  context_lines: 5
```

This returns the diff of changes ready to commit.

### Step 4: Explore Project Structure and Read Full Files

**Use `listDirectory` to explore project structure when needed:**
- See related files in the same folder
- Find test files, config files, or related modules
- Understand how the changed files fit into the project

**Use `readFile` to read full source files for context:**

**Why this is necessary:**
- Diff only shows changed lines, not the full picture
- You need to understand imports, dependencies, and class structure
- Changes may reference variables/functions defined elsewhere
- Similar patterns in the file may need the same fix

**Read files when:**
- Function changes reference other parts of the file
- You need to understand the class structure
- The change involves imports or dependencies
- You want to check for similar issues elsewhere

### Step 5: Analyze and Provide Feedback

For each file in the diff:

1. **Parse the diff** - Understand what changed (additions, deletions, modifications)
2. **Identify file type** - Determine language (.py, .js, .ts, .java, etc.)
3. **Apply review criteria** - Check code quality, bugs, security, performance, best practices
4. **Generate feedback** - Structure findings using the standard output format

## Language-Specific Checks

### Python Files (.py)
- Check for type hints
- Verify docstrings for functions/classes
- Look for bare `except:` clauses (should be specific)
- Check PEP 8 compliance (naming, spacing)

### JavaScript/TypeScript Files (.js, .ts)
- Check async/await error handling
- Look for null/undefined checks
- Verify TypeScript types are complete
- Check for memory leaks (event listeners, subscriptions)

### SQL/Database Code
- Check for SQL injection vulnerabilities
- Look for N+1 query patterns
- Verify transaction handling
- Check for missing indexes

### All Languages
- Check variable/function naming
- Look for code duplication
- Verify error handling
- Check for hardcoded values
- Review comments for accuracy

## Output Structure

Present findings in this format:

```markdown
## Review: Uncommitted Changes

### Summary
- **Unstaged files:** {count}
- **Staged files:** {count}
- **Total lines changed:** +{insertions} / -{deletions}

### File-by-File Review

#### {filename}

**Changes:** +{insertions} / -{deletions}

**Good:**
- Line {n}: {what was done well}

**Warnings:**
- Line {n}: {potential issue}
  Suggestion: {how to improve}

**Issues:**
- Line {n}: {critical problem}
  Fix: {recommended solution}

### Overall Assessment

**Quality Score:** {score}/10

**Recommendation:** 
- Ready to commit / Needs minor fixes / Needs significant changes

### Action Items
1. {specific action to take}
2. {specific action to take}
```

## Common Patterns to Flag

### Security Red Flags
```python
# BAD - Hardcoded credentials
password = "hardcoded123"

# GOOD - Use environment variables
password = os.environ.get("PASSWORD")
```

### Error Handling Issues
```python
# BAD - Bare except catches everything
try:
    risky_operation()
except:
    pass

# GOOD - Specific exception handling
try:
    risky_operation()
except ValueError as e:
    logger.error(f"Validation failed: {e}")
    raise
```

### Code Quality Issues
```python
# BAD - Unclear naming
def f(x):
    return x * 1.1

# GOOD - Descriptive naming
def calculate_price_with_tax(base_price):
    return base_price * 1.1
```

## Tips for Effective Reviews

1. **Prioritize issues** - Security > Bugs > Performance > Style
2. **Be specific** - Reference exact line numbers
3. **Provide solutions** - Don't just point out problems
4. **Consider context** - Understand what the code is trying to achieve
5. **Check edge cases** - Think about null, empty, boundary values
6. **Focus on logic** - Don't nitpick formatting if linter exists
