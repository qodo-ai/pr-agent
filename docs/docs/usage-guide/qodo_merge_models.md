
The default models used by Qodo Merge 💎 (August 2025) are a combination of GPT-5, Sonnet-4, and Gemini 2.5 Pro.

### Selecting a Specific Model

Users can configure Qodo Merge to use only a specific model by editing the [configuration](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) file.
The models supported by Qodo Merge are:

- `gpt-5`
- `claude-4-sonnet`
- `o4-mini`
- `gemini-2.5-pro`
- `deepseek/r1`

To restrict Qodo Merge to using only `o4-mini`, add this setting:

```toml
[config]
model="o4-mini"
```

To restrict Qodo Merge to using only `GPT-5`, add this setting:

```toml
[config]
model="gpt-5"
```

To restrict Qodo Merge to using only `gemini-2.5-pro`, add this setting:

```toml
[config]
model="gemini-2.5-pro"
```

To restrict Qodo Merge to using only `claude-4-sonnet`, add this setting:

```toml
[config]
model="claude-4-sonnet"
```
