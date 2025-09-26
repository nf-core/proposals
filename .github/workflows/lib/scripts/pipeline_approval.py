#!/usr/bin/env python3

import sys
import rich_click as click
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from approval import ApprovalManager


def generate_status_body(approval_manager: ApprovalManager, status: str) -> str:
    """Generate the status body for pipeline approval"""
    core_approvers = list(approval_manager.core_approvals)
    maintainer_approvers = list(approval_manager.maintainer_approvals)
    rejecters = list(approval_manager.core_rejections) + list(approval_manager.maintainer_rejections)
    awaiting_core = list(approval_manager.awaiting_core)
    awaiting_maintainers = list(approval_manager.awaiting_maintainers)

    body = f"## Approval status: {status}\n\n"
    body += "Required approvals: Either 2 core team members OR 1 core team member + 1 maintainer\n\n"

    if (core_approvers or maintainer_approvers or rejecters or
        awaiting_core or awaiting_maintainers):
        body += "|Review&nbsp;Status|Team members|\n|--|--|\n"
        if core_approvers:
            body += f"| ✅&nbsp;Approved (Core) | {approval_manager.format_user_list(core_approvers)} |\n"
        if maintainer_approvers:
            body += f"| ✅&nbsp;Approved (Maintainer) | {approval_manager.format_user_list(maintainer_approvers)} |\n"
        if rejecters:
            body += f"| ❌&nbsp;Rejected | {approval_manager.format_user_list(rejecters)} |\n"
        if awaiting_core:
            body += f"| 🕐&nbsp;Pending (Core) | {approval_manager.format_user_list(awaiting_core)} |\n"
        if awaiting_maintainers:
            body += f"| 🕐&nbsp;Pending (Maintainer) | {approval_manager.format_user_list(awaiting_maintainers)} |\n"

    return body


@click.command()
@click.option('--github-token', required=True, help='GitHub API token')
@click.option('--org', required=True, help='GitHub organization')
@click.option('--repo', required=True, help='GitHub repository')
@click.option('--issue-number', type=int, required=True, help='Issue number')
@click.option('--event-name', required=True, help='GitHub event name')
@click.option('--event-action', help='GitHub event action')
@click.option('--issue-state', help='Issue state')
@click.option('--label-name', help='Label name for label events')
@click.option('--issue-state-reason', help='Issue state reason')
def main(github_token, org, repo, issue_number, event_name, event_action, issue_state, label_name, issue_state_reason):
    """Process pipeline proposal approval automation."""
    print(f"Processing pipeline approval for issue #{issue_number}")

    # Initialize approval manager
    approval_manager = ApprovalManager(github_token, org, repo, issue_number)
    approval_manager.initialize()

    # Ignore comments on closed issues
    if event_name == 'issue_comment' and issue_state == 'closed':
        print('Comment event on closed issue, ignoring.')
        return

    # Handle label changes
    if event_name == 'issues' and event_action in ['labeled', 'unlabeled']:
        if label_name == 'timed-out':
            print('Timed-out label detected, updating status')
            status_body = generate_status_body(approval_manager, '⏰ Timed Out')
            approval_manager.update_status_comment(status_body)
            return

    # Handle new issue creation
    if event_name == 'issues' and event_action == 'opened':
        body = generate_status_body(approval_manager, '🕐 Pending')
        print('Creating initial comment for review status')
        approval_manager.update_status_comment(body)
        approval_manager.update_issue_status('🕐 Pending')
        return

    # Determine status
    status = '🕐 Pending'

    if (event_name == 'issues' and
        event_action == 'closed' and
        issue_state_reason == 'not_planned' and
        (len(approval_manager.core_rejections) > 0 or len(approval_manager.maintainer_rejections) > 0)):
        status = '❌ Rejected'
    elif (len(approval_manager.core_approvals) >= 2 or
        (len(approval_manager.core_approvals) >= 1 and len(approval_manager.maintainer_approvals) >= 1)):
        status = '✅ Approved'

    status_body = generate_status_body(approval_manager, status)
    print('New status body to post:\n', status_body)

    approval_manager.update_status_comment(status_body)
    approval_manager.update_issue_status(status)


if __name__ == "__main__":
    main()
