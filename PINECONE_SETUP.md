# Pinecone Setup for Evolutionary PR Agent

## 1. Get Pinecone API Credentials

1. Sign up at [Pinecone.io](https://www.pinecone.io/)
2. Create a new project or use existing one
3. Get your API key from the Pinecone console
4. Note your environment (e.g., `gcp-starter`, `us-west1-gcp-free`, etc.)

## 2. Configure API Keys

Create `.secrets.toml` file in the project root:

```toml
[openai]
key = "sk-your-openai-api-key"  # Required for embeddings

[pinecone]
api_key = "your-pinecone-api-key"
environment = "gcp-starter"  # Replace with your environment

[config]
# Optional: GitHub token only if you want GitHub integration
# github.personal_access_token = "your-github-token"
```

## 3. Install Dependencies

```bash
pip install pinecone openai
```

## 4. Configuration

The system is now configured to:

- ✅ Use Pinecone for vector storage (instead of JSON)
- ✅ Store all results in databases (no GitHub commenting required)
- ✅ Log all outputs to console for review

## 5. Usage Examples

### Ingest PR data into Pinecone:

```bash
python3 -m pr_agent.cli --pr_url=https://github.com/your-org/repo ingest --max-prs 50
```

### Run evolutionary analysis (stores in database):

```bash
python3 -m pr_agent.cli --pr_url=https://github.com/your-org/repo/pull/123 evolve
```

### View learning statistics:

```bash
python3 -m pr_agent.cli --pr_url=any evolve-stats
```

### Batch learn from repository:

```bash
python3 -m pr_agent.cli --pr_url=https://github.com/your-org/repo learn --max-prs 100
```

## Storage Locations

- **Learning Data**: `learning_data.json` (model comparisons, discrepancies)
- **Analysis Results**: `analysis_results.json` (command outputs)
- **Vector Database**: Pinecone cloud (PR diff embeddings)

## Notes

- No GitHub commenting required - all results stored in databases
- Pinecone provides better performance and scalability than local JSON storage
- All outputs are logged to console for immediate review
- Set `enable_github_publishing = true` in configuration if you want optional GitHub comments
