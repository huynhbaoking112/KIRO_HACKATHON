---
name: brainstorm-research
displayName: Brainstorm Research
description: Interactive brainstorming assistant that helps find solutions through structured research using web search and Context7 documentation
keywords: [brainstorm, research, solution, how to solve, problem solving, ideas, approach]
author: Alex Huynh
---

# Brainstorm Research Power

Guide users through systematic brainstorming and research to find solutions for any problem.

## Overview

This power activates when users mention keywords like "brainstorm", "solution", "how to solve", or "research options". Follow the structured problem-solving workflow below.

## Available Steering Files

Load specific workflow guides based on problem type:

| Steering File | When to Load |
|---------------|--------------|
| `brainstorm-technical-problems.md` | Software architecture, library selection, performance issues |
| `brainstorm-business-problems.md` | Process improvements, team dynamics, strategy decisions |
| `brainstorm-creative-problems.md` | UX/UI decisions, branding, content strategy |

## Tools to Use

This is a Knowledge Base Power leveraging Kiro's built-in capabilities:

- **`remote_web_search`**: Search for current information, best practices, real-world examples
- **`mcp_context7_resolve_library_id`** + **`mcp_context7_query_docs`**: Query technical documentation for library-specific solutions

## Workflow Instructions

### Step 1: Problem Clarification

Ask the user these questions before researching:
- What is the core problem being solved?
- What are the constraints (time, budget, technical limitations)?
- What has already been tried?
- What is the desired outcome?

### Step 2: Research & Information Gathering

Based on user answers:
1. Use `remote_web_search` to find relevant solutions and best practices
2. For technical problems, use Context7 to query library documentation
3. Identify common patterns and approaches from search results

### Step 3: Solution Presentation

Present 3-5 potential solutions using this format:

```
**Solution [N]: [Name]**
- **Description**: Brief overview of the approach
- **Pros**: Key advantages (bullet list)
- **Cons**: Key disadvantages (bullet list)
- **Best For**: Scenarios where this solution excels
- **Resources**: Links to documentation, tutorials, examples
```

### Step 4: Refinement & Selection

After presenting solutions:
1. Ask which solutions interest the user most
2. Provide deeper analysis on selected options
3. Help make a final decision
4. Offer implementation guidance if needed

## Example Interactions

### Technical Problem
```
User: "I need to brainstorm solutions for handling real-time notifications in my web app"

Agent actions:
1. Ask about scale, tech stack, budget
2. Search: "real-time notifications web app best practices 2024"
3. Query Context7 for WebSocket/SSE documentation if applicable
4. Present solutions: WebSockets, Server-Sent Events, polling, third-party services
5. Help user choose based on constraints
```

### Business Problem
```
User: "How to solve team communication issues in remote work?"

Agent actions:
1. Clarify team size, current tools, specific pain points
2. Search: "remote team communication best practices"
3. Present approaches: async-first, scheduled syncs, documentation culture
4. Guide to best fit for the team
```

## Common Issues & Handling

| Issue | Cause | How to Handle |
|-------|-------|---------------|
| Research results too generic | Problem statement too broad | Ask user for more specific context |
| Solutions don't fit use case | Missing constraints | Ask about specific limitations |
| Need more technical depth | Wrong workflow | Load `brainstorm-technical-problems.md` steering file |
| Context7 returns nothing | Library name not recognized | Ask user for exact library/framework name |

## Research Tips

- Prioritize recent sources (check published dates)
- Cross-reference official docs with community experiences
- For technical problems, always check Context7 first
- Include performance benchmarks when available
- Consider long-term maintenance and scalability