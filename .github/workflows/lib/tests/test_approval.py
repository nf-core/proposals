import pytest
import math
from unittest.mock import Mock, patch, MagicMock
from approval import ApprovalManager


class TestApprovalManager:
    def setup_method(self):
        """Setup for each test method"""
        self.mock_token = "fake_token"
        self.mock_org = "test-org"
        self.mock_repo = "test-repo"
        self.mock_issue_number = 123

        # Mock GitHub objects
        self.mock_github = Mock()
        self.mock_repository = Mock()
        self.mock_issue = Mock()

        # Setup the mock hierarchy
        self.mock_github.get_repo.return_value = self.mock_repository
        self.mock_repository.get_issue.return_value = self.mock_issue

    @patch('approval.Github')
    def test_constructor(self, mock_github_class):
        """Test ApprovalManager initialization"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)

        mock_github_class.assert_called_with(self.mock_token)
        self.mock_github.get_repo.assert_called_with(f"{self.mock_org}/{self.mock_repo}")
        self.mock_repository.get_issue.assert_called_with(self.mock_issue_number)

        assert manager.org == self.mock_org
        assert manager.repo == self.mock_repo
        assert manager.issue_number == self.mock_issue_number
        assert manager.core_team_members == []
        assert manager.maintainer_team_members == []
        assert manager.comments == []
        assert isinstance(manager.core_approvals, set)
        assert isinstance(manager.maintainer_approvals, set)
        assert isinstance(manager.core_rejections, set)
        assert isinstance(manager.maintainer_rejections, set)
        assert manager.awaiting_core == []
        assert manager.awaiting_maintainers == []

    def test_format_user_list_empty(self):
        """Test formatting empty user list"""
        with patch('approval.Github'):
            manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
            result = manager.format_user_list([])
            assert result == "-"

    def test_format_user_list_single(self):
        """Test formatting single user list"""
        with patch('approval.Github'):
            manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
            result = manager.format_user_list(["user1"])
            assert result == "[@user1](https://github.com/user1)"

    def test_format_user_list_multiple(self):
        """Test formatting multiple users list"""
        with patch('approval.Github'):
            manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
            result = manager.format_user_list(["user1", "user2"])
            assert result == "[@user1](https://github.com/user1), [@user2](https://github.com/user2)"

    @patch('approval.Github')
    def test_get_team_members_success(self, mock_github_class):
        """Test successful team member fetching"""
        mock_github_class.return_value = self.mock_github

        # Setup mocks
        mock_org = Mock()
        mock_team = Mock()
        mock_members = [Mock(login="user1"), Mock(login="user2"), Mock(login="user3")]

        self.mock_github.get_organization.return_value = mock_org
        mock_org.get_team_by_slug.return_value = mock_team
        mock_team.get_members.return_value = mock_members

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        result = manager.get_team_members("core")

        self.mock_github.get_organization.assert_called_with(self.mock_org)
        mock_org.get_team_by_slug.assert_called_with("core")
        assert result == ["user1", "user2", "user3"]

    @patch('approval.Github')
    def test_get_team_members_error(self, mock_github_class):
        """Test team member fetching with error"""
        mock_github_class.return_value = self.mock_github

        self.mock_github.get_organization.side_effect = Exception("API Error")

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)

        with pytest.raises(Exception, match="API Error"):
            manager.get_team_members("core")

    @patch('approval.Github')
    def test_update_issue_status_approved(self, mock_github_class):
        """Test updating issue status to approved"""
        mock_github_class.return_value = self.mock_github

        # Setup existing labels
        mock_label1 = Mock()
        mock_label1.name = "bug"
        mock_label2 = Mock()
        mock_label2.name = "proposed"
        mock_label3 = Mock()
        mock_label3.name = "enhancement"

        self.mock_issue.labels = [mock_label1, mock_label2, mock_label3]

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.update_issue_status("✅ Approved")

        self.mock_issue.set_labels.assert_called_with("bug", "enhancement", "accepted")

    @patch('approval.Github')
    def test_update_issue_status_rejected(self, mock_github_class):
        """Test updating issue status to rejected"""
        mock_github_class.return_value = self.mock_github

        # Setup existing labels
        mock_label1 = Mock()
        mock_label1.name = "bug"
        mock_label2 = Mock()
        mock_label2.name = "accepted"

        self.mock_issue.labels = [mock_label1, mock_label2]

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.update_issue_status("❌ Rejected")

        self.mock_issue.set_labels.assert_called_with("bug", "turned-down")

    @patch('approval.Github')
    def test_update_status_comment_create_new(self, mock_github_class):
        """Test creating new status comment"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.comments = []  # No existing comments

        status_body = "## Approval status: New status"
        manager.update_status_comment(status_body)

        self.mock_issue.create_comment.assert_called_with(status_body)

    @patch('approval.Github')
    def test_update_status_comment_update_existing(self, mock_github_class):
        """Test updating existing status comment"""
        mock_github_class.return_value = self.mock_github

        existing_comment = Mock()
        existing_comment.body = "## Approval status: Old status"

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.comments = [existing_comment]

        status_body = "## Approval status: New status"
        manager.update_status_comment(status_body)

        existing_comment.edit.assert_called_with(status_body)

    @patch('approval.Github')
    def test_update_status_comment_no_change(self, mock_github_class, capfd):
        """Test not updating status comment when content is same"""
        mock_github_class.return_value = self.mock_github

        status_body = "## Approval status: Same status"
        existing_comment = Mock()
        existing_comment.body = status_body

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.comments = [existing_comment]

        manager.update_status_comment(status_body)

        existing_comment.edit.assert_not_called()
        self.mock_issue.create_comment.assert_not_called()

        captured = capfd.readouterr()
        assert "Status comment already up to date" in captured.out

    @patch('approval.Github')
    def test_process_comments_core_approvals(self, mock_github_class):
        """Test processing core member approvals"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2", "core3"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Setup mock comments
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/approve"

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/approve this looks good"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        assert "core1" in manager.core_approvals
        assert "core2" in manager.core_approvals
        assert manager.awaiting_core == ["core3"]

    @patch('approval.Github')
    def test_process_comments_maintainer_approvals(self, mock_github_class):
        """Test processing maintainer approvals"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2", "core3"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Setup mock comments
        comment1 = Mock()
        comment1.user.login = "maintainer1"
        comment1.body = "/approve"

        comment2 = Mock()
        comment2.user.login = "maintainer2"
        comment2.body = "This is great\n/approve"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        assert "maintainer1" in manager.maintainer_approvals
        assert "maintainer2" in manager.maintainer_approvals
        assert manager.awaiting_maintainers == []

    @patch('approval.Github')
    def test_process_comments_core_rejections(self, mock_github_class):
        """Test processing core member rejections"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2", "core3"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Setup mock comments
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/reject"

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/reject needs more work"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        assert "core1" in manager.core_rejections
        assert "core2" in manager.core_rejections
        assert manager.awaiting_core == ["core3"]

    @patch('approval.Github')
    def test_process_comments_ignore_non_team_members(self, mock_github_class):
        """Test ignoring comments from non-team members"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2"]
        manager.maintainer_team_members = ["maintainer1"]

        # Setup mock comments from external users
        comment1 = Mock()
        comment1.user.login = "external_user"
        comment1.body = "/approve"

        comment2 = Mock()
        comment2.user.login = "another_user"
        comment2.body = "/reject"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        assert len(manager.core_approvals) == 0
        assert len(manager.maintainer_approvals) == 0
        assert len(manager.core_rejections) == 0
        assert len(manager.maintainer_rejections) == 0

    @patch('approval.Github')
    def test_process_comments_case_insensitive(self, mock_github_class):
        """Test case-insensitive approve/reject commands"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Setup mock comments with various cases
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/APPROVE"

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/Reject"

        comment3 = Mock()
        comment3.user.login = "maintainer1"
        comment3.body = "/approve"

        comment4 = Mock()
        comment4.user.login = "maintainer2"
        comment4.body = "/REJECT"

        manager.comments = [comment1, comment2, comment3, comment4]
        manager.process_comments()

        assert "core1" in manager.core_approvals
        assert "core2" in manager.core_rejections
        assert "maintainer1" in manager.maintainer_approvals
        assert "maintainer2" in manager.maintainer_rejections

    @patch('approval.Github')
    def test_process_comments_line_start_only(self, mock_github_class):
        """Test that commands only work at start of line"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Setup mock comments
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "I think we should /approve this"  # should be ignored

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/approve"  # should be processed

        comment3 = Mock()
        comment3.user.login = "maintainer1"
        comment3.body = "Please /reject this change"  # should be ignored

        comment4 = Mock()
        comment4.user.login = "maintainer2"
        comment4.body = "/reject"  # should be processed

        manager.comments = [comment1, comment2, comment3, comment4]
        manager.process_comments()

        assert "core1" not in manager.core_approvals
        assert "core2" in manager.core_approvals
        assert "maintainer1" not in manager.maintainer_rejections
        assert "maintainer2" in manager.maintainer_rejections

    @patch('approval.Github')
    def test_process_comments_multiple_commands_same_comment(self, mock_github_class):
        """Test multiple commands within same comment (last wins)"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1"]
        manager.maintainer_team_members = ["maintainer1"]

        # Setup mock comments
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/approve\n/reject\n/approve"

        comment2 = Mock()
        comment2.user.login = "maintainer1"
        comment2.body = "/reject\n/approve"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        # Core1 should be approved (last command in comment)
        assert "core1" in manager.core_approvals
        assert "core1" not in manager.core_rejections

        # Maintainer1 should be approved (last command in comment)
        assert "maintainer1" in manager.maintainer_approvals
        assert "maintainer1" not in manager.maintainer_rejections

    @patch('approval.Github')
    def test_pipeline_approval_scenarios(self, mock_github_class):
        """Test pipeline approval scenarios"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2", "core3"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        # Test 2 core members approval
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/approve"

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/approve"

        manager.comments = [comment1, comment2]
        manager.process_comments()

        assert len(manager.core_approvals) == 2
        # Pipeline approval logic: 2 core OR 1 core + 1 maintainer
        is_approved = (len(manager.core_approvals) >= 2 or
                    (len(manager.core_approvals) >= 1 and len(manager.maintainer_approvals) >= 1))
        assert is_approved is True

    @patch('approval.Github')
    def test_rfc_approval_scenarios(self, mock_github_class):
        """Test RFC approval scenarios with quorum"""
        mock_github_class.return_value = self.mock_github

        manager = ApprovalManager(self.mock_token, self.mock_org, self.mock_repo, self.mock_issue_number)
        manager.core_team_members = ["core1", "core2", "core3", "core4", "core5"]
        manager.maintainer_team_members = ["maintainer1", "maintainer2"]

        quorum = math.ceil(len(manager.core_team_members) / 2)  # 3 for 5 members

        # Test with quorum
        comment1 = Mock()
        comment1.user.login = "core1"
        comment1.body = "/approve"

        comment2 = Mock()
        comment2.user.login = "core2"
        comment2.body = "/approve"

        comment3 = Mock()
        comment3.user.login = "core3"
        comment3.body = "/approve"

        manager.comments = [comment1, comment2, comment3]
        manager.process_comments()

        assert len(manager.core_approvals) == 3
        assert len(manager.core_approvals) >= quorum

    def test_quorum_calculation(self):
        """Test quorum calculation for different team sizes"""
        # Test different team sizes
        assert math.ceil(1 / 2) == 1  # 1 member needs 1 approval
        assert math.ceil(2 / 2) == 1  # 2 members need 1 approval
        assert math.ceil(3 / 2) == 2  # 3 members need 2 approvals
        assert math.ceil(4 / 2) == 2  # 4 members need 2 approvals
        assert math.ceil(5 / 2) == 3  # 5 members need 3 approvals
        assert math.ceil(6 / 2) == 3  # 6 members need 3 approvals
        assert math.ceil(7 / 2) == 4  # 7 members need 4 approvals
