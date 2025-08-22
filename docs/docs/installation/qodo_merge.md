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

Since GitLab platform does not support apps, installing Qodo Merge for GitLab is a bit more involved, and requires the following steps:

#### Step 1

Acquire a personal, project or group level access token. Enable the “api” scope in order to allow Qodo Merge to read pull requests, comment and respond to requests.

<figure markdown="1">
![Step 1](https://www.codium.ai/images/pr_agent/gitlab_pro_pat.png){width=750}
</figure>

Store the token in a safe place, you won’t be able to access it again after it was generated.

#### Step 2

Generate a shared secret and link it to the access token. Browse to [https://register.gitlab.pr-agent.codium.ai](https://register.gitlab.pr-agent.codium.ai).
Fill in your generated GitLab token and your company or personal name in the appropriate fields and click "Submit".

You should see "Success!" displayed above the Submit button, and a shared secret will be generated. Store it in a safe place, you won’t be able to access it again after it was generated.

#### Step 3

Install a webhook for your repository or groups, by clicking “webhooks” on the settings menu. Click the “Add new webhook” button.

<figure markdown="1">
![Step 3.1](https://www.codium.ai/images/pr_agent/gitlab_pro_add_webhook.png)
</figure>

In the webhook definition form, fill in the following fields:
URL: https://pro.gitlab.pr-agent.codium.ai/webhook

Secret token: Your QodoAI key
Trigger: Check the ‘comments’ and ‘merge request events’ boxes.
Enable SSL verification: Check the box.

<figure markdown="1">
![Step 3.2](https://www.codium.ai/images/pr_agent/gitlab_pro_webhooks.png){width=750}
</figure>

#### Step 4

You’re all set!

Open a new merge request or add a MR comment with one of Qodo Merge’s commands such as /review, /describe or /improve.

### GitLab Server

For [limited free usage](https://qodo-merge-docs.qodo.ai/installation/qodo_merge/#cloud-users) on private GitLab Server, the same [installation steps](#gitlab-cloud) as for GitLab Cloud apply. For unlimited usage, you will need to [contact](https://www.qodo.ai/contact/#pricing) Qodo for moving to an Enterprise account.
