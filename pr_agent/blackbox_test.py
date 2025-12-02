from pr_agent.config_loader import get_settings
settings = get_settings()
print("LLM Provider:", settings.LLM_PROVIDER)
print("Model:", settings.MODEL)