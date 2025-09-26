import re
import os
from typing import Set, List, Optional
from github import Github
from github.Repository import Repository
from github.Issue import Issue


class ApprovalManager:
    def __init__(self, github_token: str, org: str, repo: str, issue_number: int):
        self.github = Github(github_token)
        self.org = org
        self.repo = repo
        self.issue_number = issue_number
        self.repository: Repository = self.github.get_repo(f"{org}/{repo}")
        self.issue: Issue = self.repository.get_issue(issue_number)

        self.core_team_members: List[str] = []
        self.maintainer_team_members: List[str] = []
        self.comments = []
        self.core_approvals: Set[str] = set()
        self.maintainer_approvals: Set[str] = set()
        self.core_rejections: Set[str] = set()
        self.maintainer_rejections: Set[str] = set()
        self.awaiting_core: List[str] = []
        self.awaiting_maintainers: List[str] = []

    def format_user_list(self, users: List[str]) -> str:
        """Helper for list formatting"""
        if not users:
            return "-"
        return ", ".join([f"[@{user}](https://github.com/{user})" for user in users])

    def get_team_members(self, team_slug: str) -> List[str]:
        """Helper to fetch team members"""
        try:
            org = self.github.get_organization(self.org)
            team = org.get_team_by_slug(team_slug)
            members = list(team.get_members())
            print(f"Fetched {len(members)} {team_slug} team members.")
            return [member.login for member in members]
        except Exception as err:
            print(f"Failed to fetch {team_slug} team members: {err}")
            raise err

    def initialize(self):
        """Initialize the manager with team members and comments"""
        # Fetch team members
        self.core_team_members = self.get_team_members("core")
        self.maintainer_team_members = self.get_team_members("maintainers")
        print("Core team members:", self.core_team_members)
        print("Maintainer team members:", self.maintainer_team_members)

        # Fetch comments
        self.comments = list(self.issue.get_comments())

        # Process comments
        self.process_comments()
        return self

    def update_issue_status(self, status: str):
        """Helper to update issue status and labels"""
        # Get current labels
        current_labels = [label.name for label in self.issue.labels]

        # Filter out existing status labels
        status_labels = ["accepted", "turned-down", "timed-out", "proposed"]
        existing_labels = [label for label in current_labels if label not in status_labels]

        # Determine new status label
        status_map = {
            "✅ Approved": "accepted",
            "❌ Rejected": "turned-down",
            "⏰ Timed Out": "timed-out"
        }
        new_status_label = status_map.get(status, "proposed")

        # Combine existing non-status labels with new status label
        updated_labels = existing_labels + [new_status_label]

        # Update labels
        self.issue.set_labels(*updated_labels)

    def update_status_comment(self, status_body: str):
        """Helper to find and update status comment"""
        status_comment = None
        for comment in self.comments:
            if comment.body.startswith("## Approval status:"):
                status_comment = comment
                break

        if status_comment:
            if status_comment.body.strip() == status_body.strip():
                print("Status comment already up to date - no update required.")
            else:
                print("Updating existing status comment.")
                status_comment.edit(status_body)
        else:
            # Fallback: create a new status comment if missing
            self.issue.create_comment(status_body)

    def process_comments(self):
        """Helper to process comments and collect votes"""
        # Reset all approval sets
        self.core_approvals = set()
        self.maintainer_approvals = set()
        self.core_rejections = set()
        self.maintainer_rejections = set()

        for comment in self.comments:
            commenter = comment.user.login
            is_core_member = commenter in self.core_team_members
            is_maintainer = commenter in self.maintainer_team_members

            if not is_core_member and not is_maintainer:
                continue  # Only team members count

            # Skip comments with no body
            if not comment.body:
                continue

            # Count approvals / rejections based on line starting with /approve or /reject
            lines = comment.body.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'^/approve\b', line, re.IGNORECASE):
                    if is_core_member:
                        self.core_approvals.add(commenter)
                        self.core_rejections.discard(commenter)  # Remove any previous rejection
                    elif is_maintainer:
                        self.maintainer_approvals.add(commenter)
                        self.maintainer_rejections.discard(commenter)  # Remove any previous rejection
                elif re.match(r'^/reject\b', line, re.IGNORECASE):
                    if is_core_member:
                        self.core_rejections.add(commenter)
                        self.core_approvals.discard(commenter)  # Remove any previous approval
                    elif is_maintainer:
                        self.maintainer_rejections.add(commenter)
                        self.maintainer_approvals.discard(commenter)  # Remove any previous approval

        # Update awaiting lists
        self.awaiting_core = [
            user for user in self.core_team_members
            if user not in self.core_approvals and user not in self.core_rejections
        ]
        self.awaiting_maintainers = [
            user for user in self.maintainer_team_members
            if user not in self.maintainer_approvals and user not in self.maintainer_rejections
        ]
