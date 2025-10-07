# PR-Agent Request Flow Architecture

**Generated:** 2025-10-07

## Request Processing Flow

This diagram illustrates how a PR review request flows through the system from entry point to completion.

```mermaid
sequenceDiagram
    participant User
    participant Entry as Entry Point<br/>(CLI/Action/Webhook)
    participant Agent as PR Agent Core
    participant Router as Command Router
    participant Tool as Tool<br/>(e.g., PRReviewer)
    participant GitProvider as Git Provider
    participant Processor as PR Processing
    participant TokenMgr as Token Handler
    participant AIHandler as AI Handler
    participant LLM as LLM Service<br/>(OpenAI/Claude)
    participant Output as Git Platform

    User->>Entry: /review command
    Entry->>Agent: handle_request(pr_url, "review")

    Agent->>Agent: apply_repo_settings()
    Agent->>Agent: parse_command_args()
    Agent->>Agent: validate_args()
    Agent->>Agent: update_settings_from_args()

    Agent->>Router: route_to_tool("review")
    Router->>Tool: PRReviewer(pr_url).run()

    Tool->>GitProvider: get_diff_files()
    GitProvider-->>Tool: List[FilePatchInfo]

    Tool->>GitProvider: get_pr_description()
    GitProvider-->>Tool: description_text

    Tool->>GitProvider: get_commit_messages()
    GitProvider-->>Tool: commit_messages

    Tool->>Processor: get_pr_diff(git_provider, token_handler, model)

    Processor->>TokenMgr: count_tokens(content)
    TokenMgr-->>Processor: token_count

    alt Token count within limits
        Processor->>Processor: generate_extended_diff()
        Processor-->>Tool: full_diff
    else Token count exceeds limits
        Processor->>Processor: pr_generate_compressed_diff()
        Processor->>Processor: handle_patch_deletions()
        Processor->>Processor: sort_files_by_priority()
        Processor->>Processor: clip_large_patches()
        Processor-->>Tool: compressed_diff
    end

    Tool->>Tool: prepare_prompt(diff, description, context)

    Tool->>AIHandler: chat_completion(prompt)
    AIHandler->>LLM: API call with prompt
    LLM-->>AIHandler: response
    AIHandler-->>Tool: parsed_response

    Tool->>Tool: parse_ai_response()
    Tool->>Tool: format_output()

    Tool->>GitProvider: publish_comment(review_comment)
    GitProvider->>Output: Create PR comment
    Output-->>GitProvider: comment_created
    GitProvider-->>Tool: success

    Tool-->>Agent: execution_complete
    Agent-->>Entry: success
    Entry-->>User: Review published
```

## Request Flow for Large PRs

For PRs that exceed token limits, the system uses a compression strategy:

```mermaid
flowchart TD
    Start([PR Review Request]) --> GetDiff[Get PR Diff Files]
    GetDiff --> CountTokens{Total Tokens<br/>< Model Limit?}

    CountTokens -->|Yes| ExtendedDiff[Generate Extended Diff<br/>with extra context lines]
    ExtendedDiff --> SinglePrompt[Single AI Call]
    SinglePrompt --> PublishResults[Publish Results]

    CountTokens -->|No| Compression[Start Compression Strategy]

    Compression --> SortFiles[Sort Files by:<br/>1. Language priority<br/>2. Token count]
    SortFiles --> RemoveDeletions[Remove Delete-Only Hunks]
    RemoveDeletions --> FitFiles[Fit Files into Token Budget]

    FitFiles --> BuildPatch[Build Patch]
    BuildPatch --> CheckSpace{Tokens<br/>Remaining?}

    CheckSpace -->|Yes| AddFile[Add Next File to Patch]
    AddFile --> UpdateTokens[Update Token Count]
    UpdateTokens --> CheckSpace

    CheckSpace -->|No| ListRemaining[List Remaining Files]
    ListRemaining --> MultiCall{Multiple<br/>Calls Enabled?}

    MultiCall -->|Yes| CreateBatch[Create Additional Batches]
    CreateBatch --> MultipleCalls[Multiple AI Calls]
    MultipleCalls --> MergeResults[Merge Results]
    MergeResults --> PublishResults

    MultiCall -->|No| SingleCallCompressed[Single AI Call<br/>with Compressed Diff]
    SingleCallCompressed --> PublishResults

    PublishResults --> End([Complete])

    style Compression fill:#FFD700
    style ExtendedDiff fill:#90EE90
    style SingleCallCompressed fill:#FFA07A
    style MultipleCalls fill:#87CEEB
```

## Command to Tool Mapping

```mermaid
graph LR
    subgraph "User Commands"
        review["/review"]
        describe["/describe"]
        improve["/improve"]
        ask["/ask"]
        askline["/ask_line"]
        changelog["/update_changelog"]
        adddocs["/add_docs"]
        labels["/generate_labels"]
        help["/help"]
        similar["/similar_issue"]
        config["/config"]
    end

    subgraph "Tool Classes"
        PRReviewer[PRReviewer]
        PRDescription[PRDescription]
        PRCodeSuggestions[PRCodeSuggestions]
        PRQuestions[PRQuestions]
        PRLineQuestions[PR_LineQuestions]
        PRUpdateChangelog[PRUpdateChangelog]
        PRAddDocs[PRAddDocs]
        PRGenerateLabels[PRGenerateLabels]
        PRHelpMessage[PRHelpMessage]
        PRSimilarIssue[PRSimilarIssue]
        PRConfig[PRConfig]
    end

    review --> PRReviewer
    describe --> PRDescription
    improve --> PRCodeSuggestions
    ask --> PRQuestions
    askline --> PRLineQuestions
    changelog --> PRUpdateChangelog
    adddocs --> PRAddDocs
    labels --> PRGenerateLabels
    help --> PRHelpMessage
    similar --> PRSimilarIssue
    config --> PRConfig

    style review fill:#9370DB
    style describe fill:#9370DB
    style improve fill:#9370DB
    style ask fill:#9370DB
```

## Token Management Strategy

```mermaid
flowchart TB
    Start([Start Token Analysis]) --> GetModel[Get Model Info<br/>e.g., GPT-4: 8K tokens]
    GetModel --> SetBuffers[Set Token Buffers:<br/>Soft: 1500 tokens<br/>Hard: 1000 tokens]

    SetBuffers --> CountPrompt[Count Prompt Tokens]
    CountPrompt --> CountDiff[Count Diff Tokens]
    CountDiff --> CalcTotal[Calculate Total]

    CalcTotal --> CheckSoft{Total + Soft Buffer<br/>< Model Limit?}

    CheckSoft -->|Yes| FullDiff[Use Full Extended Diff<br/>with extra context]
    FullDiff --> Success([Success])

    CheckSoft -->|No| StartCompression[Start Compression]
    StartCompression --> RemoveContext[Remove Extra Context Lines]
    RemoveContext --> RemoveDeletions[Remove Delete-Only Hunks]
    RemoveDeletions --> PrioritizeFiles[Prioritize Files by Language]

    PrioritizeFiles --> IterateFiles[Iterate Through Files]
    IterateFiles --> CheckHard{Current Total<br/>< Limit - Hard Buffer?}

    CheckHard -->|Yes| CheckSoftPerFile{File + Total<br/>< Limit - Soft Buffer?}
    CheckSoftPerFile -->|Yes| AddFileFull[Add Full File to Diff]
    AddFileFull --> NextFile[Next File]
    NextFile --> IterateFiles

    CheckSoftPerFile -->|No| ClipPolicy{Clipping<br/>Policy?}
    ClipPolicy -->|Skip| SkipFile[Skip File, Add to<br/>Unprocessed List]
    ClipPolicy -->|Clip| ClipFile[Clip File to Fit]
    ClipFile --> AddFilePartial[Add Clipped File]
    AddFilePartial --> NextFile
    SkipFile --> NextFile

    CheckHard -->|No| HardStop[Hard Stop:<br/>No More Files]
    HardStop --> FinalizeList[Add Unprocessed Files List]
    FinalizeList --> CompressedSuccess([Success with<br/>Compressed Diff])

    style CheckSoft fill:#FFD700
    style CheckHard fill:#FFA500
    style FullDiff fill:#90EE90
    style StartCompression fill:#FFB6C1
```

## Configuration Flow

```mermaid
flowchart LR
    Start([PR Request]) --> LoadDefaults[Load Default Config<br/>configuration.toml]
    LoadDefaults --> LoadSecrets[Load Secrets<br/>.secrets.toml]
    LoadSecrets --> CheckRepo{Repo-Specific<br/>Config Exists?}

    CheckRepo -->|Yes| LoadRepoConfig[Load from<br/>.pr_agent.toml<br/>in repo]
    CheckRepo -->|No| CheckEnv{Environment<br/>Variables?}

    LoadRepoConfig --> CheckEnv
    CheckEnv -->|Yes| ApplyEnv[Apply Environment<br/>Variables]
    CheckEnv -->|No| CheckCLI{CLI Arguments?}

    ApplyEnv --> CheckCLI
    CheckCLI -->|Yes| ApplyCLI[Apply CLI Arguments]
    CheckCLI -->|No| FinalConfig[Final Configuration]

    ApplyCLI --> FinalConfig
    FinalConfig --> Execute[Execute Command]

    style LoadDefaults fill:#E6E6FA
    style LoadRepoConfig fill:#FFD700
    style FinalConfig fill:#90EE90
```
