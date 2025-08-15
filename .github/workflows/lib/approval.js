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
    const labels = [];

    switch (status) {
      case "✅ Approved":
        labels.push("accepted");
        break;
      case "❌ Rejected":
        labels.push("turned-down");
        break;
      case "⏰ Timed Out":
        labels.push("timed-out");
        break;
      default:
        labels.push("proposed");
    }

    // Update labels
    await this.github.rest.issues.update({
      owner: this.org,
      repo: this.repo,
      issue_number: this.issueNumber,
      labels: labels,
    });
  }

  // Helper to find and update status comment
  async updateStatusComment(statusBody) {
    let statusComment = this.comments.find((c) => c.body.startsWith("## Approval status:"));
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
