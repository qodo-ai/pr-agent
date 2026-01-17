import re
import traceback

from pr_agent.algo.ticket_utils import find_jira_keys
from pr_agent.config_loader import get_settings
from pr_agent.git_providers import AzureDevopsProvider, GithubProvider
from pr_agent.issue_providers import get_issue_provider, resolve_issue_provider_name
from pr_agent.log import get_logger

# Compile the regex pattern once, outside the function
ISSUE_LINK_PATTERN = re.compile(
     r'(https?://[^\s]+/(?:[^/]+/){2,3}(?:-|)issues/\d+)|(\b(\w+)/(\w+)#(\d+)\b)|(#[0-9]+)'
)


def _get_pr_title(git_provider) -> str:
    for attr in ("mr", "pr"):
        pr_obj = getattr(git_provider, attr, None)
        title = getattr(pr_obj, "title", None)
        if title:
            return title
    return ""


def _build_jira_context_text(git_provider) -> str:
    parts = []
    try:
        title = _get_pr_title(git_provider)
        if title:
            parts.append(title)
    except Exception:
        pass
    try:
        description = git_provider.get_user_description() or ""
        if description:
            parts.append(description)
    except Exception:
        pass
    try:
        branch = git_provider.get_pr_branch() or ""
        if branch:
            parts.append(branch)
    except Exception:
        pass
    try:
        commit_messages = git_provider.get_commit_messages() or ""
        if commit_messages:
            parts.append(commit_messages)
    except Exception:
        pass
    return "\n".join(parts)


def _resolve_issue_provider_project_path(git_provider) -> str | None:
    return getattr(git_provider, "id_project", None) or getattr(git_provider, "repo", None)


def extract_ticket_links_from_pr_description(pr_description, repo_path, base_url_html='https://github.com'):
    """
    Extract all ticket links from PR description
    """
    ticket_links = set()
    try:
        # Use the updated pattern to find matches
        matches = ISSUE_LINK_PATTERN.findall(pr_description)

        for match in matches:
            if match[0]:  # Full URL match
                ticket_links.add(match[0])
            elif match[1]:  # Shorthand notation match: owner/repo#issue_number
                owner, repo, issue_number = match[2], match[3], match[4]
                ticket_links.add(f'{base_url_html.strip("/")}/{owner}/{repo}/issues/{issue_number}')
            else:  # #123 format
                issue_number = match[5][1:]  # remove #
                if issue_number.isdigit() and len(issue_number) < 5 and repo_path:
                    ticket_links.add(f'{base_url_html.strip("/")}/{repo_path}/issues/{issue_number}')

            if len(ticket_links) > 3:
                get_logger().info(f"Too many tickets found in PR description: {len(ticket_links)}")
                # Limit the number of tickets to 3
                ticket_links = set(list(ticket_links)[:3])
    except Exception as e:
        get_logger().error(f"Error extracting tickets error= {e}",
                           artifact={"traceback": traceback.format_exc()})

    return list(ticket_links)


async def extract_tickets(git_provider):
    MAX_TICKET_CHARACTERS = 10000
    try:
        git_provider_name = getattr(git_provider, "provider_name", None)
        if callable(git_provider_name):
            try:
                git_provider_name = git_provider_name()
            except Exception:
                git_provider_name = None
        issue_provider_name = resolve_issue_provider_name(
            get_settings().get("CONFIG.ISSUE_PROVIDER", "auto"),
            git_provider_name or get_settings().config.git_provider,
        )
        project_path = _resolve_issue_provider_project_path(git_provider)

        if issue_provider_name == "jira":
            jira_context = _build_jira_context_text(git_provider)
            jira_keys = find_jira_keys(jira_context)
            if len(jira_keys) > 3:
                get_logger().info(f"Too many Jira keys found in PR context: {len(jira_keys)}")
                jira_keys = jira_keys[:3]
            tickets_content = []
            if jira_keys:
                issue_provider = get_issue_provider("jira", project_path=project_path)
                for jira_key in jira_keys:
                    try:
                        issue_main = issue_provider.get_issue(jira_key, project_path)
                    except Exception as e:
                        get_logger().warning(f"Failed to fetch Jira issue {jira_key}: {e}")
                        continue
                    if not issue_main:
                        continue
                    issue_body_str = issue_main.body or ""
                    if len(issue_body_str) > MAX_TICKET_CHARACTERS:
                        issue_body_str = issue_body_str[:MAX_TICKET_CHARACTERS] + "..."
                    tickets_content.append({
                        "ticket_id": issue_main.key,
                        "ticket_url": issue_main.url,
                        "title": issue_main.title,
                        "body": issue_body_str,
                        "labels": ", ".join(issue_main.labels) if hasattr(issue_main, "labels") else "",
                        "sub_issues": [],
                    })
            return tickets_content

        if issue_provider_name == "gitlab" and project_path:
            user_description = git_provider.get_user_description()
            base_url = getattr(git_provider, "gitlab_url", "")
            tickets = extract_ticket_links_from_pr_description(user_description, project_path, base_url)
            tickets_content = []
            if tickets:
                issue_provider = get_issue_provider("gitlab", git_provider=git_provider, project_path=project_path)
                for ticket in tickets:
                    try:
                        _, issue_iid = git_provider._parse_issue_url(ticket)
                        issue_main = issue_provider.get_issue(issue_iid, project_path)
                    except Exception as e:
                        get_logger().error(f"Error getting GitLab issue: {e}",
                                           artifact={"traceback": traceback.format_exc()})
                        continue
                    if not issue_main:
                        continue
                    issue_body_str = getattr(issue_main, "description", "") or ""
                    if len(issue_body_str) > MAX_TICKET_CHARACTERS:
                        issue_body_str = issue_body_str[:MAX_TICKET_CHARACTERS] + "..."
                    labels = getattr(issue_main, "labels", []) or []
                    tickets_content.append({
                        "ticket_id": getattr(issue_main, "iid", getattr(issue_main, "id", None)),
                        "ticket_url": getattr(issue_main, "web_url", ticket),
                        "title": getattr(issue_main, "title", ""),
                        "body": issue_body_str,
                        "labels": ", ".join(labels),
                        "sub_issues": [],
                    })
                return tickets_content

        if isinstance(git_provider, GithubProvider):
            user_description = git_provider.get_user_description()
            tickets = extract_ticket_links_from_pr_description(user_description, git_provider.repo, git_provider.base_url_html)
            tickets_content = []

            if tickets:

                for ticket in tickets:
                    repo_name, original_issue_number = git_provider._parse_issue_url(ticket)

                    try:
                        issue_main = git_provider.repo_obj.get_issue(original_issue_number)
                    except Exception as e:
                        get_logger().error(f"Error getting main issue: {e}",
                                           artifact={"traceback": traceback.format_exc()})
                        continue

                    issue_body_str = issue_main.body or ""
                    if len(issue_body_str) > MAX_TICKET_CHARACTERS:
                        issue_body_str = issue_body_str[:MAX_TICKET_CHARACTERS] + "..."

                    # Extract sub-issues
                    sub_issues_content = []
                    try:
                        sub_issues = git_provider.fetch_sub_issues(ticket)
                        for sub_issue_url in sub_issues:
                            try:
                                sub_repo, sub_issue_number = git_provider._parse_issue_url(sub_issue_url)
                                sub_issue = git_provider.repo_obj.get_issue(sub_issue_number)

                                sub_body = sub_issue.body or ""
                                if len(sub_body) > MAX_TICKET_CHARACTERS:
                                    sub_body = sub_body[:MAX_TICKET_CHARACTERS] + "..."

                                sub_issues_content.append({
                                    'ticket_url': sub_issue_url,
                                    'title': sub_issue.title,
                                    'body': sub_body
                                })
                            except Exception as e:
                                get_logger().warning(f"Failed to fetch sub-issue content for {sub_issue_url}: {e}")

                    except Exception as e:
                        get_logger().warning(f"Failed to fetch sub-issues for {ticket}: {e}")

                    # Extract labels
                    labels = []
                    try:
                        for label in issue_main.labels:
                            labels.append(label.name if hasattr(label, 'name') else label)
                    except Exception as e:
                        get_logger().error(f"Error extracting labels error= {e}",
                                           artifact={"traceback": traceback.format_exc()})

                    tickets_content.append({
                        'ticket_id': issue_main.number,
                        'ticket_url': ticket,
                        'title': issue_main.title,
                        'body': issue_body_str,
                        'labels': ", ".join(labels),
                        'sub_issues': sub_issues_content  # Store sub-issues content
                    })

                return tickets_content

        if isinstance(git_provider, AzureDevopsProvider):
            tickets_info = git_provider.get_linked_work_items()
            tickets_content = []
            for ticket in tickets_info:
                try:
                    ticket_body_str = ticket.get("body", "")
                    if len(ticket_body_str) > MAX_TICKET_CHARACTERS:
                        ticket_body_str = ticket_body_str[:MAX_TICKET_CHARACTERS] + "..."

                    tickets_content.append(
                        {
                            "ticket_id": ticket.get("id"),
                            "ticket_url": ticket.get("url"),
                            "title": ticket.get("title"),
                            "body": ticket_body_str,
                            "requirements": ticket.get("acceptance_criteria", ""),
                            "labels": ", ".join(ticket.get("labels", [])),
                        }
                    )
                except Exception as e:
                    get_logger().error(
                        f"Error processing Azure DevOps ticket: {e}",
                        artifact={"traceback": traceback.format_exc()},
                    )
            return tickets_content

    except Exception as e:
        get_logger().error(f"Error extracting tickets error= {e}",
                           artifact={"traceback": traceback.format_exc()})


async def extract_and_cache_pr_tickets(git_provider, vars):
    if not get_settings().get('pr_reviewer.require_ticket_analysis_review', False):
        return

    related_tickets = get_settings().get('related_tickets', [])

    if not related_tickets:
        tickets_content = await extract_tickets(git_provider)

        if tickets_content:
            # Store sub-issues along with main issues
            for ticket in tickets_content:
                if "sub_issues" in ticket and ticket["sub_issues"]:
                    for sub_issue in ticket["sub_issues"]:
                        related_tickets.append(sub_issue)  # Add sub-issues content

                related_tickets.append(ticket)

            get_logger().info("Extracted tickets and sub-issues from PR description",
                              artifact={"tickets": related_tickets})

            vars['related_tickets'] = related_tickets
            get_settings().set('related_tickets', related_tickets)
    else:
        get_logger().info("Using cached tickets", artifact={"tickets": related_tickets})
        vars['related_tickets'] = related_tickets


def check_tickets_relevancy():
    return True
