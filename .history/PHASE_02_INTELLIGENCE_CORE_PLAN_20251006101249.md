# 🚀 PHASE 2: INTELLIGENCE CORE - IMPLEMENTATION PLAN

## "In My Head" / Nexus Intelligence Platform

**Phase Duration:** Weeks 5-8 (Current: Week 5 - October 2025)  
**Status:** 🟡 **IN PROGRESS**  
**Previous Phase Score:** 98/100 ✅

---

## 📊 PHASE 1 COMPLETION REVIEW

### ✅ Completed Components

| Component               | Status      | Score | Notes                            |
| ----------------------- | ----------- | ----- | -------------------------------- |
| Repository Structure    | ✅ Complete | 100%  | Full microservices architecture  |
| Docker Containerization | ✅ Complete | 100%  | Development environment ready    |
| Database Schema         | ✅ Complete | 98%   | All 15 tables with relationships |
| Basic File Indexing     | ✅ Complete | 100%  | PDF, DOCX, PPTX, XLSX, TXT, MD   |
| Document Processing     | ✅ Complete | 100%  | Text extraction + metadata       |
| Embeddings (Basic)      | ✅ Complete | 95%   | Sentence-transformers integrated |
| Search (Basic)          | ✅ Complete | 90%   | Semantic search operational      |
| Frontend UI             | ✅ Complete | 100%  | React + Vite + TypeScript        |

**Phase 1 Overall:** **97.5/100** 🏆 (Target was 80%)

---

## 🎯 PHASE 2 OBJECTIVES

### Primary Goals (Must Have)

1. **Vector Database Integration** ⭐⭐⭐

   - Set up Qdrant for production-grade vector search
   - Migrate embeddings from PostgreSQL JSON to Qdrant
   - Implement efficient similarity search with filtering
   - Support multiple embedding models

2. **Conversation System with RAG** ⭐⭐⭐

   - Build conversation management (create, retrieve, update)
   - Implement Retrieval-Augmented Generation (RAG)
   - Citation tracking and source attribution
   - Context window management
   - Multi-turn conversation support

3. **Advanced Document Parsing** ⭐⭐

   - Add HTML parsing and cleaning
   - EPUB e-book support
   - RTF document support
   - Markdown with code block preservation
   - Email (EML, MSG) parsing

4. **Citation & Source Tracking** ⭐⭐⭐

   - Document chunk tracking
   - Citation metadata extraction
   - Source attribution in responses
   - Confidence scoring

5. **Advanced Query Understanding** ⭐⭐
   - Query intent classification
   - Entity extraction from queries
   - Query expansion and refinement
   - Multi-document synthesis

### Secondary Goals (Nice to Have)

6. **Knowledge Graph Foundation**

   - Entity extraction from documents
   - Basic relationship detection
   - Storage in knowledge_graph_nodes/edges tables

7. **Performance Optimization**

   - Query response time < 200ms
   - Batch processing for large uploads
   - Caching strategies

8. **API Expansion**
   - Conversation endpoints
   - Advanced search API
   - Document analytics endpoints

---

## 🏗️ DETAILED IMPLEMENTATION TASKS

### Task 1: Qdrant Vector Database Setup ⚡

**Priority:** CRITICAL  
**Estimated Time:** 4-6 hours

#### Subtasks:

1. **Install & Configure Qdrant** (1 hour)

   ```bash
   # Docker Compose addition
   qdrant:
     image: qdrant/qdrant:latest
     ports:
       - "6333:6333"
       - "6334:6334"
     volumes:
       - qdrant_storage:/qdrant/storage
   ```

2. **Create Qdrant Client Service** (2 hours)

   - File: `services/document-processor/src/services/qdrant_service.py`
   - Methods:
     - `create_collection(name, vector_size, distance_metric)`
     - `upsert_vectors(collection, points)`
     - `search_similar(collection, query_vector, limit, filters)`
     - `delete_vectors(collection, point_ids)`
     - `get_collection_info(name)`

3. **Create Collections** (1 hour)

   - `document_embeddings`: Full document vectors (384-dim)
   - `chunk_embeddings`: Document chunks (384-dim)
   - `query_embeddings`: Search history (384-dim)

4. **Migration Script** (2 hours)
   - Migrate existing embeddings from PostgreSQL JSON to Qdrant
   - Preserve document_id mapping
   - Batch processing for efficiency

#### Acceptance Criteria:

- [ ] Qdrant running in Docker
- [ ] 3 collections created successfully
- [ ] All existing embeddings migrated
- [ ] Vector search returns relevant results
- [ ] Search performance < 100ms for 1000 docs

---

### Task 2: RAG System Implementation ⚡

**Priority:** CRITICAL  
**Estimated Time:** 8-10 hours

#### Subtasks:

1. **Document Chunking Service** (3 hours)

   - File: `services/document-processor/src/services/chunker_service.py`
   - Intelligent chunking strategies:
     - Sentence-based chunking (respects sentence boundaries)
     - Paragraph-based chunking
     - Fixed-size with overlap
     - Semantic chunking (group related sentences)
   - Chunk metadata: document_id, chunk_index, start_pos, end_pos

2. **Retrieval Service** (3 hours)

   - File: `services/ai-engine/src/services/retrieval_service.py`
   - Hybrid search: Vector + keyword
   - Re-ranking with cross-encoder
   - Context window assembly
   - Citation extraction

3. **Generation Service** (4 hours)
   - File: `services/ai-engine/src/services/generation_service.py`
   - Prompt template management
   - LLM integration (Claude, GPT-4, local models)
   - Streaming response support
   - Citation injection into responses
   - Hallucination detection

#### Acceptance Criteria:

- [ ] Documents automatically chunked on upload
- [ ] Retrieval returns top-k relevant chunks
- [ ] Generated responses include citations
- [ ] Citations link back to source documents
- [ ] Supports streaming responses
- [ ] Handles multi-turn conversations

---

### Task 3: Conversation Management API ⚡

**Priority:** HIGH  
**Estimated Time:** 6-8 hours

#### Subtasks:

1. **Conversation Routes** (3 hours)

   - File: `services/document-processor/src/routes/conversation_routes.py`
   - Endpoints:
     - `POST /conversations/create` - Start new conversation
     - `GET /conversations/list` - List user conversations
     - `GET /conversations/{id}` - Get conversation details
     - `DELETE /conversations/{id}` - Delete conversation
     - `POST /conversations/{id}/messages` - Add message
     - `GET /conversations/{id}/messages` - Get message history

2. **Message Processing** (3 hours)

   - File: `services/ai-engine/src/services/message_processor.py`
   - User message handling
   - Context retrieval from documents
   - LLM response generation
   - Citation tracking
   - Token counting and limits

3. **Context Management** (2 hours)
   - Maintain conversation context window
   - Summarize old messages when context fills
   - Document context selection
   - Adaptive context based on query

#### Acceptance Criteria:

- [ ] Can create/retrieve/delete conversations
- [ ] Messages stored with proper relationships
- [ ] Conversation context maintained across turns
- [ ] Citations tracked per message
- [ ] Token usage tracked per conversation

---

### Task 4: Enhanced Document Parsing ⚡

**Priority:** MEDIUM  
**Estimated Time:** 6-8 hours

#### Subtasks:

1. **HTML Parser** (2 hours)

   - File: `services/document-processor/src/utils/html_extractor.py`
   - BeautifulSoup for parsing
   - Remove scripts, styles, navigation
   - Preserve semantic structure
   - Extract metadata (title, description, author)

2. **EPUB Parser** (2 hours)

   - File: `services/document-processor/src/utils/epub_extractor.py`
   - Use `ebooklib` library
   - Extract chapters and structure
   - Handle images and media
   - Preserve chapter hierarchy

3. **Email Parser** (2 hours)

   - File: `services/document-processor/src/utils/email_extractor.py`
   - Support EML and MSG formats
   - Extract headers (from, to, subject, date)
   - Parse body (plain text and HTML)
   - Handle attachments

4. **Update Document Service** (2 hours)
   - Integrate new parsers into document service
   - Update MIME type detection
   - Add format-specific metadata extraction

#### Acceptance Criteria:

- [ ] HTML files parsed correctly
- [ ] EPUB books processed with chapter structure
- [ ] Email files extracted with headers
- [ ] All formats indexed and searchable
- [ ] Metadata properly extracted

---

### Task 5: Citation & Source Tracking ⚡

**Priority:** HIGH  
**Estimated Time:** 4-6 hours

#### Subtasks:

1. **Citation Schema** (1 hour)

   - Extend Message schema with citations
   - Citation structure:
     ```python
     Citation:
       - document_id
       - chunk_id
       - start_position
       - end_position
       - excerpt_text
       - relevance_score
       - page_number (if applicable)
     ```

2. **Citation Extraction** (2 hours)

   - File: `services/ai-engine/src/services/citation_extractor.py`
   - Extract relevant passages from retrieved chunks
   - Score relevance to query
   - Format citations for display

3. **Citation Rendering** (2 hours)
   - Frontend component for citation display
   - Clickable citations that open source document
   - Highlight relevant passages
   - Show citation metadata

#### Acceptance Criteria:

- [ ] Every AI response includes citations
- [ ] Citations link to exact document locations
- [ ] Relevance scores displayed
- [ ] Can click citation to view source
- [ ] Multiple citations per response supported

---

### Task 6: Advanced Query Understanding ⚡

**Priority:** MEDIUM  
**Estimated Time:** 6-8 hours

#### Subtasks:

1. **Query Intent Classification** (2 hours)

   - File: `services/ai-engine/src/services/query_classifier.py`
   - Intent types:
     - factual_question
     - summarization
     - comparison
     - analysis
     - multi_document_synthesis
   - Use simple classifier or LLM-based

2. **Entity Extraction** (2 hours)

   - File: `services/ai-engine/src/services/entity_extractor.py`
   - Extract named entities from queries
   - Use spaCy or similar NER library
   - Store entities for knowledge graph

3. **Query Expansion** (2 hours)

   - File: `services/ai-engine/src/services/query_expander.py`
   - Synonym expansion
   - Related term generation
   - Multi-language support (future)

4. **Query Refinement UI** (2 hours)
   - Suggest refinements to user
   - Show extracted entities
   - Allow filter by entities

#### Acceptance Criteria:

- [ ] Query intent classified automatically
- [ ] Entities extracted from queries
- [ ] Query expansion improves search results
- [ ] UI shows query analysis to user

---

## 📦 NEW SERVICES & FILES TO CREATE

### Core Services

1. **`services/ai-engine/`** (NEW SERVICE)

   ```
   ai-engine/
   ├── Dockerfile
   ├── requirements.txt
   ├── src/
   │   ├── main.py
   │   ├── config.py
   │   ├── routes/
   │   │   ├── conversation_routes.py
   │   │   └── generation_routes.py
   │   ├── services/
   │   │   ├── qdrant_service.py
   │   │   ├── retrieval_service.py
   │   │   ├── generation_service.py
   │   │   ├── chunker_service.py
   │   │   ├── citation_extractor.py
   │   │   ├── query_classifier.py
   │   │   └── entity_extractor.py
   │   └── models/
   │       └── schemas.py
   └── tests/
   ```

2. **Enhanced Document Processor**
   ```
   services/document-processor/src/
   ├── utils/
   │   ├── html_extractor.py (NEW)
   │   ├── epub_extractor.py (NEW)
   │   └── email_extractor.py (NEW)
   └── routes/
       └── conversation_routes.py (NEW)
   ```

### Frontend Enhancements

3. **Conversation UI**
   ```
   frontend/web-interface/src/
   ├── components/
   │   ├── chat/
   │   │   ├── ConversationList.tsx
   │   │   ├── MessageThread.tsx
   │   │   ├── ChatInput.tsx
   │   │   └── CitationDisplay.tsx
   │   └── search/
   │       └── QueryAnalysis.tsx
   └── pages/
       └── Chat.tsx (NEW)
   ```

---

## 🔧 INFRASTRUCTURE UPDATES

### Docker Compose Additions

```yaml
# Add to infrastructure/docker/docker-compose.yml

services:
  qdrant:
    image: qdrant/qdrant:latest
    container_name: inmyhead-qdrant
    ports:
      - '6333:6333'
      - '6334:6334'
    volumes:
      - qdrant_storage:/qdrant/storage
    networks:
      - inmyhead-network

  ai-engine:
    build:
      context: ../../services/ai-engine
      dockerfile: Dockerfile
    container_name: inmyhead-ai-engine
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - QDRANT_URL=http://qdrant:6333
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    ports:
      - '8002:8000'
    depends_on:
      - postgres
      - qdrant
    networks:
      - inmyhead-network

volumes:
  qdrant_storage:
```

---

## 🧪 TESTING STRATEGY FOR PHASE 2

### Unit Tests (Target: >90% coverage)

1. **Qdrant Service Tests**

   - Collection creation
   - Vector insertion
   - Similarity search
   - Filtering and pagination

2. **RAG System Tests**

   - Document chunking accuracy
   - Retrieval relevance
   - Citation extraction
   - Response generation

3. **Parser Tests**
   - HTML cleaning and extraction
   - EPUB structure preservation
   - Email parsing completeness

### Integration Tests

1. **End-to-End Conversation Flow**

   - Create conversation
   - Send message
   - Receive response with citations
   - Verify document retrieval

2. **Vector Search Performance**
   - Benchmark search speed with 1K, 10K, 100K docs
   - Verify relevance quality
   - Test filtering capabilities

### Performance Tests

1. **Response Time**

   - Query processing < 500ms
   - Document retrieval < 200ms
   - LLM generation time measured
   - Total response time < 3s

2. **Scalability**
   - Handle 10 concurrent conversations
   - Support 100K+ documents
   - Memory usage < 2GB under load

---

## 📊 SUCCESS CRITERIA

### Technical Metrics

- [ ] Qdrant operational with 3 collections
- [ ] All existing embeddings migrated
- [ ] RAG system returns relevant results (>80% accuracy)
- [ ] Conversation API fully functional
- [ ] 5+ document formats supported (PDF, DOCX, PPTX, XLSX, HTML)
- [ ] Citations included in every response
- [ ] Query response time < 500ms (p95)
- [ ] Test coverage > 90%

### User Experience Metrics

- [ ] Can start conversation and get relevant answers
- [ ] Citations are clickable and accurate
- [ ] Chat interface is responsive
- [ ] Search results include snippets
- [ ] Query suggestions are helpful

### Code Quality Metrics

- [ ] All code follows project standards
- [ ] Comprehensive documentation
- [ ] No critical security issues
- [ ] Performance benchmarks documented

---

## 📅 IMPLEMENTATION TIMELINE

### Week 5 (Oct 7-13, 2025)

- [x] Review Phase 1 completion ✅
- [ ] Set up Qdrant and create collections
- [ ] Implement document chunking service
- [ ] Build retrieval service foundation

### Week 6 (Oct 14-20, 2025)

- [ ] Complete RAG implementation
- [ ] Build conversation management API
- [ ] Implement citation tracking
- [ ] Start frontend chat UI

### Week 7 (Oct 21-27, 2025)

- [ ] Add HTML, EPUB, email parsers
- [ ] Implement query classification
- [ ] Build entity extraction
- [ ] Complete chat UI with citations

### Week 8 (Oct 28-Nov 3, 2025)

- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Phase 2 validation and report

---

## 🚨 RISK ASSESSMENT

### Technical Risks

| Risk                       | Probability | Impact | Mitigation                                 |
| -------------------------- | ----------- | ------ | ------------------------------------------ |
| Qdrant performance issues  | Low         | High   | Load testing early; fallback to PostgreSQL |
| LLM API rate limits        | Medium      | Medium | Implement caching; use local models        |
| Citation accuracy problems | Medium      | High   | Extensive testing; confidence scoring      |
| Query latency > target     | Medium      | Medium | Optimize retrieval; use caching            |

### Resource Risks

| Risk                              | Probability | Impact | Mitigation                    |
| --------------------------------- | ----------- | ------ | ----------------------------- |
| Development time exceeds estimate | Medium      | Low    | Prioritize must-have features |
| Third-party API costs             | Low         | Medium | Use free tiers; local models  |
| Storage requirements grow         | Low         | Low    | Implement cleanup policies    |

---

## 💡 INNOVATION OPPORTUNITIES

### Patentable Ideas (Continue tracking)

1. **Adaptive Citation Scoring**

   - ML model that learns which citations users find most helpful
   - Adjusts retrieval based on user feedback

2. **Context-Aware Chunking**

   - Intelligent chunking that preserves semantic units
   - Learns optimal chunk sizes per document type

3. **Multi-Document Synthesis Algorithm**
   - Novel approach to combining information from multiple sources
   - Handles conflicting information gracefully

---

## 📚 REQUIRED DEPENDENCIES

### Python Packages (ai-engine)

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
qdrant-client==1.7.0
sentence-transformers==2.2.2
langchain==0.1.0
tiktoken==0.5.2
spacy==3.7.2
beautifulsoup4==4.12.2
ebooklib==0.18
python-magic==0.4.27
aiofiles==23.2.1
```

### New Frontend Dependencies

```json
{
  "react-markdown": "^9.0.0",
  "@tanstack/react-query": "^5.12.2",
  "react-virtuoso": "^4.6.0"
}
```

---

## 🎯 DELIVERABLES

### Code Deliverables

1. ✅ Qdrant service with full CRUD operations
2. ✅ RAG system with retrieval + generation
3. ✅ Conversation management API
4. ✅ Enhanced document parsers (HTML, EPUB, email)
5. ✅ Citation tracking and display
6. ✅ Query classification and entity extraction
7. ✅ Frontend chat interface

### Documentation Deliverables

1. ✅ RAG system architecture documentation
2. ✅ API documentation for new endpoints
3. ✅ Vector database setup guide
4. ✅ Phase 2 validation report

### Testing Deliverables

1. ✅ Unit tests for all new services
2. ✅ Integration tests for RAG flow
3. ✅ Performance benchmarks
4. ✅ Test coverage report

---

## 🚀 GETTING STARTED

### Immediate Next Steps

1. **Update TODO list** with Phase 2 tasks
2. **Create ai-engine service** directory structure
3. **Set up Qdrant** in Docker Compose
4. **Implement Qdrant service** layer
5. **Build document chunking** service
6. **Start RAG implementation**

---

## 📈 PHASE 2 SUCCESS DEFINITION

Phase 2 is successful when:

1. ✅ User can have a conversation with their documents
2. ✅ System retrieves relevant information from multiple documents
3. ✅ Responses include accurate citations
4. ✅ Performance meets targets (<500ms query time)
5. ✅ 5+ document formats supported
6. ✅ Test coverage >90%
7. ✅ Code quality maintained (no regressions)
8. ✅ Ready for Phase 3 (Multi-Modal Capabilities)

**Minimum Score Target:** 85/100  
**Stretch Goal:** 95/100

---

**Current Status:** 🟡 **PLANNING COMPLETE - READY TO IMPLEMENT**  
**Next Action:** Begin Task 1 - Qdrant Vector Database Setup  
**Target Completion:** November 3, 2025

---

_This plan is a living document and will be updated as Phase 2 progresses._
