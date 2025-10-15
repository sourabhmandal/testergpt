from __future__ import annotations
from typing import List, Optional
from ninja import Schema
from typing import List, Optional
from pydantic import RootModel, Field
from pydantic import BaseModel, Field


class Comment(BaseModel):
    body: str
    line: int
    side: str


class Review(BaseModel):
    file: str = Field(..., description="The file being reviewed")
    comments: List[Comment]


class DiffIssue(BaseModel):
    """Individual issue found in the diff"""

    type: str = Field(..., description="Type of issue: error, warning, or suggestion")
    line: str = Field(..., description="Line number or range where the issue occurs")
    message: str = Field(..., description="Description of the issue")
    severity: str = Field(..., description="Severity level: high, medium, or low")
    file: str = Field(..., description="File path where the issue occurs")


class PRReviewResponse(BaseModel):
    """PR Review LLM response model for diff analysis"""

    issues: List[DiffIssue] = Field(
        default_factory=list, description="List of issues found in the diff"
    )
    summary: str = Field(..., description="Overall assessment of the changes")


class GitHubUser(Schema):
    login: str
    id: int
    node_id: str
    avatar_url: str
    gravatar_id: str
    url: str
    html_url: str
    followers_url: str
    following_url: str
    gists_url: str
    starred_url: str
    subscriptions_url: str
    organizations_url: str
    repos_url: str
    events_url: str
    received_events_url: str
    type: str
    user_view_type: str
    site_admin: bool


class GitHubLicense(Schema):
    key: str
    name: str
    spdx_id: str
    url: str
    node_id: str


class GitHubRepository(Schema):
    id: int
    node_id: str
    name: str
    full_name: str
    private: bool
    owner: GitHubUser
    html_url: str
    description: Optional[str]
    fork: bool
    url: str
    forks_url: str
    keys_url: str
    collaborators_url: str
    teams_url: str
    hooks_url: str
    issue_events_url: str
    events_url: str
    assignees_url: str
    branches_url: str
    tags_url: str
    blobs_url: str
    git_tags_url: str
    git_refs_url: str
    trees_url: str
    statuses_url: str
    languages_url: str
    stargazers_url: str
    contributors_url: str
    subscribers_url: str
    subscription_url: str
    commits_url: str
    git_commits_url: str
    comments_url: str
    issue_comment_url: str
    contents_url: str
    compare_url: str
    merges_url: str
    archive_url: str
    downloads_url: str
    issues_url: str
    pulls_url: str
    milestones_url: str
    notifications_url: str
    labels_url: str
    releases_url: str
    deployments_url: str
    created_at: str
    updated_at: str
    pushed_at: str
    git_url: str
    ssh_url: str
    clone_url: str
    svn_url: str
    homepage: Optional[str]
    size: int
    stargazers_count: int
    watchers_count: int
    language: Optional[str]
    has_issues: bool
    has_projects: bool
    has_downloads: bool
    has_wiki: bool
    has_pages: bool
    has_discussions: bool
    forks_count: int
    mirror_url: Optional[str]
    archived: bool
    disabled: bool
    open_issues_count: int
    license: Optional[GitHubLicense]
    allow_forking: bool
    is_template: bool
    web_commit_signoff_required: bool
    topics: List[str]
    visibility: str
    forks: int
    open_issues: int
    watchers: int
    default_branch: str
    allow_squash_merge: Optional[bool] = None
    allow_merge_commit: Optional[bool] = None
    allow_rebase_merge: Optional[bool] = None
    allow_auto_merge: Optional[bool] = None
    delete_branch_on_merge: Optional[bool] = None
    allow_update_branch: Optional[bool] = None
    use_squash_pr_title_as_default: Optional[bool] = None
    squash_merge_commit_message: Optional[str] = None
    squash_merge_commit_title: Optional[str] = None
    merge_commit_message: Optional[str] = None
    merge_commit_title: Optional[str] = None


class GitHubBranch(Schema):
    label: str
    ref: str
    sha: str
    user: GitHubUser
    repo: GitHubRepository


class GitHubLinks(Schema):
    self: dict  # {"href": str}
    html: dict  # {"href": str}
    issue: dict  # {"href": str}
    comments: dict  # {"href": str}
    review_comments: dict  # {"href": str}
    review_comment: dict  # {"href": str}
    commits: dict  # {"href": str}
    statuses: dict  # {"href": str}


class GitHubPullRequest(Schema):
    url: str
    id: int
    node_id: str
    html_url: str
    diff_url: str
    patch_url: str
    issue_url: str
    number: int
    state: str
    locked: bool
    title: str
    user: GitHubUser
    body: Optional[str]
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    merged_at: Optional[str]
    merge_commit_sha: Optional[str]
    assignee: Optional[GitHubUser]
    assignees: List[GitHubUser]
    requested_reviewers: List[GitHubUser]
    requested_teams: List[dict]  # Team structure would need separate schema
    labels: List[dict]  # Label structure would need separate schema
    milestone: Optional[dict]  # Milestone structure would need separate schema
    draft: bool
    commits_url: str
    review_comments_url: str
    review_comment_url: str
    comments_url: str
    statuses_url: str
    head: GitHubBranch
    base: GitHubBranch
    _links: GitHubLinks
    author_association: str
    auto_merge: Optional[dict]
    active_lock_reason: Optional[str]
    merged: bool
    mergeable: Optional[bool]
    rebaseable: Optional[bool]
    mergeable_state: str
    merged_by: Optional[GitHubUser]
    comments: int
    review_comments: int
    maintainer_can_modify: bool
    commits: int
    additions: int
    deletions: int
    changed_files: int


class GitHubInstallation(Schema):
    id: int
    node_id: str


class GithubPRChanged(Schema):
    action: str
    number: int
    pull_request: GitHubPullRequest
    before: Optional[str] = None
    after: Optional[str] = None
    repository: GitHubRepository
    sender: GitHubUser
    installation: GitHubInstallation


class GitHubCommitAuthor(Schema):
    name: str
    email: str
    date: str


class GitHubCommitTree(Schema):
    sha: str
    url: str


class GitHubCommitVerification(Schema):
    verified: bool
    reason: str
    signature: Optional[str]
    payload: Optional[str]
    verified_at: Optional[str]


class GitHubCommitDetails(Schema):
    author: GitHubCommitAuthor
    committer: GitHubCommitAuthor
    message: str
    tree: GitHubCommitTree
    url: str
    comment_count: int
    verification: GitHubCommitVerification


class GitHubCommitParent(Schema):
    sha: str
    url: str
    html_url: str


class GitHubCommitStats(Schema):
    total: int
    additions: int
    deletions: int


class GitHubCommitFile(Schema):
    sha: str
    filename: str
    status: str
    additions: int
    deletions: int
    changes: int
    blob_url: str
    raw_url: str
    contents_url: str
    patch: Optional[str] = None


class GithubCommit(Schema):
    sha: str
    node_id: str
    commit: GitHubCommitDetails
    url: str
    html_url: str
    comments_url: str
    author: Optional[GitHubUser]
    committer: Optional[GitHubUser]
    parents: List[GitHubCommitParent]


class GithubCommitDetail(Schema):
    """
    Detailed GitHub commit information including file changes and statistics.
    Used for single commit API responses that include diff information.
    """

    sha: str
    node_id: str
    commit: GitHubCommitDetails
    url: str
    html_url: str
    comments_url: str
    author: Optional[GitHubUser]
    committer: Optional[GitHubUser]
    parents: List[GitHubCommitParent]
    stats: GitHubCommitStats
    files: List[GitHubCommitFile]


class GithubCommitList(RootModel[List[GithubCommit]]):
    """
    Represents a list of GitHub commits as a root model.
    This allows direct array validation without a wrapper field.
    """

    root: List[GithubCommit]


class GithubCommitDetailList(RootModel[List[GithubCommitDetail]]):
    """
    Represents a list of detailed GitHub commits with file changes and stats.
    Used when the API returns commits with full diff information.
    """

    root: List[GithubCommitDetail]


class GitHubReactions(Schema):
    url: str
    total_count: int
    plus_one: int = Field(alias="+1")
    minus_one: int = Field(alias="-1")
    laugh: int
    hooray: int
    confused: int
    heart: int
    rocket: int
    eyes: int


class GitHubReviewCommentLinks(Schema):
    self: dict  # {"href": str}
    html: dict  # {"href": str}
    pull_request: dict  # {"href": str}


class ReviewComment(Schema):
    url: str
    pull_request_review_id: int
    id: int
    node_id: str
    diff_hunk: str
    path: str
    commit_id: str
    original_commit_id: str
    user: GitHubUser
    body: str
    created_at: str
    updated_at: str
    html_url: str
    pull_request_url: str
    author_association: str
    _links: GitHubReviewCommentLinks
    reactions: GitHubReactions
    start_line: Optional[int]
    original_start_line: Optional[int]
    start_side: Optional[str]
    line: Optional[int]
    original_line: Optional[int]
    side: Optional[str]
    original_position: Optional[int]
    position: Optional[int]
    subject_type: Optional[str]


class ReviewCommentList(RootModel[List[ReviewComment]]):
    """
    Represents a list of GitHub pull request review comments.
    Used for PR review comments API responses.
    """

    root: List[ReviewComment]
