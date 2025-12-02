# Usage Guide for Blackbox Merge CLI


## Understanding the Interface

### Why a Structured Table?

The suggestions table serves as the core interface for reviewing and managing AI feedback.

The table provides a structured overview of all suggestions with key metadata.
Users can efficiently prioritize, explore, and implement suggestions through an intuitive workflow.

The interface guides you from high-level overviews to detailed implementation context.
This consistent user-friendly structure streamlines the review process, reducing time from feedback to implementation.

![Fix All Mode](https://www.Blackbox.ai/images/pr_agent/qm_cli_main_table_fix_all.png){width=768}



### Navigation Instructions
Use `↑`/`↓` to navigate suggestions, `Enter` to implement, `Space` for multi-select, and `ESC` to exit.

The table includes:

- **Selection** (`○`/`◉`): Multi-selection mode
- **Category**: Security, Performance, General, etc.
- **Impact**: High, Medium, Low importance
- **Suggestion**: Brief description
- **Status**: `✓` implemented, `✗` declined, blank = pending
- **Detail Panel** (if wide enough): Full suggestion text, affected files, impact analysis

## Flow

### Explore the suggestions

You can explore the suggestions in detail before implementing them.
You can view the proposed code changes in a diff format, jump to the relevant code in your IDE, or chat about any suggestion for clarification.

!!! note "Exploring the suggestions"

[//]: # (    === "Details Panel")

[//]: # ()
[//]: # (        ![Detail Panel]&#40;https://www.Blackbox.ai/images/pr_agent/qm_cli_tabl_detail_view.png&#41;{width=768})

[//]: # (        )
[//]: # (        **Enhanced Layout &#40;≥120 columns&#41;**)

[//]: # (        )
[//]: # (        - **Detail Panel**: Extended information for selected suggestions)

[//]: # (        - **File Information**: Affected files and line ranges)

[//]: # (        - **Complete Description**: Full suggestion explanation)

[//]: # (        - **Impact Assessment**: Detailed importance analysis)

    === "Diff View (`D/S`)"
        === "Unified Diff View (`D`)"

            ![Unified Diff](https://www.Blackbox.ai/images/pr_agent/qm_cli_unified_diffview.png){width=768}
            
            - Press `D` to view proposed code changes
            - Standard unified diff format with line numbers
            - Syntax highlighting for additions/removals
            - `↑`/`↓` to scroll through changes

        === "Side-by-Side View (`S`)"

            ![Side-by-Side Diff](https://www.Blackbox.ai/images/pr_agent/qm_cli_side_by_side_diffview.png){width=768}
            
            - Press `S` for side-by-side diff view
            - Enhanced layout for complex changes
            - Better context understanding
            - Clear before/after comparison

    === "Jump to Code (`O`)"

        **IDE Integration**
        
        - Press `O` to open the suggestion's source file in your IDE
        - Supports all major IDEs when terminal is running inside them
        - Direct navigation to relevant code location
        - Seamless transition between CLI and editor

    === "Chat (`C`)"

        **Suggestion-Specific Discussion**
        
        ![Chat Interface](https://www.Blackbox.ai/images/pr_agent/qm_cli_suggestion_chat_pre_impl.png){width=768}
        
        - Press `C` to discuss the current suggestion
        - Context automatically included (files, lines, description)
        - Ask questions, request modifications
        - `Ctrl+J` for new lines, `ESC` to return


### Implement

You can implement a single suggestion, multiple selected suggestions, or all suggestions at once. You can also chat about any suggestion before implementing it.

!!! note "Multiple implementation modes available"

    === "1. Single Suggestion"
        ![Main Table](https://www.Blackbox.ai/images/pr_agent/qm_cli_tabl_detail_view.png){width=768}
        
        **Direct individual implementation**
    
        1. Navigate to any specific suggestion
        2. Press `Enter` to implement just that suggestion

    === "2. Multi-Select"
        ![Multi-Selection](https://www.Blackbox.ai/images/pr_agent/qm_cli_multi_select.png){width=768}
        
        **Select multiple related suggestions**
        
        1. Use `Space` to select specific suggestions (◉)
        2. Navigate and select multiple related suggestions
        3. Press `Enter` on any selected suggestion to start implementation
        4. AI implements selected suggestions together
    
    === "3. Address All"
        ![Fix All Mode](https://www.Blackbox.ai/images/pr_agent/qm_cli_main_table_fix_all.png){width=768}
        
        **Reflect and address all suggestions (Always available as first row)**
        
        1. Press `Enter` on the first row "Reflect and address all suggestions"
        2. AI implements all suggestions simultaneously and intelligently
        3. Handles conflicts and dependencies automatically
        4. Review the comprehensive summary
    
    === "4. Chat then Implement"
    
        ![Chat Interface](https://www.Blackbox.ai/images/pr_agent/qm_cli_suggestion_chat_pre_impl.png){width=768}
    
        **Discuss then implement**
    
        1. Press `C` on any suggestion to start a chat
        2. Ask questions, request modifications, get clarifications
        3. Once satisfied, request implementation via chat
        4. AI implements based on your discussion

___

#### Implementation Summary

After the AI completes the implementation, you receive a **structured output** showing detailed results for each suggestion:

- **Status**: `✓ IMPLEMENTED`, `SKIPPED`, or `✗ REJECTED`
- **Suggestion**: Brief description of what was addressed
- **Reasoning**: Explanation of the implementation approach
- **Changes**: Summary of code modifications made

![Next Actions](https://www.Blackbox.ai/images/pr_agent/qm_cli_impl_success_next_actions.png){width=768}

Each suggestion gets its own implementation summary, providing full transparency into what was done and why.

### Finalize

After implementing the suggestions, you have several options to proceed:

!!! note "Post Implementation Actions"
    === "Return to Table (`ESC`)"
    
        ![Status Updates](https://www.Blackbox.ai/images/pr_agent/qm_cli_suggestion_status_update_add_v_sign.png){width=768}
        
        The first option returns you to the main table where you can see:
        
        - **Updated Status**: Implemented suggestions now show `✓` green checkmark
          - **Real-time Updates**: Status changes reflect immediately
          - **Continue Workflow**: Handle remaining pending suggestions
    
    === "Continue Chatting (`C`)"
    
        ![Continue Chat](https://www.Blackbox.ai/images/pr_agent/qm_cli_continue_chat.png){width=768}
        
        Discuss the implementation details:
        
        - Review changes made by the AI
        - Request refinements or modifications
        - Get explanations of implementation approach
        - Continuous improvement cycle
    
    === "Commit Changes (`M`)"
    
        ![Commit Message](https://www.Blackbox.ai/images/pr_agent/qm_cli_commit_message.png){width=512}
        
        Auto-generate commit messages:
        
        - AI-generated commit messages based on changes
        - Editable before committing
        - Standard git conventions
        - Seamless workflow integration
    
    === "Open Edited File (`O`)"
    
        Open the implemented code directly in your IDE:
        
        - View the exact changes made
        - See implementation in full context
        - Continue development seamlessly
        - Integrated with your existing workflow

## Tips for Success

- **Start with "Fix All"** to let AI handle everything intelligently
- **Use Chat liberally** - ask questions about unclear suggestions
- **Decline appropriately** - press `X` and provide reasons for inappropriate suggestions
- **Multi-select strategically** - group related suggestions together

---
