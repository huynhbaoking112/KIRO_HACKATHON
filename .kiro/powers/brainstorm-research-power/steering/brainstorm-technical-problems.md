# Technical Problem Brainstorming Workflow

This steering file provides specialized guidance for brainstorming technical and software development problems.

## Technical Problem Framework

When the user presents a technical problem, follow this structured approach:

### Phase 1: Technical Context Gathering

Ask these specific questions:
1. **Technology Stack**: What languages, frameworks, or platforms are you using?
2. **Scale Requirements**: How many users/requests/data volume?
3. **Performance Constraints**: Any latency, throughput, or resource limitations?
4. **Existing Architecture**: What's already in place?
5. **Team Expertise**: What technologies does your team know well?
6. **Timeline**: When do you need this implemented?

### Phase 2: Research Strategy

For technical problems, prioritize:

1. **Context7 First** (for library/framework-specific solutions):
   - Use `mcp_context7_resolve_library_id` to find relevant libraries
   - Query documentation with `mcp_context7_query_docs`
   - Look for official patterns and best practices

2. **Web Search Second** (for broader context):
   - Search for "[technology] + [problem] + best practices"
   - Look for recent articles (check published dates)
   - Find real-world case studies and benchmarks
   - Check Stack Overflow discussions for common pitfalls

3. **Cross-Reference**: Compare official docs with community experiences

### Phase 3: Solution Evaluation Criteria

For technical solutions, evaluate based on:

**Performance**
- Latency impact
- Throughput capacity
- Resource usage (CPU, memory, network)

**Scalability**
- Horizontal vs vertical scaling
- Bottlenecks and limitations
- Cost at scale

**Maintainability**
- Code complexity
- Team learning curve
- Documentation quality
- Community support

**Reliability**
- Error handling
- Failure modes
- Recovery mechanisms
- Testing complexity

**Security**
- Attack surface
- Authentication/authorization
- Data protection
- Compliance requirements

**Cost**
- Infrastructure costs
- Development time
- Operational overhead
- Third-party service fees

### Phase 4: Solution Presentation Format

Present technical solutions with this structure:

**Solution [N]: [Technology/Pattern Name]**

**Overview**: One-sentence description

**Technical Approach**:
- Architecture diagram (describe in text)
- Key components
- Data flow

**Implementation Complexity**: [Low/Medium/High]

**Pros**:
- ✅ Performance benefit with metrics if available
- ✅ Scalability characteristics
- ✅ Ecosystem/community support
- ✅ Other advantages

**Cons**:
- ❌ Performance limitations
- ❌ Complexity concerns
- ❌ Cost implications
- ❌ Other drawbacks

**Best For**: 
- Specific use cases where this excels

**Not Recommended For**:
- Scenarios where this is a poor fit

**Code Example**: (if simple enough)
```
// Brief code snippet showing the approach
```

**Resources**:
- [Official Documentation](url)
- [Tutorial/Guide](url)
- [Real-world Example](url)

**Estimated Effort**: [Hours/Days/Weeks]

### Phase 5: Deep Dive Questions

After presenting solutions, ask:
1. "Which solutions align best with your team's expertise?"
2. "What's your priority: performance, simplicity, or cost?"
3. "Do you need this to scale immediately or can you start simple?"
4. "Are there any solutions you want me to research deeper?"

### Common Technical Problem Categories

**Data Storage**
- SQL vs NoSQL vs NewSQL
- Caching strategies
- Data modeling approaches

**API Design**
- REST vs GraphQL vs gRPC
- Authentication methods
- Rate limiting strategies

**Real-time Communication**
- WebSockets vs SSE vs Polling
- Message queues
- Event-driven architectures

**Performance Optimization**
- Caching layers
- Database indexing
- Code-level optimizations
- Infrastructure scaling

**Deployment & Infrastructure**
- Containerization strategies
- CI/CD pipelines
- Monitoring and observability
- Disaster recovery

## Example Technical Brainstorm Session

**User**: "I need to brainstorm solutions for handling file uploads in my Node.js app"

**Agent Response**:

"Let me help you find the best file upload solution. First, a few questions:

1. What's the expected file size range? (Small images vs large videos?)
2. How many concurrent uploads do you expect?
3. Where do you want to store the files? (Local server, cloud storage?)
4. Do you need features like resumable uploads or progress tracking?
5. What's your current hosting setup?

Once I understand your requirements, I'll research and present solutions like:
- Direct server upload with Multer
- Client-side upload to S3/Cloud Storage
- Chunked upload with resumability
- Third-party services (Uploadcare, Cloudinary)

Each with pros/cons for your specific use case."

## Tips for Technical Brainstorming

1. **Start with Context7** for framework-specific questions
2. **Check Recent Sources**: Technology changes fast
3. **Consider Migration Path**: How to get from current to proposed solution
4. **Think About Operations**: Who maintains this? How is it monitored?
5. **Prototype First**: Suggest quick POCs for critical decisions
6. **Benchmark When Possible**: Include performance data if available