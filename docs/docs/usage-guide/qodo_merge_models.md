
The default models used by Blackbox Merge 💎 (October 2025) are a combination of GPT-5, Haiku-4.5, and Gemini 2.5 Pro.

### Selecting a Specific Model

Users can configure Blackbox Merge to use only a specific model by editing the [configuration](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/configuration_options/) file.
The models supported by Blackbox Merge are:

- `gpt-5`
- `claude-haiku-4.5`
- `gemini-2.5-pro`
- `o4-mini`
- `deepseek/r1`

To restrict Blackbox Merge to using only `o4-mini`, add this setting:

```toml
[config]
model="o4-mini"
```

To restrict Blackbox Merge to using only `GPT-5`, add this setting:

```toml
[config]
model="gpt-5"
```

To restrict Blackbox Merge to using only `gemini-2.5-pro`, add this setting:

```toml
[config]
model="gemini-2.5-pro"
```

To restrict Blackbox Merge to using only `claude-4-sonnet`, add this setting:

```toml
[config]
model="claude-4-sonnet"
```
