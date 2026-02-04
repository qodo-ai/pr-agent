
The default models used by Qodo Merge 💎 (December 2025) are a combination of GPT-5.2, Haiku-4.5, and Gemini 2.5 Pro.

### Selecting a Specific Model

Users can configure Qodo Merge to use only a specific model by editing the [configuration](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) file.
The models supported by Qodo Merge are:

- `anthropic/claude-haiku-4-5-20251001`
- `anthropic/claude-sonnet-4-5-20250929`
- `vertex_ai/gemini-2.5-pro`
- `vertex_ai/gemini-3-pro-preview`
- `gemini/gemini-3-pro-preview`
- `gpt-5-2025-08-07`
- `gpt-5.2-2025-12-11`

To restrict Qodo Merge to using `anthropic/claude-haiku-4-5-20251001`:

```toml
[config]
model="anthropic/claude-haiku-4-5-20251001"
```

To restrict Qodo Merge to using `anthropic/claude-sonnet-4-5-20250929`:

```toml
[config]
model="anthropic/claude-sonnet-4-5-20250929"
```

To restrict Qodo Merge to using `vertex_ai/gemini-2.5-pro`:

```toml
[config]
model="vertex_ai/gemini-2.5-pro"
```

To restrict Qodo Merge to using `vertex_ai/gemini-3-pro-preview`:

```toml
[config]
model="vertex_ai/gemini-3-pro-preview"
```

To restrict Qodo Merge to using `gemini/gemini-3-pro-preview`:

```toml
[config]
model="gemini/gemini-3-pro-preview"
```

To restrict Qodo Merge to using `gpt-5-2025-08-07`:

```toml
[config]
model="gpt-5-2025-08-07"
```

To restrict Qodo Merge to using `gpt-5.2-2025-12-11`:

```toml
[config]
model="gpt-5.2-2025-12-11"
```
