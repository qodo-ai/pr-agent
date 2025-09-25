Qodo Merge is a versatile application compatible with GitHub, GitLab, and BitBucket, hosted by QodoAI.
See [here](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) for more details about the benefits of using Qodo Merge.

## Usage and Licensing

### Cloud Users

Non-paying users will enjoy feedback on up to 75 PRs per git organization per month. Above this limit, PRs will not receive feedback until a new month begins. 

For unlimited access, user licenses (seats) are required. Each user requires an individual seat license.
After purchasing seats, the team owner can assign them to specific users through the management portal.

With an assigned seat, users can seamlessly deploy the application across any of their code repositories in a git organization, and receive feedback on all their PRs.

### Enterprise Account

For companies who require an Enterprise account, please [contact](https://www.qodo.ai/contact/#pricing) us to initiate a trial period, and to discuss pricing and licensing options.


## Install Qodo Merge for GitHub

### GitHub Cloud

Qodo Merge for GitHub cloud is available for installation through the [GitHub Marketplace](https://github.com/apps/qodo-merge-pro).

![Qodo Merge](https://codium.ai/images/pr_agent/pr_agent_pro_install.png){width=468}

### GitHub Enterprise Server

To use Qodo Merge on your private GitHub Enterprise Server, you will need to [contact](https://www.qodo.ai/contact/#pricing) Qodo for starting an Enterprise trial.

(Note: The marketplace app is not compatible with GitHub Enterprise Server. Installation requires creating a private GitHub App instead.)

### GitHub Open Source Projects

For open-source projects, Qodo Merge is available for free usage. To install Qodo Merge for your open-source repositories, use the following marketplace [link](https://github.com/marketplace/qodo-merge-pro-for-open-source).

## Install Qodo Merge for Bitbucket

### Bitbucket Cloud

Qodo Merge for Bitbucket Cloud is available for installation through the following [link](https://bitbucket.org/site/addons/authorize?addon_key=d6df813252c37258)

![Qodo Merge](https://qodo.ai/images/pr_agent/pr_agent_pro_bitbucket_install.png){width=468}

### Bitbucket Server

To use Qodo Merge application on your private Bitbucket Server, you will need to contact us for starting an [Enterprise](https://www.qodo.ai/pricing/) trial.

## Install Qodo Merge for GitLab

### GitLab Cloud

Installing Qodo Merge for GitLab uses GitLab's OAuth 2.0 application system and requires the following steps:

#### Step 1: Create a GitLab OAuth 2.0 Application

Create a new OAuth 2.0 application in your GitLab instance:

1. Navigate to your GitLab group or subgroup settings
2. Go to "Applications" in the left sidebar
3. Click on "Add new application"
4. Fill in the application details:
   - **Name**: You can give any name you wish (e.g., "Qodo Merge")
   - **Redirect URI**: `https://register.oauth.app.gitlab.merge.qodo.ai/oauth/callback`
   - **Confidential**: Check this checkbox
   - **Scopes**: Check the "api" scope
   
    <figure markdown="1">
    ![Step 1](https://www.codium.ai/images/pr_agent/gitlab_pro_oauth_app_creation_image.png){width=750}
    </figure>

5. Click "Save application"
6. Copy both the **Application ID** and **Secret** - store them safely as you'll need them for the next step

#### Step 2: Register Your OAuth Application

1. Browse to: <https://register.oauth.app.gitlab.merge.qodo.ai>
2. Fill in the registration form:
   - **Host Address**: Leave empty if using gitlab.com ([for self-hosted GitLab servers](#gitlab-server), enter your GitLab base URL including scheme (e.g., https://gitlab.mycorp-inc.com) without trailing slash. Do not include paths or query strings.
   - **OAuth Application ID**: Enter the Application ID from Step 1
   - **OAuth Application Secret**: Enter the Secret from Step 1 
   
    <figure markdown="1">
    ![Step 2](https://www.codium.ai/images/pr_agent/gitlab_pro_registration_form_image.png){width=750}
    </figure>

3. Click "Submit"

#### Step 3: Authorize the OAuth Application

If all fields show green checkmarks, a redirect popup from GitLab will appear requesting authorization for the OAuth app to access the "api" scope. Click "Authorize" to approve the application.

#### Step 4: Copy the Webhook Secret Token

If the authorization is successful, a message will appear displaying a generated webhook secret token. Copy this token and store it safely - you'll need it for the next step.

#### Step 5: Install Webhooks

Install a webhook for your repository or groups by following these steps:

1. Navigate to your repository or group settings
2. Click "Webhooks" in the settings menu
3. Click the "Add new webhook" button

    <figure markdown="1">
    ![Step 5.1](https://www.codium.ai/images/pr_agent/gitlab_pro_add_webhook.png)
    </figure>

4. In the webhook definition form, fill in the following fields:
   - **URL**: `https://pro.gitlab.pr-agent.codium.ai/webhook`
   - **Secret token**: The webhook secret token generated in Step 4
   - **Trigger**: Check the 'Comments' and 'Merge request events' boxes
   - **Enable SSL verification**: Check this box

    <figure markdown="1">
    ![Step 5.2](https://www.codium.ai/images/pr_agent/gitlab_pro_webhooks.png){width=750}
    </figure>

5. Click "Add webhook"

**Note**: Repeat this webhook installation for each group or repository that is under the group or subgroup where the OAuth 2.0 application was created in Step 1.

#### Step 6: You’re all set!

Open a new merge request or add a MR comment with one of Qodo Merge’s commands such as /review, /describe or /improve.

### GitLab Server

For [limited free usage](https://qodo-merge-docs.qodo.ai/installation/qodo_merge/#cloud-users) on private GitLab Server, the same [installation steps](#gitlab-cloud) as for GitLab Cloud apply, aside from the [Host Address field mentioned in Step 2](#step-2-register-your-oauth-application) (where you fill in the hostname for your GitLab server, such as: https://gitlab.mycorp-inc.com). For unlimited usage, you will need to [contact](https://www.qodo.ai/contact/#pricing) Qodo for moving to an Enterprise account.
