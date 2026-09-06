## Overview

The `agentic_review` tool reviews a PR the way a person does: it reads the pull request
through tools instead of being handed one pre-assembled diff, delegates one reviewer per
aspect, verifies what those reviewers report against the code, and publishes the result as
the same review comment [`/review`](./review.md) produces.

```
/agentic_review
```

The difference from `/review` is where the diff comes from. `/review` packs as much of the
diff as the token budget allows into a single prompt and takes the model's answer in one
call. `agentic_review` gives the model three read tools — the changed-file list, one file's
diff, one file's contents after the change — and lets it decide what to read. A large PR is
therefore reviewed by reading the files that matter rather than by truncating the diff.

The output, the publishing path, the inline key issues, the labels and every
`pr_reviewer` display option are shared with `/review`, so switching between them changes
how the review is produced, not what the comment looks like.

## Example usage

### Manual triggering

Comment `/agentic_review` on any PR, or run it from the CLI:

```
python -m pr_agent.cli --pr_url=<PR_URL> agentic_review
```

Most of this tool's own settings are host-only (see [Requirements](#requirements)), so a
comment can only carry the two that are not, plus any `pr_reviewer` display option:

```
/agentic_review --pr_agentic_reviewer.aspects='["security"]'
```

### Automatic triggering

To run it when a PR is opened, put it in the relevant provider's `pr_commands` in a
[configuration file](../usage-guide/configuration_options.md#local-configuration-file):

```toml
[github_app]
pr_commands = [
    "/agentic_review",
    "/improve",
]
```

Use it in place of `/review`, not alongside it: both publish the same review comment.

## How a review runs

1. **Map.** The first round is pinned to `list_changed_files`, so the review always starts
   from what the PR actually changed rather than from the description.
2. **Dispatch.** The orchestrator runs one reviewer per aspect, in parallel, each in its own
   context with its own copy of the read tools. A pass ends by submitting a
   schema-validated list of findings; nothing it writes outside that submission is read.
3. **Verify.** A pass's finding is a claim. The orchestrator reads the diff or the file
   itself before reporting it and drops what it cannot confirm.
4. **Answer.** The review YAML, rendered and published by the classic reviewer's code.

Passes are separate contexts on purpose: a security reviewer and a test reviewer want
different attention over the same diff, and in one context each is read against the other's
notes. It also keeps the orchestrator's window carrying the findings rather than the twenty
file diffs each pass read to produce them.

The aspects are `correctness`, `security`, `performance`, `tests` and `maintainability`.

## Requirements

This tool calls a model API directly rather than going through litellm, because the loop
needs tool calls, prompt caching and per-round token accounting that the single-shot handler
does not expose. Two APIs are supported, selected by `pr_agentic_reviewer.provider`:

=== "Claude (default)"

    ```toml
    [pr_agentic_reviewer]
    provider = "anthropic"
    model = "claude-opus-5"
    pass_model = "claude-sonnet-5"

    [anthropic]
    key = "..."   # or set ANTHROPIC_API_KEY
    ```

=== "OpenAI"

    ```toml
    [pr_agentic_reviewer]
    provider = "openai"
    model = "gpt-5.6"
    pass_model = "gpt-5.6"

    [openai]
    key = "..."   # or set OPENAI_API_KEY
    ```

Set `model` and `pass_model` whenever you change `provider`. The shipped defaults are Claude
model names, and they are not empty, so switching `provider` alone sends a Claude model name
to OpenAI and the first call fails.

The OpenAI path runs on the Responses API, with `store` set to `false`: the conversation is
replayed on each request and nothing is retained server-side. Reasoning items are passed back
between rounds, as OpenAI asks for stateless function calling.

Everything else — the tools, the passes, the fence, the review schema, every option below —
is the same on both. `config.model` and `config.fallback_models` do not apply; the model is
`pr_agentic_reviewer.model`.

`provider`, `model` and every budget in this section are host-only: they cannot be set from a
repository's `.pr_agent.toml` or from a PR comment, because they decide which of the host's
API keys is spent and how many model calls are billed to it. `aspects` and
`max_findings_per_pass` can be set per repository.

## Running against a local model

Both SDKs read their base URL from the environment, so pointing the tool at a local
OpenAI-compatible server needs no configuration of its own — only `provider` and `model`:

=== "Ollama"

    ```bash
    # Responses API (provider = "openai"), Ollama v0.13.3+
    export OPENAI_BASE_URL=http://localhost:11434/v1
    export OPENAI_API_KEY=local

    # Messages API (provider = "anthropic"), Ollama v0.14.0+
    export ANTHROPIC_BASE_URL=http://localhost:11434
    export ANTHROPIC_API_KEY=local
    ```

=== "LM Studio"

    ```bash
    # Responses API (provider = "openai"), LM Studio 0.3.39+
    export OPENAI_BASE_URL=http://localhost:1234/v1
    export OPENAI_API_KEY=local

    # Messages API (provider = "anthropic"), LM Studio with Anthropic compatibility
    export ANTHROPIC_BASE_URL=http://localhost:1234
    export ANTHROPIC_API_KEY=local
    ```

Both runtimes serve both compatibility surfaces on the same port, so one instance exercises
both clients. Note the difference in shape: the OpenAI SDK wants the `/v1` prefix in the URL,
the Anthropic SDK appends `/v1/messages` itself and takes the bare host. LM Studio does not
document a minimum version for `/v1/messages`; if the request 404s, update LM Studio.

Set both `model` and `pass_model` to a local model name (`ollama list` shows them), and set
`effort = ""` unless the model documents its own levels.

### What a local run does and does not prove

Useful for developing the loop: a local model exercises the whole request path — the tool
definitions, the forced first read, the tool-call round trip, the conversation the client
stores and replays, and the token accounting. Those are the parts that break when a provider
changes shape, and they cost nothing to check.

Not a substitute for a real model:

- **The review itself will be weak.** `/agentic_review` ends by emitting the same review YAML
  `/review` parses, and a small local model produces malformed or incomplete YAML often enough
  that the published comment is not worth reading.
- **Cache numbers are not comparable.** A local server's prompt caching is its own; a non-zero
  `cache_read` proves the request prefix is stable, not that it would be cached the same way
  by the provider.
- **Unsupported fields fail silently rather than loudly.** A local server generally accepts and
  ignores what it does not implement, so a local pass does not mean the same request is valid
  upstream. MCP is the clearest example: both `mcp_servers` and a `{"type": "mcp"}` tool entry
  return `200 OK` from Ollama with no connection attempted and no error.

## Untrusted PR content

Everything the tools return — titles, descriptions, commit messages, diffs, file contents —
was written by whoever opened the pull request. Every tool result is sanitized and wrapped in
a `<pr_content>` fence before the model sees it, and the prompt tells the model that text in
there asking it to ignore its instructions or approve the change is itself a finding.

## Configuration options

??? example "Parameters"

    <table>
      <tr>
        <td><b>provider</b></td>
        <td>Which model API to run on: <code>anthropic</code> (Claude Messages) or <code>openai</code> (OpenAI Responses). Default: <code>anthropic</code>. Host-only.</td>
      </tr>
      <tr>
        <td><b>model</b></td>
        <td>The model the orchestrator runs on. Default: <code>claude-opus-5</code>; <code>gpt-5.6</code> when <code>provider</code> is <code>openai</code> and no model is set. Host-only.</td>
      </tr>
      <tr>
        <td><b>pass_model</b></td>
        <td>Model for the per-aspect passes — a cheaper one is usually enough, since a pass reads files and submits findings rather than writing the review. Default: <code>claude-sonnet-5</code>. Empty means <code>model</code>. Host-only.</td>
      </tr>
      <tr>
        <td><b>aspects</b></td>
        <td>Which reviewers the orchestrator may dispatch. Default: <code>["correctness", "security", "tests"]</code>. An unknown name is dropped with a warning.</td>
      </tr>
      <tr>
        <td><b>max_tokens</b></td>
        <td>Output ceiling for one model call, orchestrator and pass alike. Default: 16000.</td>
      </tr>
      <tr>
        <td><b>request_timeout_s</b></td>
        <td>Per-request timeout given to the SDK client. Default: 600.</td>
      </tr>
      <tr>
        <td><b>max_findings_per_pass</b></td>
        <td>Cap on what one pass may submit. Default: 6.</td>
      </tr>
      <tr>
        <td><b>max_delegate_calls</b></td>
        <td>Cap on <code>run_review_pass</code> calls in one review. Default: 6.</td>
      </tr>
      <tr>
        <td><b>max_tool_iterations</b> / <b>max_tool_calls</b></td>
        <td>The orchestrator's budget. The round after the last one goes out with tools off, so a review always ends in an answer. Defaults: 20 and 120.</td>
      </tr>
      <tr>
        <td><b>pass_max_tool_iterations</b> / <b>pass_max_tool_calls</b></td>
        <td>The same budgets for one pass. Defaults: 12 and 60.</td>
      </tr>
      <tr>
        <td><b>effort</b></td>
        <td>How hard the model works per call: <code>low</code>, <code>medium</code>, <code>high</code>, <code>xhigh</code> or <code>max</code> (OpenAI also accepts <code>none</code> and <code>minimal</code>). Default: <code>medium</code>; empty uses the model's own default, and an unrecognized level is dropped with a warning rather than failing the review. It is pinned for a whole review — changing it between rounds would invalidate the conversation cache.</td>
      </tr>
      <tr>
        <td><b>force_first_read</b></td>
        <td>Pin the first round to <code>list_changed_files</code>. Default: true. Set false for a model that rejects a forced <code>tool_choice</code>; the prompt asks for that read anyway.</td>
      </tr>
      <tr>
        <td><b>max_fenced_chars</b></td>
        <td>Ceiling on one fenced tool result. Default: 60000.</td>
      </tr>
      <tr>
        <td><b>compact_history_above_tokens</b></td>
        <td>Once a call's prompt reaches this many tokens, the oldest tool results are replaced with a placeholder before the next request goes out. <code>0</code> is off.</td>
      </tr>
    </table>

The `pr_reviewer` options that shape the output — `num_max_findings`, `require_tests_review`,
`require_security_review`, `require_score_review`, `extra_instructions`, `inline_key_issues`
and the rest — apply here too, because both tools emit the same review schema.

## Cost

A review is several model calls: one per orchestrator round, plus a loop per pass. Two
things keep that from being several times the cost of `/review`:

- **Prompt caching.** The static prompt and the tool array are the stable prefix, and
  everything that moves between two reviews of the same repository sits behind them, so a
  round reads the earlier rounds from cache instead of reprocessing them. On Claude those
  positions are marked explicitly, with a rolling breakpoint on the newest message; on
  OpenAI the breakpoint advances on its own and the ordering is what makes it land well.
- **Separate pass contexts.** The file diffs a pass reads stay in that pass; only its
  findings reach the orchestrator.

Each model call logs one `review model call` line with its four token counters. A run whose
`cache_read` stays at 0 across rounds has lost its cached prefix, and that line is where it
shows.
