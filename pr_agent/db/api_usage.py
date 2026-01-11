"""
API Usage Tracking Module

Tracks LLM API calls for cost monitoring and analytics.

Uses LiteLLM's model_cost dictionary for up-to-date pricing information.
LiteLLM maintains a community-updated pricing database for 100+ LLM models.
See: https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json
"""

import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

# Fallback costs per 1M tokens (used only if LiteLLM doesn't have the model)
# Updated Jan 2026 based on Google AI pricing
# These are safety net values - LiteLLM's database is preferred
FALLBACK_MODEL_COSTS = {
    "gemini/gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
    "gemini/gemini-3-pro": {"input": 2.00, "output": 12.00},
    "gemini/gemini-2.5-pro": {"input": 1.25, "output": 10.00},
    "gemini/gemini-2.5-flash": {"input": 0.30, "output": 2.50},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """
    Estimate the cost of an API call based on model and token counts.
    
    Uses LiteLLM's model_cost database for accurate, up-to-date pricing.
    Falls back to hardcoded estimates for models not in LiteLLM's database.
    
    Args:
        model: The model name (e.g., "gemini/gemini-3-pro")
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        
    Returns:
        Estimated cost in USD
    """
    try:
        from litellm import cost_per_token
        
        input_cost, output_cost = cost_per_token(
            model=model,
            prompt_tokens=input_tokens,
            completion_tokens=output_tokens
        )
        return round(input_cost + output_cost, 6)
        
    except Exception as e:
        logger.debug(
            "LiteLLM cost calculation failed, using fallback",
            extra={"context": {"model": model, "error": str(e)}}
        )
        costs = FALLBACK_MODEL_COSTS.get(model, {"input": 1.0, "output": 1.0})
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)


def get_model_pricing(model: str) -> dict[str, float] | None:
    """
    Get pricing information for a specific model from LiteLLM.
    
    Args:
        model: The model name (e.g., "gemini/gemini-3-pro")
        
    Returns:
        Dict with input_cost_per_token and output_cost_per_token, or None if not found
    """
    try:
        from litellm import model_cost
        
        if model in model_cost:
            model_info = model_cost[model]
            return {
                "input_cost_per_token": model_info.get("input_cost_per_token", 0),
                "output_cost_per_token": model_info.get("output_cost_per_token", 0),
                "max_tokens": model_info.get("max_tokens"),
                "max_input_tokens": model_info.get("max_input_tokens"),
                "max_output_tokens": model_info.get("max_output_tokens"),
            }
        return None
    except ImportError:
        logger.warning("LiteLLM not installed, cannot get model pricing")
        return None
    except Exception as e:
        logger.debug(
            "Failed to get model pricing",
            extra={"context": {"model": model, "error": str(e)}}
        )
        return None


def list_available_models_with_pricing() -> dict[str, dict]:
    """
    List all models with pricing information from LiteLLM.
    
    Returns:
        Dict mapping model names to their pricing info
    """
    try:
        from litellm import model_cost
        
        result = {}
        for model_name, info in model_cost.items():
            if info.get("input_cost_per_token") is not None:
                result[model_name] = {
                    "input_cost_per_1m": info.get("input_cost_per_token", 0) * 1_000_000,
                    "output_cost_per_1m": info.get("output_cost_per_token", 0) * 1_000_000,
                    "max_tokens": info.get("max_tokens"),
                }
        return result
    except ImportError:
        logger.warning("LiteLLM not installed, cannot list models")
        return {}
    except Exception as e:
        logger.error(
            "Failed to list models with pricing",
            extra={"context": {"error": str(e)}}
        )
        return {}


async def track_api_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: int,
    pr_url: str,
    command: str,
    success: bool = True,
    error_message: str | None = None,
) -> None:
    """
    Track an API call for cost monitoring and analytics.
    
    Args:
        model: The model name used
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        latency_ms: Request latency in milliseconds
        pr_url: The PR URL being processed
        command: The command that triggered the call (e.g., "review")
        success: Whether the call succeeded
        error_message: Error message if failed
    """
    estimated_cost = estimate_cost(model, input_tokens, output_tokens)
    
    logger.info(
        "API call tracked",
        extra={"context": {
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": latency_ms,
            "estimated_cost_usd": estimated_cost,
            "pr_url": pr_url,
            "command": command,
            "success": success,
            "error_message": error_message,
        }}
    )
    
    # Skip database storage if DATABASE_URL not configured
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.debug("DATABASE_URL not configured, skipping API usage storage")
        return
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO api_usage (
                    model, input_tokens, output_tokens, latency_ms,
                    estimated_cost, pr_url, command, success, error_message,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                """,
                (
                    model,
                    input_tokens,
                    output_tokens,
                    latency_ms,
                    estimated_cost,
                    pr_url,
                    command,
                    success,
                    error_message,
                    datetime.utcnow(),
                ),
            )
            conn.commit()
    except Exception as e:
        logger.warning(
            "Failed to store API usage in database",
            extra={"context": {"error": str(e)}}
        )


async def get_usage_summary(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Get API usage summary for a date range.
    
    Args:
        start_date: Start of date range (defaults to beginning of current month)
        end_date: End of date range (defaults to now)
        
    Returns:
        Summary dict with total costs, token counts, call counts by model
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return {"error": "DATABASE_URL not configured"}
    
    if start_date is None:
        now = datetime.utcnow()
        start_date = datetime(now.year, now.month, 1)
    
    if end_date is None:
        end_date = datetime.utcnow()
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    model,
                    COUNT(*) as call_count,
                    SUM(input_tokens) as total_input_tokens,
                    SUM(output_tokens) as total_output_tokens,
                    SUM(estimated_cost) as total_cost,
                    AVG(latency_ms) as avg_latency_ms,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as success_count
                FROM api_usage
                WHERE created_at >= %s AND created_at <= %s
                GROUP BY model
                ORDER BY total_cost DESC
                """,
                (start_date, end_date),
            )
            
            results = cursor.fetchall()
            
            summary = {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "by_model": {},
                "totals": {
                    "call_count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cost_usd": 0.0,
                },
            }
            
            for row in results:
                model_data = {
                    "call_count": row[1],
                    "input_tokens": row[2],
                    "output_tokens": row[3],
                    "cost_usd": float(row[4]),
                    "avg_latency_ms": float(row[5]),
                    "success_rate": row[6] / row[1] if row[1] > 0 else 0,
                }
                summary["by_model"][row[0]] = model_data
                summary["totals"]["call_count"] += row[1]
                summary["totals"]["input_tokens"] += row[2]
                summary["totals"]["output_tokens"] += row[3]
                summary["totals"]["cost_usd"] += float(row[4])
            
            return summary
            
    except Exception as e:
        logger.error(
            "Failed to get API usage summary",
            extra={"context": {"error": str(e)}}
        )
        return {"error": str(e)}
