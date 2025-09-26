#!/usr/bin/env python3

import sys
import rich_click as click
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from approval import ApprovalManager


def generate_status_body(approval_manager: ApprovalManager, status: str) -> str:
    """Generate the status body for SIG approval"""
    required_core_approvals = 2

    approvers = list(approval_manager.core_approvals)
    rejecters = list(approval_manager.core_rejections)
    awaiting = approval_manager.awaiting_core

    body = f"## Approval status: {status}\n\n"
    body += f"SIG proposal requires approvals from {required_core_approvals} core team members.\n\n"
    body += f"Current approvals: {len(approval_manager.core_approvals)}/{required_core_approvals}\n\n"

    if approvers or rejecters or awaiting:
        body += "|Review&nbsp;Status|Core Team members|\n|--|--|\n"
        if approvers:
            body += f"| ✅&nbsp;Approved | {approval_manager.format_user_list(approvers)} |\n"
        if rejecters:
            body += f"| ❌&nbsp;Rejected | {approval_manager.format_user_list(rejecters)} |\n"
        if awaiting:
            body += f"| 🕐&nbsp;Pending | {approval_manager.format_user_list(awaiting)} |\n"

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
    """Process SIG proposal approval automation."""
    print(f"Processing SIG approval for issue #{issue_number}")

    # Initialize approval manager
    approval_manager = ApprovalManager(github_token, org, repo, issue_number)
    approval_manager.initialize()

    # Ignore comments on closed issues
    if event_name == 'issue_comment' and issue_state == 'closed':
        print('Comment event on closed issue, ignoring.')
        return

    required_core_approvals = 2
    print(f"Required core team approvals: {required_core_approvals}")

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
        len(approval_manager.core_rejections) > 0):
        status = '❌ Rejected'
    elif len(approval_manager.core_approvals) >= required_core_approvals:
        status = '✅ Approved'

    status_body = generate_status_body(approval_manager, status)
    print('New status body to post:\n', status_body)

    approval_manager.update_status_comment(status_body)
    approval_manager.update_issue_status(status)


if __name__ == "__main__":
    main()
