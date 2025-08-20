const ApprovalManager = require("./approval.js");

// Mock GitHub API
const mockGithub = {
  request: jest.fn(),
  paginate: jest.fn(),
  rest: {
    issues: {
      listComments: jest.fn(),
      update: jest.fn(),
      updateComment: jest.fn(),
      createComment: jest.fn(),
    },
  },
};

describe("ApprovalManager", () => {
  let approvalManager;
  const mockOrg = "test-org";
  const mockRepo = "test-repo";
  const mockIssueNumber = 123;

  beforeEach(() => {
    jest.clearAllMocks();
    approvalManager = new ApprovalManager(mockGithub, mockOrg, mockRepo, mockIssueNumber);
  });

  describe("constructor", () => {
    it("should initialize with correct properties", () => {
      expect(approvalManager.github).toBe(mockGithub);
      expect(approvalManager.org).toBe(mockOrg);
      expect(approvalManager.repo).toBe(mockRepo);
      expect(approvalManager.issueNumber).toBe(mockIssueNumber);
      expect(approvalManager.coreTeamMembers).toEqual([]);
      expect(approvalManager.maintainerTeamMembers).toEqual([]);
      expect(approvalManager.comments).toEqual([]);
      expect(approvalManager.coreApprovals).toBeInstanceOf(Set);
      expect(approvalManager.maintainerApprovals).toBeInstanceOf(Set);
      expect(approvalManager.coreRejections).toBeInstanceOf(Set);
      expect(approvalManager.maintainerRejections).toBeInstanceOf(Set);
      expect(approvalManager.awaitingCore).toEqual([]);
      expect(approvalManager.awaitingMaintainers).toEqual([]);
    });
  });

  describe("formatUserList", () => {
    it("should format empty array correctly", () => {
      expect(approvalManager.formatUserList([])).toBe("-");
    });

    it("should format single user correctly", () => {
      expect(approvalManager.formatUserList(["user1"])).toBe("[@user1](https://github.com/user1)");
    });

    it("should format multiple users correctly", () => {
      expect(approvalManager.formatUserList(["user1", "user2"])).toBe(
        "[@user1](https://github.com/user1), [@user2](https://github.com/user2)",
      );
    });
  });

  describe("getTeamMembers", () => {
    it("should fetch team members successfully", async () => {
      const mockMembers = [{ login: "user1" }, { login: "user2" }, { login: "user3" }];

      mockGithub.request.mockResolvedValue({ data: mockMembers });

      const result = await approvalManager.getTeamMembers("core");

      expect(mockGithub.request).toHaveBeenCalledWith("GET /orgs/{org}/teams/{team_slug}/members", {
        org: mockOrg,
        team_slug: "core",
        per_page: 100,
      });
      expect(result).toEqual(["user1", "user2", "user3"]);
    });

    it("should handle API errors", async () => {
      const error = new Error("API Error");
      mockGithub.request.mockRejectedValue(error);

      await expect(approvalManager.getTeamMembers("core")).rejects.toThrow("API Error");
    });
  });

  describe("initialize", () => {
    it("should initialize with team members and comments", async () => {
      const mockCoreMembers = [{ login: "core1" }, { login: "core2" }];
      const mockMaintainerMembers = [{ login: "maintainer1" }, { login: "maintainer2" }];
      const mockComments = [
        { id: 1, user: { login: "core1" }, body: "/approve" },
        { id: 2, user: { login: "maintainer1" }, body: "/reject" },
      ];

      mockGithub.request
        .mockResolvedValueOnce({ data: mockCoreMembers })
        .mockResolvedValueOnce({ data: mockMaintainerMembers });

      mockGithub.paginate.mockResolvedValue(mockComments);

      const result = await approvalManager.initialize();

      expect(result).toBe(approvalManager);
      expect(approvalManager.coreTeamMembers).toEqual(["core1", "core2"]);
      expect(approvalManager.maintainerTeamMembers).toEqual(["maintainer1", "maintainer2"]);
      expect(approvalManager.comments).toEqual(mockComments);
    });
  });

  describe("updateIssueStatus", () => {
    it("should add accepted label for approved status", async () => {
      await approvalManager.updateIssueStatus("✅ Approved");

      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["accepted"],
      });
    });

    it("should add turned-down label for rejected status", async () => {
      await approvalManager.updateIssueStatus("❌ Rejected");

      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["turned-down"],
      });
    });

    it("should add timed-out label for timed out status", async () => {
      await approvalManager.updateIssueStatus("⏰ Timed Out");

      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["timed-out"],
      });
    });

    it("should add proposed label for pending status", async () => {
      await approvalManager.updateIssueStatus("🕐 Pending");

      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["proposed"],
      });
    });
  });

  describe("updateStatusComment", () => {
    it("should update existing status comment if content changed", async () => {
      const existingComment = { id: 1, body: "## Approval status: Old status" };
      approvalManager.comments = [existingComment];
      const newStatusBody = "## Approval status: New status";

      await approvalManager.updateStatusComment(newStatusBody);

      expect(mockGithub.rest.issues.updateComment).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        comment_id: 1,
        body: newStatusBody,
      });
    });

    it("should not update existing status comment if content is the same", async () => {
      const statusBody = "## Approval status: Same status";
      const existingComment = { id: 1, body: statusBody };
      approvalManager.comments = [existingComment];

      await approvalManager.updateStatusComment(statusBody);

      expect(mockGithub.rest.issues.updateComment).not.toHaveBeenCalled();
    });

    it("should create new status comment if none exists", async () => {
      approvalManager.comments = [];
      const statusBody = "## Approval status: New status";

      await approvalManager.updateStatusComment(statusBody);

      expect(mockGithub.rest.issues.createComment).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        body: statusBody,
      });
    });
  });

  describe("processComments", () => {
    beforeEach(() => {
      approvalManager.coreTeamMembers = ["core1", "core2", "core3"];
      approvalManager.maintainerTeamMembers = ["maintainer1", "maintainer2"];
    });

    it("should process core member approvals", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core2" }, body: "/approve this looks good" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.has("core1")).toBe(true);
      expect(approvalManager.coreApprovals.has("core2")).toBe(true);
      expect(approvalManager.awaitingCore).toEqual(["core3"]);
    });

    it("should process maintainer approvals", () => {
      approvalManager.comments = [
        { user: { login: "maintainer1" }, body: "/approve" },
        { user: { login: "maintainer2" }, body: "This is great\n/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.maintainerApprovals.has("maintainer1")).toBe(true);
      expect(approvalManager.maintainerApprovals.has("maintainer2")).toBe(true);
      expect(approvalManager.awaitingMaintainers).toEqual([]);
    });

    it("should process core member rejections", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/reject" },
        { user: { login: "core2" }, body: "/reject needs more work" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreRejections.has("core1")).toBe(true);
      expect(approvalManager.coreRejections.has("core2")).toBe(true);
      expect(approvalManager.awaitingCore).toEqual(["core3"]);
    });

    it("should process maintainer rejections", () => {
      approvalManager.comments = [
        { user: { login: "maintainer1" }, body: "/reject" },
        { user: { login: "maintainer2" }, body: "Issues found\n/reject" },
      ];

      approvalManager.processComments();

      expect(approvalManager.maintainerRejections.has("maintainer1")).toBe(true);
      expect(approvalManager.maintainerRejections.has("maintainer2")).toBe(true);
      expect(approvalManager.awaitingMaintainers).toEqual([]);
    });

    it("should ignore comments from non-team members", () => {
      approvalManager.comments = [
        { user: { login: "external_user" }, body: "/approve" },
        { user: { login: "another_user" }, body: "/reject" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.maintainerApprovals.size).toBe(0);
      expect(approvalManager.coreRejections.size).toBe(0);
      expect(approvalManager.maintainerRejections.size).toBe(0);
    });

    it("should handle case-insensitive approve/reject commands", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/APPROVE" },
        { user: { login: "core2" }, body: "/Reject" },
        { user: { login: "maintainer1" }, body: "/approve" },
        { user: { login: "maintainer2" }, body: "/REJECT" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.has("core1")).toBe(true);
      expect(approvalManager.coreRejections.has("core2")).toBe(true);
      expect(approvalManager.maintainerApprovals.has("maintainer1")).toBe(true);
      expect(approvalManager.maintainerRejections.has("maintainer2")).toBe(true);
    });

    it("should only process commands at start of line", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "I think we should /approve this" }, // should be ignored
        { user: { login: "core2" }, body: "/approve" }, // should be processed
        { user: { login: "maintainer1" }, body: "Please /reject this change" }, // should be ignored
        { user: { login: "maintainer2" }, body: "/reject" }, // should be processed
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.has("core1")).toBe(false);
      expect(approvalManager.coreApprovals.has("core2")).toBe(true);
      expect(approvalManager.maintainerRejections.has("maintainer1")).toBe(false);
      expect(approvalManager.maintainerRejections.has("maintainer2")).toBe(true);
    });

    it("should handle multiple commands from same user (last command per comment wins)", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core1" }, body: "/reject" },
      ];

      approvalManager.processComments();

      // The user should be in rejections, not approvals (last comment wins)
      expect(approvalManager.coreApprovals.has("core1")).toBe(false);
      expect(approvalManager.coreRejections.has("core1")).toBe(true);
    });

    it("should handle multiple commands within same comment (last command wins)", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve\n/reject\n/approve" },
        { user: { login: "maintainer1" }, body: "/reject\n/approve" },
      ];

      approvalManager.processComments();

      // Core1 should be approved (last command in comment)
      expect(approvalManager.coreApprovals.has("core1")).toBe(true);
      expect(approvalManager.coreRejections.has("core1")).toBe(false);

      // Maintainer1 should be approved (last command in comment)
      expect(approvalManager.maintainerApprovals.has("maintainer1")).toBe(true);
      expect(approvalManager.maintainerRejections.has("maintainer1")).toBe(false);
    });

    it("should reset approval sets before processing", () => {
      // Set initial state
      approvalManager.coreApprovals.add("core1");
      approvalManager.maintainerApprovals.add("maintainer1");

      // No comments this time
      approvalManager.comments = [];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.maintainerApprovals.size).toBe(0);
    });
  });

  describe("Pipeline Proposal Scenarios", () => {
    beforeEach(() => {
      approvalManager.coreTeamMembers = ["core1", "core2", "core3"];
      approvalManager.maintainerTeamMembers = ["maintainer1", "maintainer2"];
    });

    it("should approve with 2 core members", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core2" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(2);
      // Pipeline approval logic: 2 core OR 1 core + 1 maintainer
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);
      expect(isApproved).toBe(true);
    });

    it("should approve with 1 core + 1 maintainer", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "maintainer1" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(1);
      expect(approvalManager.maintainerApprovals.size).toBe(1);
      // Pipeline approval logic: 2 core OR 1 core + 1 maintainer
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);
      expect(isApproved).toBe(true);
    });

    it("should not approve with only 1 core member", () => {
      approvalManager.comments = [{ user: { login: "core1" }, body: "/approve" }];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(1);
      expect(approvalManager.maintainerApprovals.size).toBe(0);
      // Pipeline approval logic: 2 core OR 1 core + 1 maintainer
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);
      expect(isApproved).toBe(false);
    });

    it("should not approve with only maintainers", () => {
      approvalManager.comments = [
        { user: { login: "maintainer1" }, body: "/approve" },
        { user: { login: "maintainer2" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.maintainerApprovals.size).toBe(2);
      // Pipeline approval logic: 2 core OR 1 core + 1 maintainer
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);
      expect(isApproved).toBe(false);
    });
  });

  describe("RFC Proposal Scenarios", () => {
    beforeEach(() => {
      approvalManager.coreTeamMembers = ["core1", "core2", "core3", "core4", "core5"];
      approvalManager.maintainerTeamMembers = ["maintainer1", "maintainer2"];
    });

    it("should approve RFC with quorum of core members", () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core2" }, body: "/approve" },
        { user: { login: "core3" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(3);
      expect(approvalManager.coreApprovals.size >= quorum).toBe(true);
    });

    it("should not approve RFC without quorum", () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core2" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(approvalManager.coreApprovals.size >= quorum).toBe(false);
    });

    it("should calculate quorum correctly for different team sizes", () => {
      // Test different team sizes
      expect(Math.ceil(1 / 2)).toBe(1); // 1 member needs 1 approval
      expect(Math.ceil(2 / 2)).toBe(1); // 2 members need 1 approval
      expect(Math.ceil(3 / 2)).toBe(2); // 3 members need 2 approvals
      expect(Math.ceil(4 / 2)).toBe(2); // 4 members need 2 approvals
      expect(Math.ceil(5 / 2)).toBe(3); // 5 members need 3 approvals
      expect(Math.ceil(6 / 2)).toBe(3); // 6 members need 3 approvals
      expect(Math.ceil(7 / 2)).toBe(4); // 7 members need 4 approvals
    });

    it("should ignore maintainer approvals for RFC (core team only)", () => {
      approvalManager.comments = [
        { user: { login: "core1" }, body: "/approve" },
        { user: { login: "core2" }, body: "/approve" },
        { user: { login: "maintainer1" }, body: "/approve" },
        { user: { login: "maintainer2" }, body: "/approve" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(approvalManager.maintainerApprovals.size).toBe(2);

      // For RFC, only core approvals matter
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members
      expect(approvalManager.coreApprovals.size >= quorum).toBe(false);
    });
  });

  describe("Edge Cases and Error Handling", () => {
    it("should handle empty comments array", () => {
      approvalManager.coreTeamMembers = ["core1", "core2"];
      approvalManager.maintainerTeamMembers = ["maintainer1"];
      approvalManager.comments = [];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.maintainerApprovals.size).toBe(0);
      expect(approvalManager.awaitingCore).toEqual(["core1", "core2"]);
      expect(approvalManager.awaitingMaintainers).toEqual(["maintainer1"]);
    });

    it("should handle comments with no body", () => {
      approvalManager.coreTeamMembers = ["core1"];
      approvalManager.comments = [
        { user: { login: "core1" }, body: null },
        { user: { login: "core1" }, body: undefined },
        { user: { login: "core1" }, body: "" },
      ];

      expect(() => approvalManager.processComments()).not.toThrow();
    });

    it("should handle malformed comment bodies", () => {
      approvalManager.coreTeamMembers = ["core1"];
      approvalManager.comments = [
        { user: { login: "core1" }, body: "//approve" }, // should not match (double slash)
        { user: { login: "core1" }, body: "approve" }, // should not match (no slash)
        { user: { login: "core1" }, body: "text/approve" }, // should not match (no space before slash)
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.coreRejections.size).toBe(0);
    });

    it("should handle comments with mixed line endings", () => {
      approvalManager.coreTeamMembers = ["core1", "core2"];
      approvalManager.comments = [
        { user: { login: "core1" }, body: "Some text\r/approve\rMore text" },
        { user: { login: "core2" }, body: "Some text\n/reject\nMore text" },
      ];

      approvalManager.processComments();

      expect(approvalManager.coreApprovals.has("core1")).toBe(true);
      expect(approvalManager.coreRejections.has("core2")).toBe(true);
    });

    it("should handle user being in both core and maintainer teams", () => {
      approvalManager.coreTeamMembers = ["user1", "core2"];
      approvalManager.maintainerTeamMembers = ["user1", "maintainer2"]; // user1 is in both
      approvalManager.comments = [{ user: { login: "user1" }, body: "/approve" }];

      approvalManager.processComments();

      // User should be counted as core member (checked first)
      expect(approvalManager.coreApprovals.has("user1")).toBe(true);
      expect(approvalManager.maintainerApprovals.has("user1")).toBe(false);
    });
  });
});
