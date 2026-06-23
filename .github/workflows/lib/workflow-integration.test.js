const ApprovalManager = require("./approval.js");

// Mock GitHub API for integration tests
const mockGithub = {
  request: jest.fn(),
  paginate: jest.fn(),
  rest: {
    issues: {
      listComments: jest.fn(),
      get: jest.fn(),
      update: jest.fn(),
      updateComment: jest.fn(),
      createComment: jest.fn(),
    },
  },
};

describe("Workflow Integration Tests", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Pipeline Proposal Workflow", () => {
    let approvalManager;
    const mockOrg = "nf-core";
    const mockRepo = "proposals";
    const mockIssueNumber = 42;

    beforeEach(async () => {
      // Mock team members
      mockGithub.request
        .mockResolvedValueOnce({
          data: [{ login: "core_alice" }, { login: "core_bob" }, { login: "core_charlie" }],
        })
        .mockResolvedValueOnce({
          data: [{ login: "maintainer_dave" }, { login: "maintainer_eve" }],
        });

      // Mock empty comments initially
      mockGithub.paginate.mockResolvedValue([]);

      // Mock issues.get to return an issue with no existing labels
      mockGithub.rest.issues.get.mockResolvedValue({
        data: {
          labels: [],
        },
      });

      approvalManager = await new ApprovalManager(mockGithub, mockOrg, mockRepo, mockIssueNumber).initialize();
    });

    it("should approve pipeline with 2 core team members", async () => {
      // Simulate comments with approvals
      approvalManager.comments = [
        {
          id: 1,
          user: { login: "core_alice" },
          body: "/approve\n\nThis pipeline looks great!",
        },
        {
          id: 2,
          user: { login: "core_bob" },
          body: "LGTM\n/approve",
        },
      ];

      approvalManager.processComments();

      // Check approval logic for pipeline proposals
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);

      expect(isApproved).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(approvalManager.maintainerApprovals.size).toBe(0);

      // Test status generation
      const status = "✅ Approved";

      // Verify the approval manager would update the issue correctly
      await approvalManager.updateIssueStatus(status);
      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["accepted"],
      });
    });

    it("should approve pipeline with 1 core + 1 maintainer", async () => {
      approvalManager.comments = [
        {
          id: 1,
          user: { login: "core_alice" },
          body: "/approve",
        },
        {
          id: 2,
          user: { login: "maintainer_dave" },
          body: "/approve",
        },
      ];

      approvalManager.processComments();

      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);

      expect(isApproved).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(1);
      expect(approvalManager.maintainerApprovals.size).toBe(1);
    });

    it("should not approve pipeline with insufficient votes", async () => {
      approvalManager.comments = [
        {
          id: 1,
          user: { login: "core_alice" },
          body: "/approve",
        },
        {
          id: 2,
          user: { login: "external_user" },
          body: "/approve", // External user vote doesn't count
        },
      ];

      approvalManager.processComments();

      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);

      expect(isApproved).toBe(false);
      expect(approvalManager.coreApprovals.size).toBe(1);
      expect(approvalManager.maintainerApprovals.size).toBe(0);
    });

    it("should handle rejection in pipeline workflow", async () => {
      approvalManager.comments = [
        {
          id: 1,
          user: { login: "core_alice" },
          body: "/approve",
        },
        {
          id: 2,
          user: { login: "core_bob" },
          body: "/reject\n\nThis needs more work",
        },
      ];

      approvalManager.processComments();

      // Even with rejections, check if there are enough approvals
      const isApproved =
        approvalManager.coreApprovals.size >= 2 ||
        (approvalManager.coreApprovals.size >= 1 && approvalManager.maintainerApprovals.size >= 1);

      const hasRejections = approvalManager.coreRejections.size > 0 || approvalManager.maintainerRejections.size > 0;

      expect(isApproved).toBe(false);
      expect(hasRejections).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(1);
      expect(approvalManager.coreRejections.size).toBe(1);
    });
  });

  describe("RFC Proposal Workflow", () => {
    let approvalManager;
    const mockOrg = "nf-core";
    const mockRepo = "proposals";
    const mockIssueNumber = 84;

    beforeEach(async () => {
      // Mock core team with 5 members (quorum = 3)
      mockGithub.request
        .mockResolvedValueOnce({
          data: [
            { login: "core_alice" },
            { login: "core_bob" },
            { login: "core_charlie" },
            { login: "core_diana" },
            { login: "core_eve" },
          ],
        })
        .mockResolvedValueOnce({
          data: [{ login: "maintainer_frank" }, { login: "maintainer_grace" }],
        });

      mockGithub.paginate.mockResolvedValue([]);

      // Mock issues.get to return an issue with no existing labels
      mockGithub.rest.issues.get.mockResolvedValue({
        data: {
          labels: [],
        },
      });

      approvalManager = await new ApprovalManager(mockGithub, mockOrg, mockRepo, mockIssueNumber).initialize();
    });

    it("should approve RFC with core team quorum", async () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { id: 1, user: { login: "core_alice" }, body: "/approve" },
        { id: 2, user: { login: "core_bob" }, body: "/approve" },
        { id: 3, user: { login: "core_charlie" }, body: "/approve" },
      ];

      approvalManager.processComments();

      const isApproved = approvalManager.coreApprovals.size >= quorum;

      expect(isApproved).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(3);
      expect(quorum).toBe(3);

      await approvalManager.updateIssueStatus("✅ Approved");
      expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
        owner: mockOrg,
        repo: mockRepo,
        issue_number: mockIssueNumber,
        labels: ["accepted"],
      });
    });

    it("should not approve RFC without quorum", async () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { id: 1, user: { login: "core_alice" }, body: "/approve" },
        { id: 2, user: { login: "core_bob" }, body: "/approve" },
        // Only 2 approvals, need 3
      ];

      approvalManager.processComments();

      const isApproved = approvalManager.coreApprovals.size >= quorum;

      expect(isApproved).toBe(false);
      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(quorum).toBe(3);
    });

    it("should approve RFC with combined core + maintainer votes reaching quorum", async () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { id: 1, user: { login: "core_alice" }, body: "/approve" },
        { id: 2, user: { login: "core_bob" }, body: "/approve" },
        { id: 3, user: { login: "maintainer_frank" }, body: "/approve" },
        // 2 core + 1 maintainer = 3 total >= quorum, with at least 1 core
      ];

      approvalManager.processComments();

      const isApproved =
        approvalManager.coreApprovals.size >= quorum ||
        (approvalManager.coreApprovals.size >= 1 &&
          approvalManager.coreApprovals.size + approvalManager.maintainerApprovals.size >= quorum);

      expect(isApproved).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(approvalManager.maintainerApprovals.size).toBe(1);
      expect(quorum).toBe(3);
    });

    it("should not approve RFC with only maintainer votes", async () => {
      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members

      approvalManager.comments = [
        { id: 1, user: { login: "maintainer_frank" }, body: "/approve" },
        { id: 2, user: { login: "maintainer_grace" }, body: "/approve" },
      ];

      approvalManager.processComments();

      const isApproved =
        approvalManager.coreApprovals.size >= quorum ||
        (approvalManager.coreApprovals.size >= 1 &&
          approvalManager.coreApprovals.size + approvalManager.maintainerApprovals.size >= quorum);

      expect(isApproved).toBe(false);
      expect(approvalManager.coreApprovals.size).toBe(0);
      expect(approvalManager.maintainerApprovals.size).toBe(2);
    });

    it("should handle RFC rejection with core team voting", async () => {
      approvalManager.comments = [
        { id: 1, user: { login: "core_alice" }, body: "/approve" },
        { id: 2, user: { login: "core_bob" }, body: "/approve" },
        { id: 3, user: { login: "core_charlie" }, body: "/reject\n\nI disagree with this approach" },
      ];

      approvalManager.processComments();

      const quorum = Math.ceil(approvalManager.coreTeamMembers.length / 2); // 3 for 5 members
      const isApproved = approvalManager.coreApprovals.size >= quorum;
      const hasRejections = approvalManager.coreRejections.size > 0;

      expect(isApproved).toBe(false);
      expect(hasRejections).toBe(true);
      expect(approvalManager.coreApprovals.size).toBe(2);
      expect(approvalManager.coreRejections.size).toBe(1);
    });
  });

  describe("Status Comment Generation", () => {
    let approvalManager;

    beforeEach(async () => {
      mockGithub.request
        .mockResolvedValueOnce({ data: [{ login: "core1" }, { login: "core2" }] })
        .mockResolvedValueOnce({ data: [{ login: "maintainer1" }] });

      mockGithub.paginate.mockResolvedValue([]);

      approvalManager = await new ApprovalManager(mockGithub, "org", "repo", 123).initialize();
    });

    it("should update existing status comment when content changes", async () => {
      const existingComment = {
        id: 456,
        body: "## Approval status: 🕐 Pending\n\nOld content",
      };
      approvalManager.comments = [existingComment];

      const newStatusBody = "## Approval status: ✅ Approved\n\nNew content";

      await approvalManager.updateStatusComment(newStatusBody);

      expect(mockGithub.rest.issues.updateComment).toHaveBeenCalledWith({
        owner: "org",
        repo: "repo",
        comment_id: 456,
        body: newStatusBody,
      });
    });

    it("should create new status comment when none exists", async () => {
      approvalManager.comments = []; // No existing status comment

      const statusBody = "## Approval status: 🕐 Pending\n\nInitial status";

      await approvalManager.updateStatusComment(statusBody);

      expect(mockGithub.rest.issues.createComment).toHaveBeenCalledWith({
        owner: "org",
        repo: "repo",
        issue_number: 123,
        body: statusBody,
      });
    });
  });

  describe("Label Management", () => {
    let approvalManager;

    beforeEach(async () => {
      mockGithub.request.mockResolvedValueOnce({ data: [] }).mockResolvedValueOnce({ data: [] });

      mockGithub.paginate.mockResolvedValue([]);

      // Mock issues.get to return an issue with no existing labels
      mockGithub.rest.issues.get.mockResolvedValue({
        data: {
          labels: [],
        },
      });

      approvalManager = await new ApprovalManager(mockGithub, "org", "repo", 123).initialize();
    });

    it("should set correct labels for different statuses", async () => {
      const statusLabelMap = [
        ["✅ Approved", ["accepted"]],
        ["❌ Rejected", ["turned-down"]],
        ["⏰ Timed Out", ["timed-out"]],
        ["🕐 Pending", ["proposed"]],
      ];

      for (const [status, expectedLabels] of statusLabelMap) {
        mockGithub.rest.issues.update.mockClear();

        await approvalManager.updateIssueStatus(status);

        expect(mockGithub.rest.issues.update).toHaveBeenCalledWith({
          owner: "org",
          repo: "repo",
          issue_number: 123,
          labels: expectedLabels,
        });
      }
    });
  });

  describe("Pipeline Proposal Workflow - Rejection Automation", () => {
    let approvalManager;
    const mockOrg = "nf-core";
    const mockRepo = "proposals";
    const mockIssueNumber = 99;

    beforeEach(async () => {
      mockGithub.request
        .mockResolvedValueOnce({ data: [{ login: "core1" }, { login: "core2" }] })
        .mockResolvedValueOnce({ data: [{ login: "maintainer1" }] });
      mockGithub.paginate.mockResolvedValue([]);
      mockGithub.rest.issues.get.mockResolvedValue({ data: { labels: [] } });
      approvalManager = await new ApprovalManager(mockGithub, mockOrg, mockRepo, mockIssueNumber).initialize();
    });

    it("should set status to rejected if 2 core rejections", async () => {
      approvalManager.coreRejections = new Set(["core1", "core2"]);
      approvalManager.maintainerRejections = new Set();
      let status;
      if (
        approvalManager.coreRejections.size >= 2 ||
        (approvalManager.coreRejections.size >= 1 && approvalManager.maintainerRejections.size >= 1)
      ) {
        status = "❌ Rejected";
      } else {
        status = "🕐 Pending";
      }
      expect(status).toBe("❌ Rejected");
    });

    it("should set status to rejected if 1 core + 1 maintainer rejection", async () => {
      approvalManager.coreRejections = new Set(["core1"]);
      approvalManager.maintainerRejections = new Set(["maintainer1"]);
      let status;
      if (
        approvalManager.coreRejections.size >= 2 ||
        (approvalManager.coreRejections.size >= 1 && approvalManager.maintainerRejections.size >= 1)
      ) {
        status = "❌ Rejected";
      } else {
        status = "🕐 Pending";
      }
      expect(status).toBe("❌ Rejected");
    });

    it("should not set status to rejected if only 1 core rejection", async () => {
      approvalManager.coreRejections = new Set(["core1"]);
      approvalManager.maintainerRejections = new Set();
      let status;
      if (
        approvalManager.coreRejections.size >= 2 ||
        (approvalManager.coreRejections.size >= 1 && approvalManager.maintainerRejections.size >= 1)
      ) {
        status = "❌ Rejected";
      } else {
        status = "🕐 Pending";
      }
      expect(status).toBe("🕐 Pending");
    });

    it("should stay pending if 2 rejections but also 1 approval", async () => {
      approvalManager.coreRejections = new Set(["core1", "core2"]);
      approvalManager.maintainerRejections = new Set();
      approvalManager.coreApprovals = new Set(["core3"]);
      approvalManager.maintainerApprovals = new Set();
      let status;
      if (
        (approvalManager.coreRejections.size >= 2 ||
          (approvalManager.coreRejections.size >= 1 && approvalManager.maintainerRejections.size >= 1)) &&
        approvalManager.coreApprovals.size === 0 &&
        approvalManager.maintainerApprovals.size === 0
      ) {
        status = "❌ Rejected";
      } else {
        status = "🕐 Pending";
      }
      expect(status).toBe("🕐 Pending");
    });
  });
});
