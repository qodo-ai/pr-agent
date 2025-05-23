
The default models used by Qodo Merge (April 2025) are a combination of Claude Sonnet 3.7 and Gemini 2.5 Pro.

### Selecting a Specific Model

Users can configure Qodo Merge to use only a specific model by editing the [configuration](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) file.
The models supported by Qodo Merge are:

- `claude-3-7-sonnet`
- `o4-mini`
- `gpt-4.1`
- `gemini-2.5-pro`
- `deepseek/r1`

To restrict Qodo Merge to using only `o4-mini`, add this setting:

```toml
[config]
model="o4-mini"
```

To restrict Qodo Merge to using only `GPT-4.1`, add this setting:

```toml
[config]
model="gpt-4.1"
```

To restrict Qodo Merge to using only `gemini-2.5-pro`, add this setting:

```toml
[config]
model="gemini-2.5-pro"
```


To restrict Qodo Merge to using only `deepseek-r1` us-hosted, add this setting:

```toml
[config]
model="deepseek/r1"
```
