# AI Handlers Architecture

**Generated:** 2025-10-07

## AI Handler Class Hierarchy

```mermaid
classDiagram
    class BaseAiHandler {
        <<abstract>>
        +deployment_id str
        +chat_completion(messages) dict
        +get_model() str
        +get_deployment_id() str
    }

    class LiteLLMAIHandler {
        +chat_completion(messages) dict
        +get_model() str
        -_parse_response(response) dict
        -_handle_rate_limit()
        -_handle_timeout()
    }

    class OpenAIAIHandler {
        -openai_client
        +chat_completion(messages) dict
        +get_model() str
        -_create_client()
        -_parse_response(response) dict
    }

    class LangchainAIHandler {
        -langchain_client
        +chat_completion(messages) dict
        +get_model() str
        -_create_chain()
        -_parse_response(response) dict
    }

    BaseAiHandler <|-- LiteLLMAIHandler
    BaseAiHandler <|-- OpenAIAIHandler
    BaseAiHandler <|-- LangchainAIHandler

    class TokenHandler {
        +prompt_tokens int
        +model str
        +count_tokens(text) int
        +get_token_encoder()
    }

    LiteLLMAIHandler ..> TokenHandler : uses
    OpenAIAIHandler ..> TokenHandler : uses
```

## AI Model Support Matrix

```mermaid
graph TB
    subgraph "LiteLLM Handler"
        subgraph "OpenAI Models"
            GPT4[GPT-4]
            GPT4Turbo[GPT-4 Turbo]
            GPT5[GPT-5]
            GPT35[GPT-3.5 Turbo]
        end

        subgraph "Anthropic Models"
            Claude3Opus[Claude 3 Opus]
            Claude3Sonnet[Claude 3 Sonnet]
            Claude3Haiku[Claude 3 Haiku]
        end

        subgraph "Google Models"
            Gemini[Gemini Pro]
            PaLM[PaLM 2]
        end

        subgraph "Other Models"
            Deepseek[Deepseek]
            Cohere[Cohere]
            Replicate[Replicate]
        end
    end

    LiteLLM[LiteLLM Handler] --> GPT4
    LiteLLM --> GPT4Turbo
    LiteLLM --> GPT5
    LiteLLM --> GPT35
    LiteLLM --> Claude3Opus
    LiteLLM --> Claude3Sonnet
    LiteLLM --> Claude3Haiku
    LiteLLM --> Gemini
    LiteLLM --> PaLM
    LiteLLM --> Deepseek
    LiteLLM --> Cohere
    LiteLLM --> Replicate

    style LiteLLM fill:#9370DB
    style GPT4 fill:#90EE90
    style Claude3Opus fill:#87CEEB
```

## AI Request Flow with Fallback

```mermaid
sequenceDiagram
    participant Tool as PR Tool
    participant Handler as AI Handler
    participant Primary as Primary Model<br/>(e.g., GPT-4)
    participant Fallback1 as Fallback Model 1<br/>(e.g., GPT-3.5)
    participant Fallback2 as Fallback Model 2<br/>(e.g., Claude)

    Tool->>Handler: chat_completion(prompt)
    Handler->>Handler: Get primary model config

    Handler->>Primary: API Request
    alt Success
        Primary-->>Handler: Response
        Handler->>Handler: Parse response
        Handler-->>Tool: Parsed result
    else Rate Limit or Error
        Primary-->>Handler: Error
        Handler->>Handler: Log error, try fallback

        Handler->>Fallback1: API Request
        alt Success
            Fallback1-->>Handler: Response
            Handler->>Handler: Parse response
            Handler-->>Tool: Parsed result
        else Error
            Fallback1-->>Handler: Error
            Handler->>Handler: Log error, try next fallback

            Handler->>Fallback2: API Request
            alt Success
                Fallback2-->>Handler: Response
                Handler->>Handler: Parse response
                Handler-->>Tool: Parsed result
            else All Failed
                Fallback2-->>Handler: Error
                Handler-->>Tool: Raise Exception
            end
        end
    end
```

## Model Selection Strategy

```mermaid
flowchart TD
    Start([Request]) --> CheckModelType{Model Type?}

    CheckModelType -->|REGULAR| GetRegular[Get config.model]
    CheckModelType -->|WEAK| GetWeak[Get config.model_weak]
    CheckModelType -->|REASONING| GetReasoning[Get config.model_reasoning]

    GetRegular --> CheckFallback{Fallback<br/>Models<br/>Configured?}
    GetWeak --> CheckFallback
    GetReasoning --> CheckFallback

    CheckFallback -->|Yes| BuildList[Build model list:<br/>Primary + Fallbacks]
    CheckFallback -->|No| SingleModel[Use single model]

    BuildList --> CheckDeployment{Azure<br/>Deployments?}
    CheckDeployment -->|Yes| MapDeployments[Map deployment IDs<br/>to models]
    CheckDeployment -->|No| UseModels[Use models directly]

    MapDeployments --> TryPrimary[Try Primary Model]
    UseModels --> TryPrimary
    SingleModel --> TryPrimary

    TryPrimary --> Success{Success?}
    Success -->|Yes| Return([Return Result])
    Success -->|No| HasNext{More<br/>Models?}

    HasNext -->|Yes| TryNext[Try Next Model]
    TryNext --> Success
    HasNext -->|No| Fail([Raise Exception])

    style CheckModelType fill:#FFD700
    style TryPrimary fill:#87CEEB
    style Return fill:#90EE90
    style Fail fill:#FFB6C1
```

## Token Management in AI Calls

```mermaid
flowchart TB
    Start([Prepare AI Request]) --> CountPrompt[Count Prompt Tokens]
    CountPrompt --> GetModelLimit[Get Model Max Tokens]
    GetModelLimit --> CalcBuffer[Calculate Output Buffer<br/>Usually 1000-2000 tokens]

    CalcBuffer --> CheckFit{Prompt + Buffer<br/>< Model Limit?}

    CheckFit -->|Yes| SendRequest[Send Request]
    CheckFit -->|No| CompressPrompt[Compress Prompt]

    CompressPrompt --> ClipContent[Clip Content to Fit]
    ClipContent --> Validate{Still<br/>Valid?}

    Validate -->|Yes| SendRequest
    Validate -->|No| Error[Raise Error:<br/>Cannot fit content]

    SendRequest --> WaitResponse[Wait for Response]
    WaitResponse --> ParseResponse[Parse Response]

    ParseResponse --> CountResponse[Count Response Tokens]
    CountResponse --> LogUsage[Log Token Usage]
    LogUsage --> Return([Return Result])

    Error --> Fail([Fail])

    style CheckFit fill:#FFD700
    style CompressPrompt fill:#FFA500
    style SendRequest fill:#87CEEB
    style Return fill:#90EE90
    style Fail fill:#FFB6C1
```

## LiteLLM Configuration Flow

```mermaid
flowchart LR
    Start([AI Request]) --> CheckProvider{Model<br/>Provider?}

    CheckProvider -->|openai| ConfigOpenAI[Configure OpenAI]
    CheckProvider -->|azure| ConfigAzure[Configure Azure OpenAI]
    CheckProvider -->|anthropic| ConfigAnthropic[Configure Anthropic]
    CheckProvider -->|google| ConfigGoogle[Configure Google]
    CheckProvider -->|other| ConfigOther[Configure Other Provider]

    ConfigOpenAI --> SetAPIKey[Set API Key]
    ConfigAzure --> SetAzureCreds[Set Azure Credentials:<br/>API Key, Base URL,<br/>Deployment ID]
    ConfigAnthropic --> SetAnthropicKey[Set Anthropic Key]
    ConfigGoogle --> SetGoogleKey[Set Google Key]
    ConfigOther --> SetOtherCreds[Set Provider Credentials]

    SetAPIKey --> BuildRequest[Build LiteLLM Request]
    SetAzureCreds --> BuildRequest
    SetAnthropicKey --> BuildRequest
    SetGoogleKey --> BuildRequest
    SetOtherCreds --> BuildRequest

    BuildRequest --> SetParams[Set Parameters:<br/>Temperature,<br/>Max Tokens,<br/>Top P]

    SetParams --> AddMetadata[Add Metadata:<br/>Request ID,<br/>User ID,<br/>Custom Tags]

    AddMetadata --> MakeCall[Make LiteLLM API Call]
    MakeCall --> Response([Return Response])

    style CheckProvider fill:#FFD700
    style BuildRequest fill:#87CEEB
    style MakeCall fill:#9370DB
    style Response fill:#90EE90
```

## Response Parsing Strategy

```mermaid
flowchart TD
    Start([AI Response]) --> CheckFormat{Response<br/>Format?}

    CheckFormat -->|JSON| ParseJSON[Parse JSON]
    CheckFormat -->|Markdown| ParseMarkdown[Parse Markdown]
    CheckFormat -->|Plain Text| ParseText[Parse Text]

    ParseJSON --> ValidateJSON{Valid<br/>JSON?}
    ValidateJSON -->|Yes| ExtractFields[Extract Required Fields]
    ValidateJSON -->|No| TryFix[Try to Fix JSON:<br/>Escape chars,<br/>Remove trailing commas]

    TryFix --> StillValid{Fixed?}
    StillValid -->|Yes| ExtractFields
    StillValid -->|No| LogError[Log Parse Error]

    ParseMarkdown --> ExtractSections[Extract Sections]
    ParseText --> ExtractPatterns[Extract Patterns]

    ExtractFields --> MapToModel[Map to Data Model]
    ExtractSections --> MapToModel
    ExtractPatterns --> MapToModel

    MapToModel --> Validate{Validate<br/>Result?}
    Validate -->|Yes| Return([Return Parsed Data])
    Validate -->|No| UseDefault[Use Default/Fallback]

    LogError --> UseDefault
    UseDefault --> Return

    style ParseJSON fill:#87CEEB
    style ValidateJSON fill:#FFD700
    style MapToModel fill:#9370DB
    style Return fill:#90EE90
```

## AI Handler Error Handling

```mermaid
flowchart TB
    Start([AI Request]) --> TryCall[Try API Call]
    TryCall --> CheckError{Error<br/>Type?}

    CheckError -->|Rate Limit| Retry[Wait & Retry<br/>Exponential Backoff]
    CheckError -->|Timeout| RetryTimeout[Retry with<br/>Longer Timeout]
    CheckError -->|Invalid Request| FixRequest[Fix Request<br/>Parameters]
    CheckError -->|Auth Error| RefreshAuth[Refresh Authentication]
    CheckError -->|Model Error| TryFallback[Try Fallback Model]
    CheckError -->|Network Error| RetryNetwork[Retry Connection]
    CheckError -->|No Error| Success([Success])

    Retry --> CheckRetries{Max<br/>Retries?}
    RetryTimeout --> CheckRetries
    FixRequest --> TryCall
    RefreshAuth --> TryCall
    TryFallback --> TryCall
    RetryNetwork --> CheckRetries

    CheckRetries -->|No| TryCall
    CheckRetries -->|Yes| LogFail[Log Failure]
    LogFail --> RaiseFinal[Raise Final Exception]

    Success --> Return([Return Result])

    style CheckError fill:#FFD700
    style TryFallback fill:#FFA500
    style Success fill:#90EE90
    style RaiseFinal fill:#FFB6C1
```
