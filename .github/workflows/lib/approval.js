class ApprovalManager {
  constructor(github, org, repo, issueNumber) {
    this.github = github;
    this.org = org;
    this.repo = repo;
    this.issueNumber = issueNumber;
    this.coreTeamMembers = [];
    this.maintainerTeamMembers = [];
    this.comments = [];
    this.coreApprovals = new Set();
    this.maintainerApprovals = new Set();
    this.coreRejections = new Set();
    this.maintainerRejections = new Set();
    this.awaitingCore = [];
    this.awaitingMaintainers = [];
  }

  // Helper for list formatting
  formatUserList(users) {
    return users.length ? users.map((u) => `[@${u}](https://github.com/${u})`).join(", ") : "-";
  }

  // Determine the status of a pipeline proposal from durable issue state and
  // votes, rather than from the event that happened to trigger the workflow.
  determinePipelineStatus(issue) {
    const labels = (issue.labels || []).map((label) => (typeof label === "string" ? label : label.name));
    const approvalThresholdReached =
      this.coreApprovals.size >= 2 || (this.coreApprovals.size >= 1 && this.maintainerApprovals.size >= 1);
    const rejectionThresholdReached =
      (this.coreRejections.size >= 2 || (this.coreRejections.size >= 1 && this.maintainerRejections.size >= 1)) &&
      this.coreApprovals.size === 0 &&
      this.maintainerApprovals.size === 0;
    const closedAsRejected =
      issue.state === "closed" &&
      issue.state_reason === "not_planned" &&
      (this.coreRejections.size > 0 || this.maintainerRejections.size > 0);

    if (labels.includes("timed-out")) {
      return "⏰ Timed Out";
    }
    if (closedAsRejected || rejectionThresholdReached) {
      return "❌ Rejected";
    }
    if (approvalThresholdReached) {
      return "✅ Approved";
    }
    return "🕐 Pending";
  }

  // Helper to fetch team members
  async getTeamMembers(teamSlug) {
    try {
      const res = await this.github.request("GET /orgs/{org}/teams/{team_slug}/members", {
        org: this.org,
        team_slug: teamSlug,
        per_page: 100,
      });
      console.log(`Fetched ${res.data.length} ${teamSlug} team members.`);
      return res.data.map((m) => m.login);
    } catch (err) {
      console.error(`Failed to fetch ${teamSlug} team members:`, err);
      throw err;
    }
  }

  // Initialize the manager with team members and comments
  async initialize() {
    // Fetch team members
    this.coreTeamMembers = await this.getTeamMembers("core");
    this.maintainerTeamMembers = await this.getTeamMembers("maintainers");
    console.log("Core team members:", this.coreTeamMembers);
    console.log("Maintainer team members:", this.maintainerTeamMembers);

    // Fetch comments
    this.comments = await this.github.paginate(this.github.rest.issues.listComments, {
      owner: this.org,
      repo: this.repo,
      issue_number: this.issueNumber,
      per_page: 100,
    });

    // Process comments
    this.processComments();
    return this;
  }

  // Helper to update issue status and labels
  async updateIssueStatus(status) {
    // Get current issue to preserve existing labels
    const issue = await this.github.rest.issues.get({
      owner: this.org,
      repo: this.repo,
      issue_number: this.issueNumber,
    });

    // Filter out existing status labels
    const statusLabels = ["accepted", "turned-down", "timed-out", "proposed"];
    const existingLabels = issue.data.labels
      .map((label) => (typeof label === "string" ? label : label.name))
      .filter((label) => !statusLabels.includes(label));

    // Determine new status label
    let newStatusLabel;
    switch (status) {
      case "✅ Approved":
        newStatusLabel = "accepted";
        break;
      case "❌ Rejected":
        newStatusLabel = "turned-down";
        break;
      case "⏰ Timed Out":
        newStatusLabel = "timed-out";
        break;
      default:
        newStatusLabel = "proposed";
    }

    // Combine existing non-status labels with new status label
    const updatedLabels = [...existingLabels, newStatusLabel];

    // Avoid triggering another workflow run when the labels are already right.
    const currentLabels = issue.data.labels.map((label) => (typeof label === "string" ? label : label.name));
    if (
      currentLabels.length === updatedLabels.length &&
      currentLabels.every((label) => updatedLabels.includes(label))
    ) {
      console.log("Issue labels already up to date - no update required.");
      return;
    }

    // Update labels
    await this.github.rest.issues.update({
      owner: this.org,
      repo: this.repo,
      issue_number: this.issueNumber,
      labels: updatedLabels,
    });
  }

  // Helper to find and update status comment
  async updateStatusComment(statusBody) {
    const statusComments = this.comments.filter((c) => c.body && c.body.startsWith("## Approval status:"));
    const statusComment = statusComments[0];

    // Opening an issue also applies its template labels. Older workflow runs
    // could race and create more than one status comment; clean those up when
    // the issue is next processed.
    for (const duplicate of statusComments.slice(1)) {
      console.log(`Deleting duplicate status comment ${duplicate.id}.`);
      await this.github.rest.issues.deleteComment({
        owner: this.org,
        repo: this.repo,
        comment_id: duplicate.id,
      });
    }

    if (statusComment) {
      if (statusComment.body.trim() === statusBody.trim()) {
        console.log("Status comment already up to date - no update required.");
      } else {
        console.log("Updating existing status comment.");
        await this.github.rest.issues.updateComment({
          owner: this.org,
          repo: this.repo,
          comment_id: statusComment.id,
          body: statusBody,
        });
      }
    } else {
      // Fallback: create a new status comment if missing
      await this.github.rest.issues.createComment({
        owner: this.org,
        repo: this.repo,
        issue_number: this.issueNumber,
        body: statusBody,
      });
    }
  }

  // Helper to process comments and collect votes
  processComments() {
    // Reset all approval sets
    this.coreApprovals = new Set();
    this.maintainerApprovals = new Set();
    this.coreRejections = new Set();
    this.maintainerRejections = new Set();

    for (const comment of this.comments) {
      const commenter = comment.user.login;
      const isCoreMember = this.coreTeamMembers.includes(commenter);
      const isMaintainer = this.maintainerTeamMembers.includes(commenter);

      if (!isCoreMember && !isMaintainer) continue; // Only team members count

      // Skip comments with no body
      if (!comment.body) continue;

      // Count approvals / rejections based on line starting with /approve or /reject
      const lines = comment.body.split(/\r\n|\r|\n/);
      for (const rawLine of lines) {
        const line = rawLine.trim();
        if (/^\/approve\b/i.test(line)) {
          if (isCoreMember) {
            this.coreApprovals.add(commenter);
            this.coreRejections.delete(commenter); // Remove any previous rejection
          } else if (isMaintainer) {
            this.maintainerApprovals.add(commenter);
            this.maintainerRejections.delete(commenter); // Remove any previous rejection
          }
        } else if (/^\/reject\b/i.test(line)) {
          if (isCoreMember) {
            this.coreRejections.add(commenter);
            this.coreApprovals.delete(commenter); // Remove any previous approval
          } else if (isMaintainer) {
            this.maintainerRejections.add(commenter);
            this.maintainerApprovals.delete(commenter); // Remove any previous approval
          }
        }
      }
    }

    // Update awaiting lists
    this.awaitingCore = this.coreTeamMembers.filter((u) => !this.coreApprovals.has(u) && !this.coreRejections.has(u));
    this.awaitingMaintainers = this.maintainerTeamMembers.filter(
      (u) => !this.maintainerApprovals.has(u) && !this.maintainerRejections.has(u),
    );
  }
}

module.exports = ApprovalManager;
