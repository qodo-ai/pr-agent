# Tools Architecture

**Generated:** 2025-10-07

## Tools Class Structure

```mermaid
classDiagram
    class BaseTool {
        <<abstract>>
        +pr_url str
        +git_provider GitProvider
        +ai_handler BaseAiHandler
        +args list
        +run() async
        +prepare_prompt() str
        +parse_response(response) dict
    }

    class PRReviewer {
        +is_auto bool
        +is_answer bool
        +run() async
        -_prepare_pr_review()
        -_get_review_data()
        -_publish_review()
        -_inline_comments()
    }

    class PRDescription {
        +run() async
        -_prepare_description()
        -_generate_title()
        -_generate_summary()
        -_generate_walkthrough()
        -_publish_description()
    }

    class PRCodeSuggestions {
        +run() async
        -_prepare_suggestions()
        -_get_code_suggestions()
        -_rank_suggestions()
        -_publish_suggestions()
        -_track_suggestions()
    }

    class PRQuestions {
        +run() async
        -_prepare_questions()
        -_get_ai_answers()
        -_publish_answers()
    }

    class PR_LineQuestions {
        +run() async
        -_get_line_context()
        -_prepare_line_question()
        -_publish_answer()
    }

    class PRUpdateChangelog {
        +run() async
        -_analyze_changes()
        -_generate_changelog()
        -_update_file()
    }

    class PRAddDocs {
        +run() async
        -_find_undocumented()
        -_generate_docs()
        -_publish_docs()
    }

    class PRGenerateLabels {
        +run() async
        -_analyze_pr()
        -_suggest_labels()
        -_publish_labels()
    }

    class PRHelpDocs {
        +run() async
        -_identify_issues()
        -_find_solutions()
        -_publish_help()
    }

    class PRSimilarIssue {
        +vector_db
        +run() async
        -_embed_pr()
        -_search_similar()
        -_rank_results()
        -_publish_results()
    }

    class PRConfig {
        +run() async
        -_get_current_config()
        -_display_config()
    }

    BaseTool <|-- PRReviewer
    BaseTool <|-- PRDescription
    BaseTool <|-- PRCodeSuggestions
    BaseTool <|-- PRQuestions
    BaseTool <|-- PR_LineQuestions
    BaseTool <|-- PRUpdateChangelog
    BaseTool <|-- PRAddDocs
    BaseTool <|-- PRGenerateLabels
    BaseTool <|-- PRHelpDocs
    BaseTool <|-- PRSimilarIssue
    BaseTool <|-- PRConfig
```

## PR Review Tool Flow

```mermaid
flowchart TB
    Start([/review command]) --> Initialize[Initialize PRReviewer]
    Initialize --> FetchPR[Fetch PR Details]

    FetchPR --> GetDiff[Get PR Diff Files]
    GetDiff --> GetDescription[Get PR Description]
    GetDescription --> GetCommits[Get Commit Messages]
    GetCommits --> GetLabels[Get Existing Labels]

    GetLabels --> ProcessDiff[Process Diff<br/>with Token Management]
    ProcessDiff --> CheckSize{Compressed<br/>or Full?}

    CheckSize -->|Full| FullContext[Use Full Context<br/>with Extra Lines]
    CheckSize -->|Compressed| CompressedContext[Use Compressed Diff<br/>Priority Files Only]

    FullContext --> BuildPrompt[Build Review Prompt]
    CompressedContext --> BuildPrompt

    BuildPrompt --> AddInstructions[Add Custom Instructions<br/>from Config]
    AddInstructions --> CallAI[Call AI Handler]

    CallAI --> ParseResponse[Parse JSON Response]
    ParseResponse --> ValidateResponse{Valid<br/>Format?}

    ValidateResponse -->|No| RetryParse[Retry Parsing<br/>or Use Defaults]
    ValidateResponse -->|Yes| FormatReview[Format Review Comment]

    RetryParse --> FormatReview
    FormatReview --> CheckInline{Publish Inline<br/>Comments?}

    CheckInline -->|Yes| CreateInline[Create Inline Comments]
    CheckInline -->|No| PublishMain[Publish Main Comment]

    CreateInline --> PublishMain
    PublishMain --> CheckLabels{Add<br/>Labels?}

    CheckLabels -->|Yes| PublishLabels[Publish Labels]
    CheckLabels -->|No| Complete([Complete])

    PublishLabels --> Complete

    style BuildPrompt fill:#9370DB
    style CallAI fill:#FFD700
    style Complete fill:#90EE90
```

## PR Description Tool Flow

```mermaid
flowchart TB
    Start([/describe command]) --> Initialize[Initialize PRDescription]
    Initialize --> FetchPR[Fetch PR Details]

    FetchPR --> GetFiles[Get Changed Files]
    GetFiles --> CheckExisting{Existing<br/>Description?}

    CheckExisting -->|Yes| ExtractUser[Extract User Description]
    CheckExisting -->|No| NoUser[No User Description]

    ExtractUser --> ProcessFiles[Process Files<br/>Language Analysis]
    NoUser --> ProcessFiles

    ProcessFiles --> CheckLarge{Large PR<br/>Multiple Calls?}

    CheckLarge -->|Yes| MultipleAI[Multiple AI Calls<br/>for File Groups]
    CheckLarge -->|No| SingleAI[Single AI Call]

    MultipleAI --> CollectSummaries[Collect File Summaries]
    CollectSummaries --> FinalSummary[Final Summary Call]
    SingleAI --> GenerateComponents[Generate PR Components]
    FinalSummary --> GenerateComponents

    GenerateComponents --> Title[Generate Title]
    Title --> Type[Determine PR Type]
    Type --> Summary[Generate Summary]
    Summary --> Walkthrough[Generate Walkthrough]
    Walkthrough --> Labels[Suggest Labels]

    Labels --> FormatMarkdown[Format as Markdown]
    FormatMarkdown --> PreserveUser{Preserve User<br/>Description?}

    PreserveUser -->|Yes| CombineDescriptions[Combine User + AI]
    PreserveUser -->|No| UseAI[Use AI Only]

    CombineDescriptions --> PublishDescription[Publish Description<br/>to PR]
    UseAI --> PublishDescription

    PublishDescription --> Complete([Complete])

    style CheckLarge fill:#FFD700
    style MultipleAI fill:#FFA500
    style PublishDescription fill:#90EE90
```

## Code Suggestions Tool Flow

```mermaid
flowchart TB
    Start([/improve command]) --> Initialize[Initialize PRCodeSuggestions]
    Initialize --> FetchPR[Fetch PR Details]

    FetchPR --> GetDiff[Get Diff Files]
    GetDiff --> FilterFiles[Filter Files<br/>Ignore test/generated]

    FilterFiles --> ProcessByFile[Process Files Individually<br/>or in Groups]
    ProcessByFile --> BuildContext[Build Context for Each File]

    BuildContext --> AddMetadata[Add Metadata:<br/>Language, Patterns,<br/>Best Practices]

    AddMetadata --> CallAI[Call AI for Suggestions]
    CallAI --> ParseSuggestions[Parse Suggestions JSON]

    ParseSuggestions --> ValidateSuggestions{Valid<br/>Format?}
    ValidateSuggestions -->|No| TryFix[Try Fix JSON]
    ValidateSuggestions -->|Yes| RankSuggestions[Rank by Importance]

    TryFix --> CheckFixed{Fixed?}
    CheckFixed -->|Yes| RankSuggestions
    CheckFixed -->|No| UsePartial[Use Partial Results]

    UsePartial --> RankSuggestions
    RankSuggestions --> FilterDuplicates[Filter Duplicates]

    FilterDuplicates --> CheckFormat{Output<br/>Format?}

    CheckFormat -->|Inline| CreateInlineSuggestions[Create Inline Comments<br/>with Code Blocks]
    CheckFormat -->|Summary| CreateSummary[Create Summary Comment]

    CreateInlineSuggestions --> CheckTracking{Enable<br/>Tracking?}
    CreateSummary --> CheckTracking

    CheckTracking -->|Yes| AddTrackingIDs[Add Tracking IDs<br/>to Suggestions]
    CheckTracking -->|No| Publish[Publish Suggestions]

    AddTrackingIDs --> StoreSuggestions[Store in Database<br/>for Tracking]
    StoreSuggestions --> Publish

    Publish --> CheckChat{Enable<br/>Chat?}
    CheckChat -->|Yes| EnableReply[Enable Reply Buttons]
    CheckChat -->|No| Complete([Complete])

    EnableReply --> Complete

    style CallAI fill:#9370DB
    style RankSuggestions fill:#FFD700
    style Publish fill:#90EE90
```

## Ask Questions Tool Flow

```mermaid
flowchart TB
    Start([/ask command]) --> ParseQuestion[Parse User Question]
    ParseQuestion --> FetchPR[Fetch PR Context]

    FetchPR --> GetDiff[Get PR Diff]
    GetDiff --> GetDescription[Get Description]
    GetDescription --> GetComments[Get Existing Comments]

    GetComments --> BuildContext[Build Context:<br/>Diff + Description +<br/>Question]

    BuildContext --> CheckQuestionType{Question<br/>Type?}

    CheckQuestionType -->|General| GeneralContext[Use Full PR Context]
    CheckQuestionType -->|Specific File| FileContext[Focus on Specific File]
    CheckQuestionType -->|Code Line| LineContext[Focus on Code Lines]

    GeneralContext --> PreparePrompt[Prepare Question Prompt]
    FileContext --> PreparePrompt
    LineContext --> PreparePrompt

    PreparePrompt --> CallAI[Call AI Handler]
    CallAI --> ParseAnswer[Parse Answer]

    ParseAnswer --> FormatAnswer[Format Answer<br/>as Markdown]
    FormatAnswer --> AddReferences[Add Code References]

    AddReferences --> PublishAnswer[Publish as Comment]
    PublishAnswer --> Complete([Complete])

    style CheckQuestionType fill:#FFD700
    style CallAI fill:#9370DB
    style Complete fill:#90EE90
```

## Line Questions Tool Flow

```mermaid
sequenceDiagram
    participant User
    participant Platform as Git Platform
    participant Tool as PR_LineQuestions
    participant GitProvider
    participant AIHandler

    User->>Platform: Add comment on line<br/>/ask_line question
    Platform->>Tool: Trigger with comment ID

    Tool->>GitProvider: get_comment_body(comment_id)
    GitProvider-->>Tool: Comment text + question

    Tool->>GitProvider: get_line_context(file, line_number)
    GitProvider-->>Tool: File content + surrounding lines

    Tool->>Tool: Build context:<br/>- File content<br/>- Line numbers<br/>- Question

    Tool->>AIHandler: chat_completion(prompt)
    AIHandler-->>Tool: Answer

    Tool->>Tool: Format answer with<br/>code references

    Tool->>GitProvider: reply_to_comment(comment_id, answer)
    GitProvider->>Platform: Post reply
    Platform-->>User: Show answer in thread
```

## Similar Issue Search Flow

```mermaid
flowchart TB
    Start([/similar_issue command]) --> Initialize[Initialize PRSimilarIssue]
    Initialize --> CheckVectorDB{Vector DB<br/>Configured?}

    CheckVectorDB -->|No| Error[Return Error:<br/>Vector DB Required]
    CheckVectorDB -->|Yes| GetPRData[Get PR Data]

    GetPRData --> ExtractText[Extract Text:<br/>Title + Description +<br/>Key Code Changes]

    ExtractText --> GenerateEmbedding[Generate Embedding<br/>via AI Model]
    GenerateEmbedding --> QueryVectorDB[Query Vector Database:<br/>Pinecone/LanceDB/Qdrant]

    QueryVectorDB --> GetResults[Get Top N Similar Items]
    GetResults --> FilterResults[Filter by:<br/>Similarity Score,<br/>Status,<br/>Time Range]

    FilterResults --> CheckResults{Found<br/>Results?}

    CheckResults -->|No| NoResults[Return No Results Found]
    CheckResults -->|Yes| RankResults[Rank by Relevance]

    RankResults --> FormatOutput[Format Output:<br/>Links + Summaries]
    FormatOutput --> PublishResults[Publish as Comment]

    PublishResults --> Complete([Complete])
    NoResults --> Complete
    Error --> End([End])

    style CheckVectorDB fill:#FFD700
    style QueryVectorDB fill:#9370DB
    style Complete fill:#90EE90
```

## Tool Configuration

```mermaid
graph TB
    subgraph "Tool Configurations"
        subgraph "PR Reviewer Config"
            ReviewPrompts[Prompts:<br/>pr_reviewer_prompts.toml]
            ReviewSettings[Settings:<br/>review categories,<br/>severity levels,<br/>inline comments]
        end

        subgraph "PR Description Config"
            DescPrompts[Prompts:<br/>pr_description_prompts.toml]
            DescSettings[Settings:<br/>max_ai_calls,<br/>include_walkthrough,<br/>enable_labels]
        end

        subgraph "Code Suggestions Config"
            SuggPrompts[Prompts:<br/>code_suggestions/]
            SuggSettings[Settings:<br/>num_suggestions,<br/>rank_method,<br/>enable_tracking]
        end

        subgraph "Questions Config"
            QuestPrompts[Prompts:<br/>pr_questions_prompts.toml<br/>pr_line_questions_prompts.toml]
            QuestSettings[Settings:<br/>max_context_lines]
        end
    end

    subgraph "Base Configuration"
        BaseConfig[configuration.toml]
        Secrets[.secrets.toml]
    end

    BaseConfig --> ReviewSettings
    BaseConfig --> DescSettings
    BaseConfig --> SuggSettings
    BaseConfig --> QuestSettings

    Secrets --> ReviewSettings
    Secrets --> DescSettings

    style BaseConfig fill:#9370DB
    style ReviewPrompts fill:#87CEEB
```

## Tool Execution Context

```mermaid
flowchart LR
    Start([Tool Execution]) --> LoadConfig[Load Configuration]
    LoadConfig --> CreateProvider[Create Git Provider]
    CreateProvider --> CreateAIHandler[Create AI Handler]

    CreateAIHandler --> SetContext[Set Execution Context:<br/>PR URL, Args,<br/>User Settings]

    SetContext --> ValidateAccess[Validate Access:<br/>Permissions,<br/>Rate Limits]

    ValidateAccess --> ExecuteTool[Execute Tool Logic]
    ExecuteTool --> CleanupResources[Cleanup Resources:<br/>Close connections,<br/>Clear cache]

    CleanupResources --> LogMetrics[Log Metrics:<br/>Duration,<br/>Tokens used,<br/>Success/Failure]

    LogMetrics --> Return([Return Result])

    style SetContext fill:#FFD700
    style ExecuteTool fill:#9370DB
    style Return fill:#90EE90
```
