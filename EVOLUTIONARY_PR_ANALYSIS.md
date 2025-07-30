# 🧬 Evolutionary PR Analysis System

A sophisticated PR analysis system that combines RAG (Retrieval-Augmented Generation), multi-model analysis, and continuous learning to provide increasingly accurate code reviews.

## Overview

This system implements an "evolutionary" approach to PR analysis by:

1. **RAG Context**: Using historical PR data to provide relevant context for current reviews
2. **Multi-Model Analysis**: Running both GPT-4.1 and O3 models in parallel for comprehensive analysis
3. **Continuous Learning**: Using O3 as "ground truth" to identify GPT-4.1 mistakes and improve over time
4. **Performance Monitoring**: Tracking system performance and learning progress

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PR Ingestion  │───▶│   Vector Database │───▶│  RAG Retrieval  │
│                 │    │   (LanceDB/       │    │                 │
│ - Diff Analysis │    │    Pinecone)      │    │ - Similar PRs   │
│ - Summary Gen   │    │                   │    │ - Context       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  O3 Supervisor  │◀───│ Model Comparison │◀───│ Multi-Model     │
│                 │    │                  │    │ Analysis        │
│ - Ground Truth  │    │ - Discrepancies  │    │                 │
│ - Bug Detection │    │ - Learning Data  │    │ - GPT-4.1       │
│ - Quality Score │    │ - Metrics        │    │ - O3 Model      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                          ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Learning Database│◀───│ Enhanced Review │
                       │                  │    │                 │
                       │ - Mistakes       │    │ - Context-Aware │
                       │ - Improvements   │    │ - Multi-Model   │
                       │ - Patterns       │    │ - Learning      │
                       └──────────────────┘    └─────────────────┘
```

## Installation & Setup

### 1. Install Dependencies

```bash
# Core dependencies (if not already installed)
pip install lancedb pyarrow openai

# Optional: for Pinecone vector DB
pip install pinecone-client

# Optional: for advanced metrics
pip install numpy pandas
```

### 2. Configure the System

Add to your `configuration.toml`:

```toml
[pr_evolutionary]
enable_evolutionary_review = true       # Enable the system
enable_rag_context = true              # Use historical context
enable_o3_supervision = true           # Use O3 for learning
vector_db_type = "lancedb"             # "lancedb" or "pinecone"
max_rag_contexts = 5                   # Number of similar PRs to retrieve
batch_learning_enabled = true          # Enable batch learning
confidence_threshold = 0.7             # Minimum confidence for recommendations
parallel_model_analysis = true         # Run models in parallel

# For Pinecone (if using)
[pinecone]
api_key = "your-pinecone-api-key"
environment = "your-pinecone-environment"
```

### 3. Initialize the System

```bash
# Setup databases and verify configuration
python -m pr_agent.tools.pr_evolutionary_setup setup

# Verify everything is working
python -m pr_agent.tools.pr_evolutionary_setup verify

# Bootstrap with data from a repository (optional)
python -m pr_agent.tools.pr_evolutionary_setup bootstrap --repo-url https://github.com/your/repo --max-prs 100
```

## Usage

### Command Line Interface

#### Basic Evolutionary Review
```bash
# Analyze a PR with evolutionary features
python cli.py --pr_url=https://github.com/org/repo/pull/123 evolve

# With specific options
python cli.py --pr_url=... evolve --no-rag --format=summary --confidence=0.8
```

#### Learning from Repository
```bash
# Learn from historical PRs in a repository
python cli.py --pr_url=https://github.com/org/repo learn --max-prs=50

# Ingest PR data for later use
python cli.py --pr_url=https://github.com/org/repo ingest --max-prs=100 --output=data.json
```

#### Performance Monitoring
```bash
# Get learning statistics
python cli.py --pr_url=any evolve-stats

# Export metrics for analysis
python -m pr_agent.tools.pr_evolutionary_metrics export --format=csv
```

### API Usage

```python
from pr_agent.tools.pr_evolutionary_reviewer import EvolutionaryPRReviewer

# Initialize the reviewer
reviewer = EvolutionaryPRReviewer(
    enable_o3_supervision=True,
    enable_rag=True
)

# Analyze a PR
result = reviewer.review_pr_evolutionary("https://github.com/org/repo/pull/123")

# Access results
print(f"Confidence: {result.confidence_score}")
print(f"Context used: {result.context_used}")
print(f"Processing time: {result.processing_time_seconds}s")
print(result.enhanced_review)

# Get learning statistics
stats = reviewer.get_learning_stats()
print(f"Total comparisons: {stats['total_comparisons']}")
print(f"Average agreement: {stats['average_agreement_score']}")
```

### Programmatic Learning

```python
# Learn from external feedback
reviewer.learn_from_pr(
    pr_url="https://github.com/org/repo/pull/123",
    learning_data={
        'user_rating': 4.5,
        'issues_missed': ['Authentication bypass in line 45'],
        'false_positives': ['Style issue was actually correct']
    }
)

# Batch learn from repository
reviewer.batch_learn_from_repository(
    repo_url="https://github.com/org/repo",
    max_prs=200
)
```

## Features

### 🔍 RAG Context Retrieval
- Automatically finds similar historical PRs
- Provides relevant examples and patterns
- Improves review accuracy through context

### 🤖 Multi-Model Analysis
- Runs GPT-4.1 and O3 models in parallel
- Compares results for discrepancies
- Uses O3 as ground truth for learning

### 📈 Continuous Learning
- Identifies where GPT-4.1 deviates from O3
- Stores learning patterns and mistakes
- Improves future reviews automatically

### 📊 Performance Monitoring
- Tracks processing times and accuracy
- Monitors learning progress
- Provides optimization recommendations

### 🗄️ Flexible Storage
- LanceDB for local vector storage
- Pinecone for cloud-based vectors
- JSON storage for learning data

## Command Reference

### `/evolve` - Evolutionary PR Review
Performs comprehensive PR analysis with RAG context and O3 supervision.

**Options:**
- `--no-rag`: Disable RAG context retrieval
- `--no-o3`: Disable O3 supervision
- `--format=json|summary|standard`: Output format
- `--confidence=0.0-1.0`: Minimum confidence threshold
- `--contexts=N`: Maximum RAG contexts to use

**Example:**
```bash
/evolve --format=summary --contexts=3
```

### `/learn` - Batch Learning
Learns from multiple PRs in a repository to improve future analysis.

**Options:**
- `--max-prs=N`: Maximum PRs to process (default: 100)
- `--days=N`: Only learn from PRs in last N days

**Example:**
```bash
/learn --max-prs=50 --days=30
```

### `/evolve-stats` - Performance Statistics
Shows learning progress and system performance metrics.

**Example:**
```bash
/evolve-stats
```

### `/ingest` - Data Ingestion
Ingests PR data for the RAG system without performing analysis.

**Options:**
- `--max-prs=N`: Maximum PRs to ingest
- `--output=file`: Save raw data to file

**Example:**
```bash
/ingest --max-prs=100 --output=repo_data.json
```

## Configuration Options

| Setting | Default | Description |
|---------|---------|-------------|
| `enable_evolutionary_review` | `false` | Master switch for evolutionary features |
| `enable_rag_context` | `true` | Use historical context in reviews |
| `enable_o3_supervision` | `true` | Use O3 for ground truth learning |
| `vector_db_type` | `"lancedb"` | Vector database type |
| `max_rag_contexts` | `5` | Max similar PRs to retrieve |
| `batch_learning_enabled` | `true` | Allow batch learning operations |
| `learning_data_retention_days` | `90` | How long to keep learning data |
| `confidence_threshold` | `0.7` | Min confidence for recommendations |
| `parallel_model_analysis` | `true` | Run models in parallel |

## Performance Monitoring

### Real-time Metrics
- Processing time per PR
- Confidence scores
- Agreement between models
- Resource usage (tokens, API calls)

### Learning Progress
- Model agreement trends
- Common discrepancy patterns
- Improvement over time
- Error rate monitoring

### Alerts and Recommendations
- High processing time warnings
- Low confidence alerts
- Resource usage optimization
- Learning effectiveness insights

## Best Practices

### 1. Data Quality
- Bootstrap with high-quality repository data
- Regularly clean old/irrelevant data
- Focus on repositories with similar codebases

### 2. Performance Optimization
- Enable parallel model analysis
- Monitor and adjust RAG context limits
- Use appropriate vector database for scale

### 3. Learning Management
- Review learning statistics regularly
- Clean up old learning data periodically
- Incorporate external feedback when available

### 4. Monitoring
- Track agreement scores over time
- Monitor processing times
- Set up alerts for performance issues

## Troubleshooting

### Common Issues

**1. "Vector database not found"**
```bash
# Run setup command
python -m pr_agent.tools.pr_evolutionary_setup setup
```

**2. "No RAG contexts found"**
```bash
# Bootstrap with repository data
python -m pr_agent.tools.pr_evolutionary_setup bootstrap --repo-url https://github.com/your/repo
```

**3. "O3 model not available"**
- Check model configuration in settings
- Verify API access to O3/O1 models
- Fallback to GPT-4 if needed

**4. "High processing times"**
- Enable `parallel_model_analysis`
- Reduce `max_rag_contexts`
- Check network connectivity

### Debug Commands
```bash
# Verify system setup
python -m pr_agent.tools.pr_evolutionary_setup verify

# Export learning data for analysis
python -m pr_agent.tools.pr_evolutionary_setup export

# Clean up old data
python -m pr_agent.tools.pr_evolutionary_setup cleanup --days-old=30
```

## Advanced Usage

### Custom Learning Integration
```python
from pr_agent.tools.pr_supervisor import LearningDatabase

# Custom learning data
learning_db = LearningDatabase()
learning_db.store_external_feedback({
    'pr_id': 'repo#123',
    'feedback_type': 'user_correction',
    'data': {'missed_issue': 'SQL injection vulnerability'},
    'timestamp': datetime.now().isoformat()
})
```

### Performance Analysis
```python
from pr_agent.tools.pr_evolutionary_metrics import MetricsCollector

collector = MetricsCollector()
insights = collector.get_performance_insights(days_back=30)

# Analyze trends
print(f"Confidence trend: {insights['quality']['confidence_trend']}")
print(f"Performance recommendations: {insights['recommendations']}")
```

### Custom RAG Context
```python
from pr_agent.algo.rag_handler import HybridSearchRAG

rag = HybridSearchRAG("lancedb")
context = rag.get_context_for_pr_analysis(
    pr_title="Fix authentication bug",
    pr_description="Resolves login issue",
    diff_text="...",
    language="Python"
)

print(f"Found {len(context.similar_diffs)} similar contexts")
```

## Contributing

To extend the evolutionary PR analysis system:

1. **Add new analysis models**: Extend `pr_supervisor.py`
2. **Improve RAG retrieval**: Enhance `rag_handler.py`
3. **Add metrics**: Update `pr_evolutionary_metrics.py`
4. **New storage backends**: Implement in vector database classes

## License

This evolutionary PR analysis system is part of the PR-Agent project and follows the same license terms.