# Deployment Architecture

**Generated:** 2025-10-07

## Deployment Options Overview

```mermaid
graph TB
    subgraph "Deployment Methods"
        CLI[CLI Local Execution]
        GHA[GitHub Actions]
        GHApp[GitHub App]
        GLWebhook[GitLab Webhook]
        BBApp[Bitbucket App]
        AzureWebhook[Azure DevOps Webhook]
        Docker[Docker Container]
        Lambda[AWS Lambda]
        SelfHosted[Self-Hosted Server]
    end

    subgraph "Infrastructure Components"
        FastAPI[FastAPI Server]
        Uvicorn[Uvicorn ASGI]
        Gunicorn[Gunicorn]
    end

    subgraph "External Dependencies"
        GitAPIs[Git Platform APIs]
        LLMServices[LLM Services]
        SecretsManager[Secrets Manager]
        Storage[Storage Services]
    end

    CLI --> LLMServices
    CLI --> GitAPIs

    GHA --> FastAPI
    GHApp --> FastAPI
    GLWebhook --> FastAPI
    BBApp --> FastAPI
    AzureWebhook --> FastAPI

    FastAPI --> Uvicorn
    FastAPI --> Gunicorn

    FastAPI --> GitAPIs
    FastAPI --> LLMServices
    FastAPI --> SecretsManager
    FastAPI --> Storage

    Docker --> FastAPI
    Lambda --> FastAPI
    SelfHosted --> FastAPI

    style CLI fill:#90EE90
    style GHA fill:#87CEEB
    style FastAPI fill:#9370DB
    style Docker fill:#FFD700
```

## GitHub Actions Deployment

```mermaid
flowchart TB
    Start([PR Event]) --> Trigger[GitHub Actions Triggered]
    Trigger --> Checkout[Checkout PR Agent Code]
    Checkout --> SetupPython[Setup Python Environment]
    SetupPython --> InstallDeps[Install Dependencies]
    InstallDeps --> LoadSecrets[Load Secrets from<br/>GitHub Secrets]

    LoadSecrets --> SetEnv[Set Environment Variables:<br/>OPENAI_KEY<br/>GITHUB_TOKEN]

    SetEnv --> RunAction[Run PR Agent Action]
    RunAction --> ParseEvent[Parse GitHub Event]
    ParseEvent --> ExtractPR[Extract PR URL]
    ExtractPR --> ExecuteCommand[Execute Command<br/>e.g., review]

    ExecuteCommand --> ProcessPR[Process PR]
    ProcessPR --> CallAI[Call AI Service]
    CallAI --> PostComment[Post Comment to PR]
    PostComment --> Complete([Complete])

    style Trigger fill:#FFD700
    style RunAction fill:#9370DB
    style Complete fill:#90EE90
```

## GitHub App Deployment

```mermaid
sequenceDiagram
    participant User
    participant GitHub
    participant Webhook as Webhook Receiver
    participant Queue as Task Queue
    participant Worker as PR Agent Worker
    participant Storage as Persistent Storage

    User->>GitHub: Create/Update PR
    GitHub->>Webhook: POST /webhook<br/>PR event payload

    Webhook->>Webhook: Verify webhook signature
    Webhook->>Webhook: Parse event type
    Webhook->>Queue: Enqueue task

    Webhook-->>GitHub: 200 OK

    Queue->>Worker: Dequeue task
    Worker->>Worker: Parse PR URL
    Worker->>GitHub: Fetch PR details
    GitHub-->>Worker: PR data

    Worker->>Worker: Process PR
    Worker->>Storage: Check previous runs
    Storage-->>Worker: Previous state

    Worker->>Worker: Execute command
    Worker->>GitHub: Post results
    GitHub-->>Worker: Success

    Worker->>Storage: Update state
    Worker->>Queue: Mark complete

    GitHub->>User: Notification
```

## GitLab Webhook Deployment

```mermaid
flowchart TB
    Start([GitLab MR Event]) --> WebhookPost[POST to Webhook URL]
    WebhookPost --> VerifyToken[Verify GitLab Token]
    VerifyToken --> ValidToken{Valid?}

    ValidToken -->|No| Reject[Return 401 Unauthorized]
    ValidToken -->|Yes| ParsePayload[Parse Webhook Payload]

    ParsePayload --> ExtractEvent[Extract Event Type:<br/>MR opened/updated]
    ExtractEvent --> GetMRUrl[Get MR URL]
    GetMRUrl --> CreateTask[Create Processing Task]

    CreateTask --> Background[Run in Background]
    Background --> FetchMR[Fetch MR Details<br/>from GitLab API]
    FetchMR --> ProcessDiff[Process MR Diff]
    ProcessDiff --> CallAI[Call AI Service]
    CallAI --> FormatResponse[Format Response]
    FormatResponse --> PostComment[Post Comment to GitLab MR]
    PostComment --> Complete([Complete])

    Reject --> End([End])

    style ValidToken fill:#FFD700
    style Background fill:#87CEEB
    style Complete fill:#90EE90
```

## Docker Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Container"
        subgraph "Application Layer"
            FastAPI[FastAPI App]
            Routes[Route Handlers]
            PRAgent[PR Agent Core]
        end

        subgraph "Dependencies"
            Python[Python 3.11]
            Libs[Python Libraries:<br/>litellm, pygithub,<br/>python-gitlab, etc.]
        end

        subgraph "Configuration"
            EnvVars[Environment Variables]
            ConfigFiles[Config Files:<br/>configuration.toml]
        end
    end

    subgraph "External Services"
        GitPlatforms[Git Platforms]
        LLMAPIs[LLM APIs]
        Secrets[Secrets Manager]
    end

    subgraph "Host Environment"
        Port[Port Mapping<br/>3000:3000]
        Volumes[Volume Mounts<br/>for config]
        Network[Docker Network]
    end

    EnvVars --> FastAPI
    ConfigFiles --> PRAgent
    Python --> FastAPI
    Libs --> PRAgent

    FastAPI --> Routes
    Routes --> PRAgent

    Port --> FastAPI
    Volumes --> ConfigFiles
    Network --> FastAPI

    PRAgent --> GitPlatforms
    PRAgent --> LLMAPIs
    PRAgent --> Secrets

    style FastAPI fill:#9370DB
    style PRAgent fill:#87CEEB
    style Docker Container fill:#E6E6FA
```

## AWS Lambda Deployment

```mermaid
flowchart LR
    Start([Webhook Event]) --> APIGateway[API Gateway]
    APIGateway --> Lambda[Lambda Function]

    Lambda --> ColdStart{Cold<br/>Start?}
    ColdStart -->|Yes| InitEnv[Initialize Environment:<br/>Load deps,<br/>Config,<br/>Secrets]
    ColdStart -->|No| UseWarm[Use Warm Instance]

    InitEnv --> ProcessEvent[Process Event]
    UseWarm --> ProcessEvent

    ProcessEvent --> ParsePayload[Parse Webhook Payload]
    ParsePayload --> FetchPR[Fetch PR Data]
    FetchPR --> CheckSize{PR Size<br/>OK for Lambda?}

    CheckSize -->|Yes| ProcessInline[Process in Lambda]
    CheckSize -->|No| OffloadSQS[Offload to SQS Queue]

    ProcessInline --> CallLLM[Call LLM Service]
    CallLLM --> PostResults[Post Results]
    PostResults --> Return([Return Response])

    OffloadSQS --> SQS[SQS Queue]
    SQS --> ECS[ECS Task for<br/>Large PR Processing]
    ECS --> PostResults

    style Lambda fill:#FFD700
    style ColdStart fill:#FFA500
    style OffloadSQS fill:#87CEEB
```

## Self-Hosted Server Deployment

```mermaid
graph TB
    subgraph "Server Infrastructure"
        subgraph "Load Balancer"
            LB[Nginx/HAProxy]
        end

        subgraph "Application Tier"
            Gunicorn1[Gunicorn Worker 1]
            Gunicorn2[Gunicorn Worker 2]
            Gunicorn3[Gunicorn Worker 3]
        end

        subgraph "Background Jobs"
            Celery[Celery Workers]
            Redis[Redis Queue]
        end

        subgraph "Data/Config"
            DB[(PostgreSQL)]
            Cache[(Redis Cache)]
            Files[Config Files]
        end
    end

    subgraph "Monitoring"
        Logs[Log Aggregation]
        Metrics[Metrics/Monitoring]
        Health[Health Checks]
    end

    subgraph "External"
        Git[Git Platforms]
        LLM[LLM Services]
    end

    LB --> Gunicorn1
    LB --> Gunicorn2
    LB --> Gunicorn3

    Gunicorn1 --> Redis
    Gunicorn2 --> Redis
    Gunicorn3 --> Redis

    Redis --> Celery

    Gunicorn1 --> DB
    Gunicorn1 --> Cache
    Gunicorn1 --> Files

    Celery --> Git
    Celery --> LLM

    Gunicorn1 --> Logs
    Celery --> Logs
    Gunicorn1 --> Metrics
    LB --> Health

    style LB fill:#9370DB
    style Gunicorn1 fill:#87CEEB
    style Celery fill:#FFD700
```

## Scaling Considerations

```mermaid
flowchart TB
    Start([Request Load]) --> CheckLoad{Current<br/>Load Level?}

    CheckLoad -->|Low| SingleWorker[Single Worker]
    CheckLoad -->|Medium| MultiWorker[Multiple Workers<br/>2-4 instances]
    CheckLoad -->|High| AutoScale[Auto-scaling Group<br/>5-20 instances]
    CheckLoad -->|Very High| Distributed[Distributed System<br/>Queue-based Processing]

    SingleWorker --> ServeRequest[Serve Request]
    MultiWorker --> LoadBalancer[Load Balancer]
    AutoScale --> LoadBalancer
    Distributed --> MessageQueue[Message Queue<br/>RabbitMQ/SQS]

    LoadBalancer --> WorkerPool[Worker Pool]
    MessageQueue --> WorkerPool

    WorkerPool --> ProcessPR[Process PR]
    ServeRequest --> ProcessPR

    ProcessPR --> CheckPRSize{PR Size?}
    CheckPRSize -->|Small| QuickProcess[Quick Processing<br/>< 5 seconds]
    CheckPRSize -->|Medium| StandardProcess[Standard Processing<br/>5-30 seconds]
    CheckPRSize -->|Large| BatchProcess[Batch Processing<br/>30+ seconds]

    QuickProcess --> Response([Return Response])
    StandardProcess --> Response
    BatchProcess --> AsyncResponse[Async Response<br/>with Status Updates]
    AsyncResponse --> Response

    style CheckLoad fill:#FFD700
    style AutoScale fill:#9370DB
    style Distributed fill:#FFB6C1
```

## Configuration Management

```mermaid
flowchart TB
    subgraph "Configuration Sources"
        Default[Default Config<br/>configuration.toml]
        Secrets[Secrets<br/>.secrets.toml]
        Env[Environment Variables]
        CLI[CLI Arguments]
        Repo[Repo-Specific<br/>.pr_agent.toml]
    end

    subgraph "Configuration Layers"
        Layer1[Layer 1: Defaults]
        Layer2[Layer 2: Secrets]
        Layer3[Layer 3: Environment]
        Layer4[Layer 4: CLI Args]
        Layer5[Layer 5: Repo Config]
    end

    subgraph "Deployment Methods"
        GHA_Deploy[GitHub Actions]
        Docker_Deploy[Docker]
        Lambda_Deploy[Lambda]
        Server_Deploy[Self-Hosted]
    end

    Default --> Layer1
    Secrets --> Layer2
    Env --> Layer3
    CLI --> Layer4
    Repo --> Layer5

    Layer1 --> Layer2
    Layer2 --> Layer3
    Layer3 --> Layer4
    Layer4 --> Layer5

    Layer5 --> FinalConfig[Final Configuration]

    FinalConfig --> GHA_Deploy
    FinalConfig --> Docker_Deploy
    FinalConfig --> Lambda_Deploy
    FinalConfig --> Server_Deploy

    style Layer5 fill:#90EE90
    style FinalConfig fill:#FFD700
```

## Security Architecture

```mermaid
graph TB
    subgraph "Secret Management"
        EnvSecrets[Environment Variables]
        AWSSecrets[AWS Secrets Manager]
        GCPSecrets[GCP Secret Manager]
        VaultSecrets[HashiCorp Vault]
    end

    subgraph "Authentication"
        GitTokens[Git Platform Tokens]
        LLMKeys[LLM API Keys]
        WebhookSecrets[Webhook Secrets]
    end

    subgraph "Authorization"
        RateLimits[Rate Limiting]
        IPWhitelist[IP Whitelisting]
        ScopeValidation[Scope Validation]
    end

    subgraph "Data Protection"
        Transit[TLS/HTTPS in Transit]
        AtRest[Encryption at Rest]
        NoRetention[Zero Data Retention]
    end

    EnvSecrets --> GitTokens
    AWSSecrets --> GitTokens
    GCPSecrets --> GitTokens
    VaultSecrets --> GitTokens

    GitTokens --> RateLimits
    LLMKeys --> RateLimits
    WebhookSecrets --> IPWhitelist

    RateLimits --> Transit
    ScopeValidation --> Transit
    Transit --> AtRest
    AtRest --> NoRetention

    style EnvSecrets fill:#FFD700
    style GitTokens fill:#87CEEB
    style Transit fill:#90EE90
    style NoRetention fill:#9370DB
```
