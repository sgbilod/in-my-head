# IN MY HEAD - DEVELOPMENT INSTRUCTIONS

## 🎯 PROJECT MISSION

Build **"In My Head"** - a revolutionary AI-powered personal knowledge management system that surpasses NotebookLM by 1000x through:

- **100% local-first architecture** with complete privacy
- **Multi-modal document processing** (text, audio, video, images, code)
- **Autonomous resource discovery** and intelligent management
- **Real-time semantic search** and knowledge synthesis
- **Extensible plugin ecosystem** for customization

**Brand Promise**: "Your Knowledge, Infinitely Connected, Eternally Private, Boundlessly Intelligent"

---

## 🏗️ ARCHITECTURE PRINCIPLES

### 1. Privacy-First Design ✅

**MANDATORY RULES:**

- All sensitive data processing MUST occur locally by default
- External API calls require explicit user consent with clear warnings
- End-to-end encryption for any optional cloud sync features
- Comprehensive audit logging for all data access
- Zero telemetry without user opt-in
- No data ever sent to external servers without permission

**Implementation:**

```python
# All document processing happens locally
class DocumentProcessor:
    def process(self, file_path: str) -> Document:
        # Process locally, no external calls
        pass
```

### 2. Modular Microservices Architecture 🏗️

**Service Boundaries:**

- Each service is independent and containerized
- Communication via REST API or message queues (Redis)
- Services can be scaled independently
- Clear separation of concerns
- Health checks on all services

**Services:**

1. **API Gateway**: Request routing, auth, rate limiting
2. **Document Processor**: File parsing and extraction
3. **AI Engine**: LLM inference and embeddings
4. **Search Service**: Vector and keyword search
5. **Resource Manager**: Auto-discovery and optimization

### 3. AI-Agnostic Core 🤖

**Multi-Model Support:**

- Support multiple LLM providers (Claude, GPT, Gemini, local models)
- Abstract AI interactions behind unified interface
- Allow users to switch models seamlessly
- Fallback mechanisms for API failures
- Local LLM as default (privacy first)

**Example:**

```typescript
interface AIProvider {
  generateEmbedding(text: string): Promise<number[]>;
  generateResponse(prompt: string): Promise<string>;
  getSupportedModels(): string[];
}
```

### 4. Performance-Critical ⚡

**Hard Requirements:**

- Target <200ms response time for queries (p95)
- Lazy loading and intelligent caching strategies
- Efficient vector search with HNSW indices
- Memory-efficient document processing (streaming)
- Batch processing for large operations

**Benchmarks:**

- Document indexing: >1000 docs/minute
- Query response: <200ms (p95)
- Memory usage: <500MB idle, <2GB active
- Startup time: <5 seconds

---

## 📝 CODING STANDARDS

### TypeScript/JavaScript Standards

**Style:**

- Use TypeScript for ALL frontend and Node.js code
- ESLint + Prettier for code formatting
- Strict type checking enabled (`strict: true`)
- Functional programming patterns preferred
- Avoid `any` type - use proper types or `unknown`

**Structure:**

```typescript
// Good: Type-safe with interfaces
interface Document {
  id: string;
  title: string;
  content: string;
  metadata: DocumentMetadata;
}

function processDocument(doc: Document): ProcessedDocument {
  // Implementation
}

// Bad: Using any
function processDocument(doc: any) {
  // Don't do this
}
```

**Rules:**

- Maximum function length: 50 lines
- Maximum file length: 300 lines
- Use async/await, not callbacks
- Comprehensive JSDoc comments for public APIs
- Named exports preferred over default exports

### Python Standards

**Style:**

- Follow PEP 8 style guide strictly
- Type hints for all function signatures
- Black for code formatting (line length: 100)
- Maximum function length: 50 lines
- Docstrings for all public functions (Google style)

**Structure:**

```python
from typing import List, Dict, Optional

def process_documents(
    file_paths: List[str],
    options: Optional[Dict[str, str]] = None
) -> List[Document]:
    """
    Process multiple documents and return parsed results.

    Args:
        file_paths: List of file paths to process
        options: Optional processing configuration

    Returns:
        List of processed Document objects

    Raises:
        FileNotFoundError: If any file doesn't exist
        ProcessingError: If processing fails
    """
    # Implementation
    pass
```

**Tools:**

- `black` for formatting
- `flake8` for linting
- `mypy` for type checking
- `pytest` for testing

### Testing Requirements ✅

**Coverage Targets:**

- Unit test coverage: >90%
- Integration tests for all API endpoints
- E2E tests for critical user flows
- Performance benchmarks for key operations
- Security testing with OWASP ZAP

**Test Structure:**

```typescript
// Jest example
describe('DocumentProcessor', () => {
  describe('processDocument', () => {
    it('should process PDF documents correctly', async () => {
      // Arrange
      const filePath = 'test.pdf';
      const processor = new DocumentProcessor();

      // Act
      const result = await processor.process(filePath);

      // Assert
      expect(result.type).toBe('pdf');
      expect(result.content).toBeDefined();
    });
  });
});
```

```python
# Pytest example
class TestDocumentProcessor:
    def test_process_pdf_document(self):
        # Arrange
        file_path = "test.pdf"
        processor = DocumentProcessor()

        # Act
        result = processor.process(file_path)

        # Assert
        assert result.type == "pdf"
        assert result.content is not None
```

### Git Workflow 📝

**Branch Naming:**

- Features: `feature/short-description`
- Bug fixes: `fix/short-description`
- Documentation: `docs/short-description`
- Refactoring: `refactor/short-description`

**Commit Messages:**
Use Conventional Commits format:

```
feat: add document processor for DOCX files
fix: resolve memory leak in vector search
docs: update API documentation
test: add unit tests for search service
refactor: simplify embedding generation logic
```

**Pull Request Process:**

1. Create feature branch from `main`
2. Write code and tests
3. Ensure all tests pass
4. Run linters and formatters
5. Create PR with description
6. Require 1 approval before merge
7. Squash and merge to main

---

## 🐳 DOCKER GUIDELINES

### Container Best Practices

**Dockerfile Standards:**

```dockerfile
# Multi-stage build for smaller images
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodejs -u 1001
USER nodejs
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
  CMD node healthcheck.js
CMD ["node", "dist/index.js"]
```

**Requirements:**

- Multi-stage builds to minimize image size
- Run as non-root user
- Health checks for all services
- Resource limits defined
- Secrets via environment variables or Docker secrets
- `.dockerignore` to exclude unnecessary files

### Development vs Production

**Development:**

- Hot reloading enabled
- Debug logging active
- Exposed ports for debugging
- Volume mounts for code
- Additional dev tools installed

**Production:**

- Optimized builds
- Minimal logging
- Security hardened
- No debug tools
- Read-only file systems where possible

---

## 🔒 SECURITY REQUIREMENTS

### Code Security ⚠️

**NEVER:**

- Hardcode secrets, API keys, or passwords
- Commit `.env` files with real credentials
- Use `eval()` or similar dangerous functions
- Trust user input without validation
- Store passwords in plain text

**ALWAYS:**

- Validate and sanitize ALL user inputs
- Use parameterized queries (SQL injection prevention)
- Implement XSS protection in frontend
- Use CSRF tokens for state-changing operations
- Implement rate limiting on all endpoints
- Use secure random number generation
- Hash passwords with bcrypt/argon2 (cost factor ≥12)

**Example:**

```typescript
// Good: Input validation
import Joi from 'joi';

const schema = Joi.object({
  email: Joi.string().email().required(),
  name: Joi.string().min(3).max(100).required(),
});

const { error, value } = schema.validate(req.body);
if (error) {
  return res.status(400).json({ error: error.details });
}
```

### Dependency Management 📦

**Requirements:**

- Automated security scanning (Dependabot)
- Regular dependency updates (weekly)
- Pin exact versions in production
- Audit npm/pip packages before adding
- Remove unused dependencies
- Use `npm audit` and `safety check` regularly

### Data Security 🔐

**Implementation:**

- Encryption at rest for sensitive data (AES-256)
- TLS 1.3 for all network communication
- Secure session management (httpOnly, secure cookies)
- No sensitive data in logs or error messages
- Implement proper authentication and authorization
- Use environment variables for configuration

---

## 📊 MONITORING & LOGGING

### Logging Standards 📝

**Format:**

```json
{
  "timestamp": "2025-10-04T12:34:56.789Z",
  "level": "INFO",
  "service": "document-processor",
  "requestId": "uuid-here",
  "message": "Document processed successfully",
  "metadata": {
    "documentId": "doc123",
    "processingTime": 1234
  }
}
```

**Log Levels:**

- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARN`: Warning messages for potential issues
- `ERROR`: Error events that might still allow operation
- `CRITICAL`: Critical errors requiring immediate attention

**Rules:**

- Use structured logging (JSON format)
- Include request IDs for tracing
- NO sensitive data in logs (no passwords, API keys, PII)
- Log rotation and retention policies (7 days dev, 30 days prod)
- Appropriate log levels

### Metrics Collection 📈

**Prometheus Metrics:**

```typescript
// Example metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
});

const documentsProcessed = new promClient.Counter({
  name: 'documents_processed_total',
  help: 'Total number of documents processed',
  labelNames: ['type', 'status'],
});
```

**Track:**

- Request/response times
- Error rates
- Resource utilization (CPU, memory, disk)
- AI operation latency
- Document processing throughput
- Cache hit rates

---

## 🧪 TESTING STRATEGY

### Unit Tests ✅

**Coverage Requirements:**

- > 90% line coverage
- > 85% branch coverage
- All public APIs tested
- Edge cases and error handling tested
- Fast execution (<10 seconds total)

**Tools:**

- Jest for JavaScript/TypeScript
- Pytest for Python
- Mock external dependencies
- Use test fixtures for data

### Integration Tests 🔗

**Scope:**

- Service-to-service communication
- Database integration testing
- API contract testing (Pact)
- Docker Compose test environments
- Test all API endpoints

### E2E Tests 🎭

**Tools:**

- Playwright for UI testing
- Test critical user journeys
- Cross-browser testing (Chromium, Firefox, WebKit)
- Accessibility testing (WCAG 2.1 AA)
- Visual regression testing

**Critical Flows:**

1. User indexes documents
2. User searches for content
3. User asks AI questions
4. User exports results

### Performance Tests ⚡

**Tools:**

- k6 for load testing
- Memory profiling tools
- Stress testing for limits

**Benchmarks:**

- 1000 concurrent users
- 10,000 documents indexed
- <200ms p95 query latency
- No memory leaks after 24h operation

---

## 🚀 DEPLOYMENT PROCESS

### Development Environment 💻

**Setup:**

```bash
# Use Docker Compose
docker-compose -f infrastructure/docker/docker-compose.dev.yml up
```

**Features:**

- Hot reloading enabled
- Debug mode active
- Test databases
- Verbose logging

### Staging Environment 🧪

**Configuration:**

- Kubernetes deployment
- Production-like configuration
- Smoke tests before release
- Performance benchmarks
- Security scanning

### Production Environment 🌐

**Strategy:**

- Blue-green deployment
- Automated rollback on errors
- Canary releases for major changes
- Zero-downtime updates
- Health checks and monitoring

**Deployment Checklist:**

- [ ] All tests passing
- [ ] Security scan completed
- [ ] Performance benchmarks met
- [ ] Documentation updated
- [ ] Backup created
- [ ] Rollback plan ready

---

## 📚 DOCUMENTATION REQUIREMENTS

### Code Documentation 📝

**Required:**

- JSDoc/docstrings for all public APIs
- README.md in each service directory
- Architecture Decision Records (ADRs) for major decisions
- API documentation with OpenAPI/Swagger
- Inline comments for complex logic

### User Documentation 👤

**Required:**

- Getting started guide
- Feature documentation with screenshots
- Troubleshooting guide
- FAQ section
- Video tutorials (optional)

---

## ⚠️ LEGAL & COMPLIANCE

### Media Resources 📁

**ALLOWED:**

- Legitimate open-source resources
- Integration with legal APIs (Archive.org, Wikimedia Commons)
- Public domain content
- Creative Commons licensed content
- User's own files

**FORBIDDEN:**

- Scraping copyrighted content
- Bypassing paywalls
- Storing pirated materials
- Redistributing copyrighted works without permission
- Ignoring DMCA takedown requests

### Intellectual Property 📄

**Project IP:**

- All code is MIT licensed
- Document patentable innovations
- Trademark registration for "In My Head" brand
- Copyright notices in all files

**Patentable Areas:**

1. Adaptive context window management system
2. Hybrid vector-graph search algorithm
3. Resource correlation prediction engine
4. Multi-modal embedding fusion technique

### Privacy Compliance 🔐

**Requirements:**

- GDPR-ready architecture (if applicable)
- CCPA compliance for California users
- Clear privacy policy
- User consent mechanisms
- Data retention policies
- Right to deletion (data portability)

---

## 🎨 UI/UX GUIDELINES

### Design Principles 🎯

1. **Privacy-First**: Make privacy features obvious and accessible
2. **Simplicity**: One-click operations where possible
3. **Speed**: Instant feedback for all actions
4. **Accessibility**: WCAG 2.1 AA compliance
5. **Consistency**: Uniform design language throughout

### Visual Standards 🎨

**Colors:**

- Primary: #6366F1 (Indigo)
- Secondary: #8B5CF6 (Purple)
- Success: #10B981 (Green)
- Warning: #F59E0B (Amber)
- Error: #EF4444 (Red)
- Dark mode: Default

**Typography:**

- Headings: Inter
- Body: Inter
- Code: JetBrains Mono

### Components 🧩

**Use:**

- shadcn/ui components
- Radix UI primitives
- TailwindCSS for styling
- Lucide icons

### Performance 🚀

**Targets:**

- First Contentful Paint <1s
- Time to Interactive <3s
- Lazy loading for heavy components
- Optimistic UI updates
- Skeleton loaders during data fetch

---

## 🔧 DEVELOPMENT WORKFLOW

### Daily Development Process 📅

1. **Morning**: Pull latest from main branch
2. **Create**: Feature branch for your work
3. **TDD**: Write tests first (Test-Driven Development encouraged)
4. **Implement**: Write code to pass tests
5. **Test**: Run full test suite locally
6. **Commit**: With conventional commit message
7. **PR**: Create pull request with description
8. **Review**: Address feedback
9. **Merge**: After approval and passing CI/CD

### Code Review Checklist ✅

**Before Submitting PR:**

- [ ] Tests written and passing
- [ ] Documentation updated
- [ ] No console.log statements
- [ ] Performance considered
- [ ] Security reviewed
- [ ] Accessibility checked
- [ ] Linter passing
- [ ] Build successful

**During Review:**

- [ ] Code is readable and maintainable
- [ ] Follows project conventions
- [ ] No code duplication
- [ ] Error handling implemented
- [ ] Edge cases considered

---

## 🐛 DEBUGGING GUIDELINES

### Common Issues 🔍

**Vector Database Connection:**

```bash
# Check Qdrant service
docker-compose ps qdrant
docker-compose logs qdrant
```

**Slow Queries:**

```typescript
// Add query profiling
console.time('query');
const result = await searchService.query(prompt);
console.timeEnd('query');
```

**Memory Leaks:**

```bash
# Use Node.js profiler
node --inspect dist/index.js
# Then open chrome://inspect
```

**AI Timeouts:**

```python
# Implement proper error handling
try:
    result = await ai_engine.generate(prompt, timeout=30)
except TimeoutError:
    # Fallback logic
    result = cached_result
```

### Debug Tools 🛠️

- **Frontend**: Chrome DevTools, React DevTools
- **Backend**: Python debugger (pdb), Node.js inspector
- **Docker**: `docker-compose logs`, `docker exec -it`
- **Database**: pgAdmin, RedisInsight
- **Monitoring**: Prometheus, Grafana

---

## 📈 PERFORMANCE TARGETS

### Hard Requirements ⚡

- **Document Indexing**: >1000 docs/minute
- **Query Response**: <200ms (p95)
- **Memory Usage**: <500MB idle, <2GB active
- **CPU Usage**: <10% idle, <80% active
- **Startup Time**: <5 seconds
- **Concurrent Users**: Support 100+ simultaneous users

### Optimization Strategies 🎯

1. **Caching**: Redis for frequent queries
2. **Lazy Loading**: Load data only when needed
3. **Batch Processing**: Process multiple items together
4. **Connection Pooling**: Reuse database connections
5. **Indexing**: Proper database indices
6. **Compression**: Gzip responses
7. **CDN**: Static assets via CDN (future)

---

## 🌟 INNOVATION AREAS

### Patent-Worthy Ideas 💡

1. **Adaptive Context Window Management**
   - Novel approach to maintaining conversation context
   - Automatic relevance scoring and pruning
2. **Hybrid Vector-Graph Search**

   - Combining semantic search with knowledge graph traversal
   - Multi-hop reasoning across documents

3. **Resource Correlation Prediction**

   - ML-based prediction of document relationships
   - Usage pattern analysis

4. **Multi-Modal Embedding Fusion**
   - Unified embeddings across text, audio, video, images
   - Cross-modal search capabilities

### Research Topics 🔬

- Zero-shot document classification
- Automatic knowledge graph construction
- Federated learning for privacy
- Quantum-resistant encryption
- Neural architecture search for optimal embedding models

---

## 📞 SUPPORT & COMMUNICATION

### Getting Help 💬

1. **Documentation**: Check docs/ folder first
2. **Stack Overflow**: Search for similar issues
3. **GitHub Discussions**: For architecture questions
4. **Discord**: Real-time help from community
5. **Email**: support@inmyhead.ai for urgent issues

### Reporting Issues 🐛

**Issue Template:**

```markdown
## Description

[Clear description of the issue]

## Steps to Reproduce

1. Step 1
2. Step 2
3. Step 3

## Expected Behavior

[What should happen]

## Actual Behavior

[What actually happens]

## Environment

- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Node.js: [version]
- Python: [version]
- Docker: [version]

## Logs

[Relevant logs or error messages]

## Screenshots

[If applicable]
```

---

## 🎯 SUCCESS METRICS

### Technical Metrics 📊

- **Test Coverage**: >90%
- **Build Time**: <5 minutes
- **Deployment Frequency**: Daily to staging, weekly to prod
- **Mean Time to Recovery**: <1 hour
- **Error Rate**: <0.1%
- **Uptime**: 99.9%

### User Metrics 👥

- **Query Accuracy**: >95%
- **User Satisfaction**: >4.5/5
- **Feature Adoption**: >80% of users use key features
- **Performance Consistency**: <5% variance in response times
- **Retention**: >70% monthly active users

### Innovation Metrics 💡

- **Patent Applications**: 3+ filed
- **Research Papers**: 1+ published
- **Open Source Contributions**: Active community
- **Plugin Ecosystem**: 10+ community plugins

---

## 🎓 LEARNING RESOURCES

### Recommended Reading 📚

- **Architecture**: "Designing Data-Intensive Applications" by Martin Kleppmann
- **AI/ML**: "Hands-On Machine Learning" by Aurélien Géron
- **Docker**: "Docker Deep Dive" by Nigel Poulton
- **TypeScript**: Official TypeScript Handbook
- **Python**: "Fluent Python" by Luciano Ramalho

### Courses 🎥

- FastAPI official tutorial
- React + TypeScript by Matt Pocock
- Kubernetes for Developers
- Vector Databases and Embeddings

---

## 🚀 FINAL NOTES

**Remember:**

- We're building the future of personal knowledge management
- Privacy is non-negotiable
- Performance matters - users notice lag
- Every line of code should reflect our commitment to quality
- Test everything thoroughly
- Document your work
- Ask questions when uncertain
- Celebrate small wins!

**Project Motto:**
**"Your Knowledge, Infinitely Connected, Eternally Private, Boundlessly Intelligent"**

---

**Last Updated**: October 4, 2025  
**Version**: 1.0.0  
**Status**: Active Development 🚧
