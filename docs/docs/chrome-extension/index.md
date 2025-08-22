`Platforms supported: GitHub Cloud`

[Qodo Merge Chrome extension](https://chromewebstore.google.com/detail/pr-agent-chrome-extension/ephlnjeghhogofkifjloamocljapahnl){:target="_blank"} is a collection of tools that integrates seamlessly with your GitHub environment, aiming to enhance your Git usage experience, and providing AI-powered capabilities to your PRs.

With a single-click installation you will gain access to a context-aware chat on your pull requests code, a toolbar extension with multiple AI feedbacks, Qodo Merge filters, and additional abilities.

The extension is powered by top code models like GPT-5. All the extension's features are free to use on public repositories.

For private repositories, you will need to install [Qodo Merge](https://github.com/apps/qodo-merge-pro){:target="_blank"} in addition to the extension.
For a demonstration of how to install Qodo Merge and use it with the Chrome extension, please refer to the tutorial video at the provided [link](https://codium.ai/images/pr_agent/private_repos.mp4){:target="_blank"}.

<img src="https://codium.ai/images/pr_agent/PR-AgentChat.gif" width="768">

### Supported browsers

The extension is supported on all Chromium-based browsers, including Google Chrome, Arc, Opera, Brave, and Microsoft Edge.

## Features

### PR chat

The PR-Chat feature allows to freely chat with your PR code, within your GitHub environment.
It will seamlessly use the PR as context to your chat session, and provide AI-powered feedback.

To enable private chat, simply install the Qodo Merge Chrome extension. After installation, each PR's file-changed tab will include a chat box, where you may ask questions about your code.
This chat session is **private**, and won't be visible to other users.

All open-source repositories are supported.
For private repositories, you will also need to install Qodo Merge. After installation, make sure to open at least one new PR to fully register your organization. Once done, you can chat with both new and existing PRs across all installed repositories.

#### Context-aware PR chat

Qodo Merge constructs a comprehensive context for each pull request, incorporating the PR description, commit messages, and code changes with extended dynamic context. This contextual information, along with additional PR-related data, forms the foundation for an AI-powered chat session. The agent then leverages this rich context to provide intelligent, tailored responses to user inquiries about the pull request.

<img src="https://codium.ai/images/pr_agent/pr_chat_1.png" width="768">
<img src="https://codium.ai/images/pr_agent/pr_chat_2.png" width="768">

### Toolbar extension

With Qodo Merge Chrome extension, it's [easier than ever](https://www.youtube.com/watch?v=gT5tli7X4H4) to interactively configure and experiment with the different tools and configuration options.

For private repositories, after you found the setup that works for you, you can also easily export it as a persistent configuration file, and use it for automatic commands.

<img src="https://codium.ai/images/pr_agent/toolbar1.png" width="512">

<img src="https://codium.ai/images/pr_agent/toolbar2.png" width="512">

### Qodo Merge filters

Qodo Merge filters is a sidepanel option. that allows you to filter different message in the conversation tab.

For example, you can choose to present only message from Qodo Merge, or filter those messages, focusing only on user's comments.

<img src="https://codium.ai/images/pr_agent/pr_agent_filters1.png" width="256">

<img src="https://codium.ai/images/pr_agent/pr_agent_filters2.png" width="256">

### Enhanced code suggestions

Qodo Merge Chrome extension adds the following capabilities to code suggestions tool's comments:

- Auto-expand the table when you are viewing a code block, to avoid clipping.
- Adding a "quote-and-reply" button, that enables to address and comment on a specific suggestion (for example, asking the author to fix the issue)

<img src="https://codium.ai/images/pr_agent/chrome_extension_code_suggestion1.png" width="512">

<img src="https://codium.ai/images/pr_agent/chrome_extension_code_suggestion2.png" width="512">

## Data Privacy

We take your code's security and privacy seriously:

- The Chrome extension will not send your code to any external servers.
- For private repositories, we will first validate the user's identity and permissions. After authentication, we generate responses using the existing Qodo Merge integration.

## Options and Configurations

### Accessing the Options Page

To access the options page for the Qodo Merge Chrome extension:

1. Find the extension icon in your Chrome toolbar (usually in the top-right corner of your browser)
2. Right-click on the extension icon
3. Select "Options" from the context menu that appears

Alternatively, you can access the options page directly using this URL:

[chrome-extension://ephlnjeghhogofkifjloamocljapahnl/options.html](chrome-extension://ephlnjeghhogofkifjloamocljapahnl/options.html)

<img src="https://codium.ai/images/pr_agent/chrome_ext_options.png" width="256">

### Configuration Options

<img src="https://codium.ai/images/pr_agent/chrome_ext_settings_page.png" width="512">

#### API Base Host

For single-tenant customers, you can configure the extension to communicate directly with your company's Qodo Merge server instance.

To set this up:

- Enter your organization's Qodo Merge API endpoint in the "API Base Host" field
- This endpoint should be provided by your Qodo DevOps Team

*Note: The extension does not send your code to the server, but only triggers your previously installed Qodo Merge application.*

#### Interface Options

You can customize the extension's interface by:

- Toggling the "Show Qodo Merge Toolbar" option
- When disabled, the toolbar will not appear in your Github comment bar

Remember to click "Save Settings" after making any changes.