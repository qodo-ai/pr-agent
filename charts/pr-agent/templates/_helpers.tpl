{{/*
Expand the name of the chart.
*/}}
{{- define "pr-agent.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "pr-agent.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "pr-agent.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pr-agent.labels" -}}
helm.sh/chart: {{ include "pr-agent.chart" . }}
{{ include "pr-agent.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pr-agent.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pr-agent.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "pr-agent.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "pr-agent.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Generate the deployment command based on deployment mode
*/}}
{{- define "pr-agent.command" -}}
{{- if eq .Values.deploymentMode "github_app" }}
- python
- -m
- gunicorn
- -k
- uvicorn.workers.UvicornWorker
- -c
- pr_agent/servers/gunicorn_config.py
- --forwarded-allow-ips
- "*"
- pr_agent.servers.github_app:app
{{- else if eq .Values.deploymentMode "gitlab_webhook" }}
- python
- pr_agent/servers/gitlab_webhook.py
{{- else if eq .Values.deploymentMode "bitbucket_app" }}
- python
- pr_agent/servers/bitbucket_app.py
{{- else if eq .Values.deploymentMode "gitea_app" }}
- python
- -m
- gunicorn
- -k
- uvicorn.workers.UvicornWorker
- -c
- pr_agent/servers/gunicorn_config.py
- pr_agent.servers.gitea_app:app
{{- else if eq .Values.deploymentMode "azure_devops_webhook" }}
- python
- pr_agent/servers/azuredevops_server_webhook.py
{{- else if eq .Values.deploymentMode "bitbucket_server_webhook" }}
- python
- pr_agent/servers/bitbucket_server_webhook.py
{{- else }}
{{- fail (printf "Unknown deployment mode: %s" .Values.deploymentMode) }}
{{- end }}
{{- end }}

{{/*
Generate Docker image with tag
*/}}
{{- define "pr-agent.image" -}}
{{- printf "%s:%s" .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) }}
{{- end }}

{{/*
Generate environment variables for PR-Agent configuration
*/}}
{{- define "pr-agent.configEnvVars" -}}
{{- range $key, $value := .Values.config }}
- name: CONFIG__{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
{{- end }}
{{- if .Values.pr_reviewer }}
{{- range $key, $value := .Values.pr_reviewer }}
- name: PR_REVIEWER__{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}
{{- if .Values.pr_description }}
{{- range $key, $value := .Values.pr_description }}
- name: PR_DESCRIPTION__{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}
{{- if .Values.pr_code_suggestions }}
{{- range $key, $value := .Values.pr_code_suggestions }}
- name: PR_CODE_SUGGESTIONS__{{ $key | upper | replace "-" "_" }}
  value: {{ $value | quote }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Generate secret environment variables
*/}}
{{- define "pr-agent.secretEnvVars" -}}
{{- if .Values.secrets.openai_key }}
- name: OPENAI_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: openai-key
{{- end }}
{{- if .Values.secrets.github_token }}
- name: GITHUB_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: github-token
{{- end }}
{{- if .Values.secrets.github_webhook_secret }}
- name: GITHUB_WEBHOOK_SECRET
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: github-webhook-secret
{{- end }}
{{- if .Values.secrets.github_app_id }}
- name: GITHUB_APP_ID
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: github-app-id
{{- end }}
{{- if .Values.secrets.github_private_key }}
- name: GITHUB_PRIVATE_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: github-private-key
{{- end }}
{{- if .Values.secrets.gitlab_token }}
- name: GITLAB_TOKEN
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: gitlab-token
{{- end }}
{{- if .Values.secrets.anthropic_key }}
- name: ANTHROPIC_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: anthropic-key
{{- end }}
{{- if .Values.secrets.google_ai_studio_gemini_api_key }}
- name: GOOGLE_AI_STUDIO_GEMINI_API_KEY
  valueFrom:
    secretKeyRef:
      name: {{ include "pr-agent.fullname" . }}-secrets
      key: google-ai-studio-gemini-api-key
{{- end }}
{{- end }} 