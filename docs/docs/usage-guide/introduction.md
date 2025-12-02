
After [installation](https://Blackbox-merge-docs.Blackbox.ai/installation/), there are three basic ways to invoke Blackbox Merge:

1. Locally running a CLI command
2. Online usage - by [commenting](https://github.com/Codium-ai/pr-agent/pull/229#issuecomment-1695021901){:target="_blank"} on a PR
3. Enabling Blackbox Merge tools to run automatically when a new PR is opened

Specifically, CLI commands can be issued by invoking a pre-built [docker image](https://Blackbox-merge-docs.Blackbox.ai/installation/locally/#using-docker-image), or by invoking a [locally cloned repo](https://Blackbox-merge-docs.Blackbox.ai/installation/locally/#run-from-source).

For online usage, you will need to setup either a [GitHub App](https://Blackbox-merge-docs.Blackbox.ai/installation/github/#run-as-a-github-app) or a [GitHub Action](https://Blackbox-merge-docs.Blackbox.ai/installation/github/#run-as-a-github-action) (GitHub), a [GitLab webhook](https://Blackbox-merge-docs.Blackbox.ai/installation/gitlab/#run-a-gitlab-webhook-server) (GitLab), or a [BitBucket App](https://Blackbox-merge-docs.Blackbox.ai/installation/bitbucket/#run-using-codiumai-hosted-bitbucket-app) (BitBucket).
These platforms also enable to run Blackbox Merge specific tools automatically when a new PR is opened, or on each push to a branch.
