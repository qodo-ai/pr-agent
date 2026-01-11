#!/usr/bin/env python3
"""
Workiz PR Agent CLI Admin Tool

Administrative commands for managing the PR Agent:
- status: Show database and system status
- discover: Discover repositories in the organization
- index-repos: Index repositories for RAG
- analyze-repos: Run RepoSwarm analysis
- sync-jira: Sync Jira tickets
- sync-github-activity: Sync GitHub activity for Knowledge Assistant
- costs: Show API usage and costs
- reviews: Show review history

Usage:
    python scripts/cli_admin.py status
    python scripts/cli_admin.py costs --month 2026-01
    python scripts/cli_admin.py reviews --limit 10
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path

import click

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, verbose):
    """Workiz PR Agent CLI Admin Tool"""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


@cli.command()
@click.pass_context
def status(ctx):
    """Show database and system status."""
    click.echo("📊 Workiz PR Agent Status\n")
    click.echo("=" * 50)
    
    # Check environment
    click.echo("\n🔧 Environment:")
    env_vars = [
        "DATABASE_URL",
        "GITHUB_APP_ID",
        "GOOGLE_API_KEY",
        "JIRA_BASE_URL",
    ]
    for var in env_vars:
        value = os.environ.get(var)
        status_icon = "✅" if value else "❌"
        masked = "***" if value else "Not set"
        click.echo(f"  {status_icon} {var}: {masked}")
    
    # Check database
    click.echo("\n💾 Database:")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        click.echo("  ❌ DATABASE_URL not configured")
        return
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            click.echo("  ✅ Connection successful")
            
            # Get table counts
            tables = [
                "repositories",
                "code_chunks",
                "jira_tickets",
                "review_history",
                "api_usage",
            ]
            
            for table in tables:
                try:
                    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    click.echo(f"  📦 {table}: {count} records")
                except Exception:
                    click.echo(f"  ⚠️  {table}: table not found")
                    
    except Exception as e:
        click.echo(f"  ❌ Connection failed: {e}")


@cli.command()
@click.option("--month", "-m", help="Month in YYYY-MM format (defaults to current)")
@click.pass_context
def costs(ctx, month):
    """Show API usage and cost summary."""
    click.echo("💰 API Usage & Costs\n")
    click.echo("=" * 50)
    
    if month:
        try:
            year, mon = month.split("-")
            start_date = datetime(int(year), int(mon), 1)
            if int(mon) == 12:
                end_date = datetime(int(year) + 1, 1, 1)
            else:
                end_date = datetime(int(year), int(mon) + 1, 1)
        except Exception:
            click.echo("❌ Invalid month format. Use YYYY-MM")
            return
    else:
        now = datetime.utcnow()
        start_date = datetime(now.year, now.month, 1)
        end_date = now
    
    async def get_costs():
        from pr_agent.db import get_usage_summary
        return await get_usage_summary(start_date, end_date)
    
    summary = asyncio.run(get_costs())
    
    if "error" in summary:
        click.echo(f"❌ {summary['error']}")
        return
    
    click.echo(f"\n📅 Period: {summary['period']['start'][:10]} to {summary['period']['end'][:10]}")
    click.echo(f"\n📊 Totals:")
    click.echo(f"  • API Calls: {summary['totals']['call_count']:,}")
    click.echo(f"  • Input Tokens: {summary['totals']['input_tokens']:,}")
    click.echo(f"  • Output Tokens: {summary['totals']['output_tokens']:,}")
    click.echo(f"  • Estimated Cost: ${summary['totals']['cost_usd']:.2f}")
    
    if summary.get("by_model"):
        click.echo(f"\n🤖 By Model:")
        for model, data in summary["by_model"].items():
            click.echo(f"\n  {model}:")
            click.echo(f"    • Calls: {data['call_count']:,}")
            click.echo(f"    • Cost: ${data['cost_usd']:.2f}")
            click.echo(f"    • Avg Latency: {data['avg_latency_ms']:.0f}ms")
            click.echo(f"    • Success Rate: {data['success_rate']*100:.1f}%")


@cli.command()
@click.option("--repository", "-r", help="Filter by repository")
@click.option("--author", "-a", help="Filter by PR author")
@click.option("--limit", "-l", default=10, help="Number of records to show")
@click.pass_context
def reviews(ctx, repository, author, limit):
    """Show recent review history."""
    click.echo("📝 Review History\n")
    click.echo("=" * 50)
    
    async def get_reviews():
        from pr_agent.db import get_review_history, get_review_stats
        history = await get_review_history(repository, author, limit)
        stats = await get_review_stats(repository)
        return history, stats
    
    history, stats = asyncio.run(get_reviews())
    
    if "error" in stats:
        click.echo(f"❌ {stats['error']}")
        return
    
    click.echo(f"\n📊 Stats (This Month):")
    click.echo(f"  • Total Reviews: {stats['total_reviews']:,}")
    click.echo(f"  • Repos Reviewed: {stats['repos_reviewed']}")
    click.echo(f"  • Authors Reviewed: {stats['authors_reviewed']}")
    click.echo(f"  • Total Findings: {stats['total_findings']:,}")
    click.echo(f"  • Total Suggestions: {stats['total_suggestions']:,}")
    
    if history:
        click.echo(f"\n📋 Recent Reviews:")
        for review in history:
            click.echo(f"\n  • PR #{review['pr_number']}: {review['pr_title'][:50]}...")
            click.echo(f"    Repository: {review['repository']}")
            click.echo(f"    Author: {review['pr_author']}")
            click.echo(f"    Findings: {review['findings_count']}, Suggestions: {review['suggestions_count']}")
            click.echo(f"    Duration: {review['duration_ms']}ms")
            click.echo(f"    Date: {review['created_at']}")
    else:
        click.echo("\n  No reviews found.")


@cli.command()
@click.option("--orgs", "-o", default="Workiz", help="GitHub organizations (comma-separated)")
@click.option("--dry-run", is_flag=True, help="Show what would be discovered without saving")
@click.pass_context
def discover(ctx, orgs, dry_run):
    """Discover repositories in GitHub organizations."""
    click.echo("🔍 Repository Discovery\n")
    click.echo("=" * 50)
    
    # TODO: Implement in Phase 5
    click.echo("⚠️  Repository discovery will be implemented in Phase 5.")
    click.echo(f"    Organizations to scan: {orgs}")
    click.echo(f"    Dry run: {dry_run}")


@cli.command("index-repos")
@click.option("--all", "all_repos", is_flag=True, help="Index all repositories")
@click.option("--repo", "-r", help="Index specific repository")
@click.pass_context
def index_repos(ctx, all_repos, repo):
    """Index repositories for code search (RAG)."""
    click.echo("📚 Repository Indexing\n")
    click.echo("=" * 50)
    
    # TODO: Implement in Phase 5
    click.echo("⚠️  Repository indexing will be implemented in Phase 5.")
    if all_repos:
        click.echo("    Mode: Index all repositories")
    elif repo:
        click.echo(f"    Mode: Index repository {repo}")
    else:
        click.echo("    Error: Specify --all or --repo")


@cli.command("analyze-repos")
@click.option("--all", "all_repos", is_flag=True, help="Analyze all repositories")
@click.option("--repo", "-r", help="Analyze specific repository")
@click.pass_context
def analyze_repos(ctx, all_repos, repo):
    """Run RepoSwarm analysis on repositories."""
    click.echo("🔬 RepoSwarm Analysis\n")
    click.echo("=" * 50)
    
    # TODO: Implement in Phase 5
    click.echo("⚠️  RepoSwarm analysis will be implemented in Phase 5.")
    if all_repos:
        click.echo("    Mode: Analyze all repositories")
    elif repo:
        click.echo(f"    Mode: Analyze repository {repo}")
    else:
        click.echo("    Error: Specify --all or --repo")


@cli.command("sync-jira")
@click.option("--full", is_flag=True, help="Full sync (all tickets)")
@click.option("--incremental", is_flag=True, help="Incremental sync (recent changes)")
@click.pass_context
def sync_jira(ctx, full, incremental):
    """Sync Jira tickets for context."""
    click.echo("🎫 Jira Sync\n")
    click.echo("=" * 50)
    
    # TODO: Implement in Phase 6
    click.echo("⚠️  Jira sync will be implemented in Phase 6.")
    if full:
        click.echo("    Mode: Full sync")
    elif incremental:
        click.echo("    Mode: Incremental sync")
    else:
        click.echo("    Error: Specify --full or --incremental")


@cli.command("sync-github-activity")
@click.option("--days", "-d", default=30, help="Days of history to sync")
@click.pass_context
def sync_github_activity(ctx, days):
    """Sync GitHub activity for Knowledge Assistant."""
    click.echo("📥 GitHub Activity Sync\n")
    click.echo("=" * 50)
    
    # TODO: Implement in Phase 8
    click.echo("⚠️  GitHub activity sync will be implemented in Phase 8.")
    click.echo(f"    Days to sync: {days}")


@cli.command("model-pricing")
@click.option("--model", "-m", help="Specific model to check (e.g., gemini/gemini-3-pro)")
@click.option("--filter", "-f", "filter_str", help="Filter models by name (e.g., 'gemini', 'gpt-4')")
@click.pass_context
def model_pricing(ctx, model, filter_str):
    """Show model pricing from LiteLLM's database.
    
    LiteLLM maintains an up-to-date community database of model pricing.
    This command shows what prices will be used for cost tracking.
    """
    click.echo("💵 Model Pricing (from LiteLLM)\n")
    click.echo("=" * 50)
    
    try:
        from pr_agent.db import get_model_pricing, list_available_models_with_pricing
        
        if model:
            pricing = get_model_pricing(model)
            if pricing:
                click.echo(f"\n🤖 {model}:")
                input_per_1m = pricing["input_cost_per_token"] * 1_000_000
                output_per_1m = pricing["output_cost_per_token"] * 1_000_000
                click.echo(f"   Input:  ${input_per_1m:.4f} per 1M tokens")
                click.echo(f"   Output: ${output_per_1m:.4f} per 1M tokens")
                if pricing.get("max_tokens"):
                    click.echo(f"   Max Tokens: {pricing['max_tokens']:,}")
                if pricing.get("max_input_tokens"):
                    click.echo(f"   Max Input: {pricing['max_input_tokens']:,}")
                if pricing.get("max_output_tokens"):
                    click.echo(f"   Max Output: {pricing['max_output_tokens']:,}")
            else:
                click.echo(f"❌ Model '{model}' not found in LiteLLM's database.")
                click.echo("   Fallback pricing will be used for cost estimation.")
        else:
            all_models = list_available_models_with_pricing()
            
            if filter_str:
                filtered = {k: v for k, v in all_models.items() if filter_str.lower() in k.lower()}
            else:
                common_models = [
                    "gemini/gemini-3-pro",
                    "gemini/gemini-2.5-pro",
                    "gemini/gemini-2.0-flash",
                    "gemini/gemini-1.5-pro",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                    "claude-3-5-sonnet",
                    "claude-3-opus",
                    "claude-3-haiku",
                ]
                filtered = {k: all_models[k] for k in common_models if k in all_models}
            
            if not filtered:
                click.echo("❌ No models found matching criteria.")
                if filter_str:
                    click.echo(f"   Filter used: '{filter_str}'")
                return
            
            click.echo(f"\n{'Model':<35} {'Input/1M':<12} {'Output/1M':<12}")
            click.echo("-" * 60)
            
            for model_name in sorted(filtered.keys()):
                info = filtered[model_name]
                input_cost = f"${info['input_cost_per_1m']:.4f}"
                output_cost = f"${info['output_cost_per_1m']:.4f}"
                click.echo(f"{model_name:<35} {input_cost:<12} {output_cost:<12}")
            
            click.echo(f"\n📊 Total models in LiteLLM database: {len(all_models):,}")
            if filter_str:
                click.echo(f"   Showing: {len(filtered)} models matching '{filter_str}'")
            else:
                click.echo(f"   Showing: {len(filtered)} common models (use --filter for more)")
        
    except ImportError as e:
        click.echo(f"❌ LiteLLM not installed: {e}")
        click.echo("   Fallback pricing will be used.")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


if __name__ == "__main__":
    cli()
