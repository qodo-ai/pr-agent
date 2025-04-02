from threading import Lock

from jinja2 import Environment, StrictUndefined
from math import ceil
from tiktoken import encoding_for_model, get_encoding

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger


class TokenEncoder:
    _encoder_instance = None
    _model = None
    _lock = Lock()  # Create a lock object

    @classmethod
    def get_token_encoder(cls):
        model = get_settings().config.model
        if cls._encoder_instance is None or model != cls._model:  # Check without acquiring the lock for performance
            with cls._lock:  # Lock acquisition to ensure thread safety
                if cls._encoder_instance is None or model != cls._model:
                    cls._model = model
                    cls._encoder_instance = encoding_for_model(cls._model) if "gpt" in cls._model else get_encoding(
                        "cl100k_base")
        return cls._encoder_instance


class TokenHandler:
    """
    A class for handling tokens in the context of a pull request.

    Attributes:
    - encoder: An object of the encoding_for_model class from the tiktoken module. Used to encode strings and count the
      number of tokens in them.
    - limit: The maximum number of tokens allowed for the given model, as defined in the MAX_TOKENS dictionary in the
      pr_agent.algo module.
    - prompt_tokens: The number of tokens in the system and user strings, as calculated by the _get_system_user_tokens
      method.
    """

    def __init__(self, pr=None, vars: dict = {}, system="", user=""):
        """
        Initializes the TokenHandler object.

        Args:
        - pr: The pull request object.
        - vars: A dictionary of variables.
        - system: The system string.
        - user: The user string.
        """
        self.encoder = TokenEncoder.get_token_encoder()
        if pr is not None:
            self.prompt_tokens = self._get_system_user_tokens(pr, self.encoder, vars, system, user)

    def _get_system_user_tokens(self, pr, encoder, vars: dict, system, user):
        """
        Calculates the number of tokens in the system and user strings.

        Args:
        - pr: The pull request object.
        - encoder: An object of the encoding_for_model class from the tiktoken module.
        - vars: A dictionary of variables.
        - system: The system string.
        - user: The user string.

        Returns:
        The sum of the number of tokens in the system and user strings.
        """
        try:
            environment = Environment(undefined=StrictUndefined)
            system_prompt = environment.from_string(system).render(vars)
            user_prompt = environment.from_string(user).render(vars)
            system_prompt_tokens = len(encoder.encode(system_prompt))
            user_prompt_tokens = len(encoder.encode(user_prompt))
            return system_prompt_tokens + user_prompt_tokens
        except Exception as e:
            get_logger().error(f"Error in _get_system_user_tokens: {e}")
            return 0

    def calc_claude_tokens(self, patch):
        try:
            import anthropic
            from pr_agent.algo import MAX_TOKENS
            client = anthropic.Anthropic(api_key=get_settings(use_context=False).get('anthropic.key'))
            MaxTokens = MAX_TOKENS[get_settings().config.model]

            # Check if the content size is too large (9MB limit)
            if len(patch.encode('utf-8')) > 9_000_000:
                get_logger().warning(
                    "Content too large for Anthropic token counting API, falling back to local tokenizer"
                )
                return MaxTokens

            response = client.messages.count_tokens(
                model="claude-3-7-sonnet-20250219",
                system="system",
                messages=[{
                    "role": "user",
                    "content": patch
                }],
            )
            return response.input_tokens

        except Exception as e:
            get_logger().error( f"Error in Anthropic token counting: {e}")
            return MaxTokens

    def count_tokens(self, patch: str, force_accurate=False) -> int:
        """
        Counts the number of tokens in a given patch string.

        Args:
        - patch: The patch string.

        Returns:
        The number of tokens in the patch string.
        """
        encoder_estimate = len(self.encoder.encode(patch, disallowed_special=()))
        if not force_accurate:
            return encoder_estimate
        #else, need to provide an accurate estimation:

        model = get_settings().config.model.lower()
        if force_accurate and 'claude' in model and get_settings(use_context=False).get('anthropic.key'):
            return self.calc_claude_tokens(patch) # API call to Anthropic for accurate token counting for Claude models
        #else: Non Anthropic provided model

        return encoder_estimate
