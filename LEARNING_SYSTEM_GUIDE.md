# Learning-Enhanced RAG System Guide

## System Overview

The enhanced system combines **historical PR analysis** with **learning insights from model comparisons** to provide more intelligent and context-aware PR reviews.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Learning Data   │    │ Historical PRs   │    │ Current PR      │
│ (model comps)   │────│ (diff data)      │────│ Analysis        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Pinecone Vector Database                        │
│  ┌─────────────────┐         ┌─────────────────────────────┐   │
│  │ learning_insight│         │ pr_diff                     │   │
│  │ embeddings      │         │ embeddings                  │   │
│  └─────────────────┘         └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Enhanced Prompt Generation                    │
│                                                                 │
│  Similar Historical Changes + Learning Insights + Base Prompt  │
└─────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. **Data Sources**
- **`learning_data.json`**: Contains GPT-4 vs O3 model comparison results and extracted learning points
- **PR Diff Database**: Historical PR changes with summaries and metadata
- **Current PR**: The PR being analyzed

### 2. **Vector Storage (Pinecone)**
- **Learning Insights**: Stored with `document_type: "learning_insight"`
- **PR Diffs**: Stored with `document_type: "pr_diff"`
- **Semantic Search**: Both types searchable via embeddings

### 3. **Context Retrieval**
```python
# When analyzing a PR:
query = "Fix authentication bug in login system"

# System retrieves:
similar_prs = search(query, document_type="pr_diff")        # Historical similar changes
learning_insights = search(query, document_type="learning_insight")  # Relevant lessons learned

combined_context = RAGContext(similar_prs, learning_insights)
```

### 4. **Enhanced Prompt Generation**
```
## Similar Historical Changes (for reference):
### Similar Change #1 (similarity: 0.85)
**Title:** Fix auth bug in login
**Summary:** Updated JWT validation
**Files:** auth.py, login.js
**Language:** python

### Learning Insights from Previous Analysis:
• Reconsider recommendation criteria when models disagree
• Pay attention to variable naming consistency
• Check for security implications in auth changes

## Current Analysis:
[Your original prompt for current PR analysis]
```

## End-to-End Usage

### 1. **Setup & Initialization**

```python
from pr_agent.algo.rag_handler import RAGHandler

# Initialize with Pinecone (recommended for production)
rag = RAGHandler(vector_db_type="pinecone", learning_data_path="learning_data.json")

# Or use JSON for testing/development
rag = RAGHandler(vector_db_type="json", learning_data_path="learning_data.json")
```

### 2. **Populate Learning Insights (One-time setup)**

```python
# Load and store learning insights in vector database
success = rag.populate_learning_insights()
print(f"Learning insights populated: {success}")

# Check statistics
stats = rag.get_learning_insights_stats()
print(f"Stored {stats['total_learning_insights']} learning insights")
```

### 3. **Analyze a PR with Enhanced Context**

```python
# Get enhanced context for PR analysis
pr_query = f"Title: {pr_title}\nDescription: {pr_description}\nDiff: {diff_preview}"

context = rag.get_similar_contexts(
    query_text=pr_query,
    k=3,  # Number of similar PRs to retrieve
    language="python",  # Optional: filter by language
    include_learning=True  # Include learning insights
)

print(f"Found {len(context.similar_diffs)} similar PRs")
print(f"Found {len(context.learning_insights)} relevant learning insights")
```

### 4. **Generate Enhanced Prompt**

```python
base_prompt = "Review this PR for potential issues, security concerns, and code quality:"

enhanced_prompt = rag.enhance_prompt_with_context(
    base_prompt=base_prompt,
    context=context,
    max_context=3
)

# Use enhanced_prompt with your AI model
# The prompt now includes historical context + learning insights
```

### 5. **Integration with Evolutionary Reviewer**

```python
# In pr_evolutionary_reviewer.py
class PrEvolutionaryReviewer:
    def __init__(self):
        self.rag = RAGHandler("pinecone")
        self.rag.populate_learning_insights()  # Ensure insights are loaded
    
    def analyze_pr(self, pr_data):
        # Get enhanced context
        context = self.rag.get_similar_contexts(
            f"{pr_data.title} {pr_data.description}",
            include_learning=True
        )
        
        # Enhance your analysis prompt
        enhanced_prompt = self.rag.enhance_prompt_with_context(
            self.base_analysis_prompt,
            context
        )
        
        # Continue with enhanced analysis...
```

## Testing End-to-End

### 1. **Run System Tests**
```bash
python test_complete_system.py
```

### 2. **Manual Testing Steps**

```python
# Test 1: Basic functionality
rag = RAGHandler("json")  # Use JSON for testing
insights = rag._load_learning_insights()
print(f"Loaded {len(insights)} insights")

# Test 2: Context retrieval
context = rag.get_similar_contexts("fix bug in authentication", include_learning=True)
print(f"Context includes learning: {len(context.learning_insights) > 0}")

# Test 3: Prompt enhancement
base = "Review this PR:"
enhanced = rag.enhance_prompt_with_context(base, context)
print(f"Enhancement ratio: {len(enhanced)/len(base):.1f}x")

# Test 4: Pinecone integration (requires API key)
if pinecone_available:
    rag_pinecone = RAGHandler("pinecone")
    success = rag_pinecone.populate_learning_insights()
    print(f"Pinecone population: {success}")
```

### 3. **Production Testing**

```python
# Test with real PR data
real_pr = {
    "title": "Fix authentication vulnerability in login endpoint",
    "description": "Updates JWT token validation to prevent replay attacks",
    "diff": "- old_validation() + new_secure_validation()"
}

context = rag.get_similar_contexts(
    f"{real_pr['title']} {real_pr['description']}",
    k=5,
    include_learning=True
)

# Verify results
assert len(context.similar_diffs) > 0, "Should find similar PRs"
assert len(context.learning_insights) > 0, "Should find relevant learning insights"

formatted = context.get_formatted_context()
assert "Learning Insights" in formatted, "Should include learning section"
```

## Configuration

### Environment Variables
```bash
# Required for Pinecone
export PINECONE_API_KEY="your-api-key"
export OPENAI_API_KEY="your-openai-key"  # For embeddings

# Optional
export LANCEDB_URI="./lancedb"  # For LanceDB storage
```

### Settings in `config.yml`
```yaml
pinecone:
  api_key: ${PINECONE_API_KEY}

openai:
  key: ${OPENAI_API_KEY}

lancedb:
  uri: "./lancedb"
```

## Monitoring & Maintenance

### 1. **Check System Health**
```python
# Database statistics
db_stats = rag.get_database_stats()
learning_stats = rag.get_learning_insights_stats()

print(f"Total documents: {db_stats.get('total_documents', 0)}")
print(f"Learning insights: {learning_stats.get('total_learning_insights', 0)}")
```

### 2. **Update Learning Insights**
```python
# When new learning data is available
success = rag.populate_learning_insights()  # Automatically handles duplicates
```

### 3. **Performance Monitoring**
```python
import time

start = time.time()
context = rag.get_similar_contexts("test query", k=5, include_learning=True)
end = time.time()

print(f"Context retrieval took {end - start:.2f} seconds")
print(f"Retrieved {len(context.similar_diffs)} PRs and {len(context.learning_insights)} insights")
```

The system is now ready for production use with comprehensive learning-enhanced PR analysis capabilities!