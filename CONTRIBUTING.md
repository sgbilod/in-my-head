# Contributing to In My Head

Thank you for considering contributing to "In My Head"! This document provides guidelines and instructions for contributing to the project.

## 🎯 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together towards common goals
- **Be inclusive**: Welcome diverse perspectives and experiences
- **Be constructive**: Provide helpful feedback
- **Be patient**: Remember that everyone was a beginner once

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- Git installed
- Docker and Docker Compose
- Node.js 18+ and npm
- Python 3.11+ and pip
- A GitHub account
- Basic understanding of TypeScript and Python

### Setting Up Your Development Environment

1. **Fork the repository** on GitHub

2. **Clone your fork**:

   ```bash
   git clone https://github.com/YOUR_USERNAME/in-my-head.git
   cd in-my-head
   ```

3. **Add upstream remote**:

   ```bash
   git remote add upstream https://github.com/ORIGINAL_OWNER/in-my-head.git
   ```

4. **Install dependencies**:

   ```bash
   # Install Node.js dependencies
   cd services/api-gateway && npm install && cd ../..

   # Install Python dependencies
   cd services/document-processor && pip install -r requirements.txt && cd ../..
   cd services/ai-engine && pip install -r requirements.txt && cd ../..
   cd services/search-service && pip install -r requirements.txt && cd ../..
   cd services/resource-manager && pip install -r requirements.txt && cd ../..
   ```

5. **Start development environment**:
   ```bash
   docker-compose -f infrastructure/docker/docker-compose.dev.yml up
   ```

## 📋 How to Contribute

### Reporting Bugs 🐛

Before creating a bug report, please check:

1. **Search existing issues** to avoid duplicates
2. **Verify it's reproducible** in the latest version
3. **Gather information** about your environment

**When creating a bug report, include**:

- Clear, descriptive title
- Steps to reproduce
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Environment details (OS, versions, etc.)
- Relevant logs or error messages

**Use the bug report template**:

```markdown
## Description

[Clear description of the bug]

## Steps to Reproduce

1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior

[What should happen]

## Actual Behavior

[What actually happens]

## Environment

- OS: [e.g., Windows 11, macOS 14]
- Node.js: [version]
- Python: [version]
- Docker: [version]

## Additional Context

[Any other relevant information]
```

### Suggesting Features 💡

We welcome feature suggestions! Before submitting:

1. **Check the roadmap** to see if it's already planned
2. **Search existing feature requests** to avoid duplicates
3. **Consider if it aligns** with project goals

**When suggesting a feature, include**:

- Clear, descriptive title
- Problem statement (what need does this address?)
- Proposed solution
- Alternative solutions considered
- Examples from other tools (if applicable)
- Mockups or diagrams (if UI-related)

### Contributing Code 🔧

#### 1. Choose or Create an Issue

- Browse [open issues](https://github.com/OWNER/in-my-head/issues)
- Look for issues labeled `good first issue` or `help wanted`
- Comment on the issue to indicate you're working on it
- Wait for maintainer approval before starting

#### 2. Create a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create a new branch
git checkout -b feature/your-feature-name
# Or for bug fixes
git checkout -b fix/bug-description
```

**Branch naming conventions**:

- Features: `feature/short-description`
- Bug fixes: `fix/short-description`
- Documentation: `docs/short-description`
- Refactoring: `refactor/short-description`
- Tests: `test/short-description`

#### 3. Make Your Changes

Follow our coding standards:

**TypeScript/JavaScript**:

- Use TypeScript for all code
- Follow ESLint and Prettier rules
- Write tests for new functionality
- Add JSDoc comments for public APIs
- Maximum function length: 50 lines

**Python**:

- Follow PEP 8 style guide
- Use type hints
- Format with Black (line length: 100)
- Add docstrings (Google style)
- Maximum function length: 50 lines

**General**:

- Write meaningful commit messages
- Keep commits atomic and focused
- Add tests for new features
- Update documentation as needed
- Ensure all tests pass

#### 4. Write Tests

All new code must include tests:

```bash
# Run tests for Node.js services
cd services/api-gateway
npm test

# Run tests for Python services
cd services/document-processor
pytest

# Run all tests
./scripts/run-tests.sh
```

**Test coverage requirements**:

- Unit tests: >90% coverage
- Integration tests for new features
- E2E tests for user-facing features

#### 5. Commit Your Changes

Use **Conventional Commits** format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

**Examples**:

```bash
git commit -m "feat(search): add semantic search support"
git commit -m "fix(api): resolve authentication token expiration"
git commit -m "docs(readme): update installation instructions"
git commit -m "test(processor): add tests for PDF parsing"
```

#### 6. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

#### 7. Create a Pull Request

1. Go to your fork on GitHub
2. Click "New Pull Request"
3. Fill out the PR template:

```markdown
## Description

[What does this PR do?]

## Related Issue

Closes #[issue number]

## Type of Change

- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## How Has This Been Tested?

[Describe the tests you ran]

## Checklist

- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

[Add screenshots to help explain your changes]
```

#### 8. Respond to Review Feedback

- Be responsive to reviewer comments
- Make requested changes promptly
- Push updates to your branch (they'll appear in the PR)
- Thank reviewers for their time
- Be patient and professional

## 📝 Style Guidelines

### Code Style

**TypeScript/JavaScript**:

```typescript
// Good: Clear, typed, documented
/**
 * Process a document and extract metadata.
 * @param filePath - Path to the document
 * @returns Processed document with metadata
 */
async function processDocument(filePath: string): Promise<Document> {
  const content = await readFile(filePath);
  return {
    id: generateId(),
    content,
    metadata: extractMetadata(content),
  };
}

// Bad: Untyped, unclear
async function process(f: any) {
  const c = await readFile(f);
  return { id: gen(), c, m: meta(c) };
}
```

**Python**:

```python
# Good: Typed, documented, clear
def process_document(file_path: str) -> Document:
    """
    Process a document and extract metadata.

    Args:
        file_path: Path to the document

    Returns:
        Processed document with metadata

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    with open(file_path, 'r') as f:
        content = f.read()

    return Document(
        id=generate_id(),
        content=content,
        metadata=extract_metadata(content)
    )

# Bad: No types, unclear
def process(f):
    c = open(f).read()
    return {'id': gen(), 'c': c, 'm': meta(c)}
```

### Documentation Style

- Use clear, concise language
- Include code examples
- Add diagrams for complex concepts
- Keep documentation up-to-date
- Use proper Markdown formatting

### Commit Message Style

```
# Good
feat(search): add vector search with Qdrant integration

- Implement semantic search using embeddings
- Add query optimization for large document sets
- Include caching for frequent queries

Closes #123

# Bad
added search stuff
```

## 🧪 Testing Guidelines

### Unit Tests

```typescript
// TypeScript example with Jest
describe('DocumentProcessor', () => {
  let processor: DocumentProcessor;

  beforeEach(() => {
    processor = new DocumentProcessor();
  });

  it('should process PDF documents', async () => {
    const result = await processor.process('test.pdf');

    expect(result.type).toBe('pdf');
    expect(result.content).toBeDefined();
    expect(result.metadata).toHaveProperty('pageCount');
  });

  it('should handle missing files gracefully', async () => {
    await expect(processor.process('missing.pdf')).rejects.toThrow('File not found');
  });
});
```

```python
# Python example with pytest
class TestDocumentProcessor:
    @pytest.fixture
    def processor(self):
        return DocumentProcessor()

    def test_process_pdf(self, processor):
        result = processor.process('test.pdf')

        assert result.type == 'pdf'
        assert result.content is not None
        assert 'page_count' in result.metadata

    def test_missing_file(self, processor):
        with pytest.raises(FileNotFoundError):
            processor.process('missing.pdf')
```

### Integration Tests

Test service interactions:

```python
@pytest.mark.integration
async def test_document_search_pipeline():
    # Index document
    doc_id = await document_processor.index('test.pdf')

    # Wait for indexing
    await asyncio.sleep(1)

    # Search for content
    results = await search_service.search('test query')

    assert len(results) > 0
    assert any(r.document_id == doc_id for r in results)
```

## 📚 Documentation Guidelines

### README Updates

- Keep README concise but comprehensive
- Update feature lists when adding features
- Update installation steps if changed
- Add screenshots for UI changes

### Code Comments

```typescript
// Good: Explains WHY, not WHAT
// Cache results for 5 minutes to reduce API calls and improve response time
const cacheResult = await cache.set(key, result, 300);

// Bad: States the obvious
// Set the cache
const cacheResult = await cache.set(key, result, 300);
```

### API Documentation

Use OpenAPI/Swagger for REST APIs:

```typescript
/**
 * @openapi
 * /api/documents:
 *   post:
 *     summary: Upload and process a document
 *     requestBody:
 *       required: true
 *       content:
 *         multipart/form-data:
 *           schema:
 *             type: object
 *             properties:
 *               file:
 *                 type: string
 *                 format: binary
 *     responses:
 *       200:
 *         description: Document processed successfully
 *       400:
 *         description: Invalid file format
 */
```

## 🔍 Review Process

### What We Look For

1. **Code Quality**:

   - Clean, readable code
   - Follows style guidelines
   - No unnecessary complexity
   - Proper error handling

2. **Testing**:

   - Tests are included
   - Tests are meaningful
   - Coverage requirements met
   - Edge cases considered

3. **Documentation**:

   - Code is well-commented
   - README updated if needed
   - API docs updated
   - Breaking changes noted

4. **Performance**:

   - No obvious performance issues
   - Efficient algorithms
   - Proper resource management
   - No memory leaks

5. **Security**:
   - No security vulnerabilities
   - Input validation implemented
   - No hardcoded secrets
   - Follows security best practices

### Review Timeline

- Initial review: Within 2-3 days
- Follow-up reviews: Within 1-2 days
- Merging: After approval and passing CI/CD

## 🎉 Recognition

We value all contributions! Contributors will be:

- Added to CONTRIBUTORS.md
- Mentioned in release notes
- Credited in documentation
- Thanked in our community channels

## 📞 Getting Help

Need help contributing? Reach out:

- **GitHub Discussions**: For questions and discussions
- **Discord**: Real-time help (link in README)
- **Email**: contribute@inmyhead.ai

## 🙏 Thank You!

Every contribution, no matter how small, helps make "In My Head" better. Thank you for being part of our community!

---

_Last Updated: October 4, 2025_
