---
name: autodev-pipeline
description: Build or use the proactive auto-development pipeline (issue detection → spec → plan → implement → PR). Covers the autodev Django app architecture.
---

# AutoDev Pipeline

The proactive auto-development system: automatically detects issues from connected trackers, generates specs via AI, executes the SpecKit flow, and creates a PR linked to the original issue.

## Architecture Overview

```
Issue Tracker (GitHub/GitLab/Jira/Linear)
    ↓ [polling or webhook, every 5 min]
IssueTrackerSyncEngine
    ↓
AutoDevDemand (detected, eligible?)
    ↓ [Celery: process_demand task]
DemandAnalyzer (LiteLLM → spec.md)
    ↓ [human approval gate if configured]
PipelineOrchestrator (specify → plan → tasks)
    ↓ [Claude Agent SDK in Docker sandbox]
CodeExecutor (implement, commit, push)
    ↓
PRCreator (GitHub/GitLab API → PR linked to issue)
    ↓
AutoDevPipeline (status: pr_created)
```

## Django App Structure (`backend/autodev/`)

```
autodev/
├── models.py                    # IssueTrackerConfig, AutoDevDemand, AutoDevPipeline, AutoDevConfig
├── serializers.py               # DRF serializers
├── views.py                     # ViewSets: config, demands, pipeline
├── urls.py                      # /api/v1/autodev/*
├── tasks.py                     # Celery: poll_issue_trackers, process_demand, execute_pipeline_step
├── signals.py                   # Pipeline status change handlers
└── services/
    ├── issue_tracker.py         # IssueTrackerSyncEngine
    ├── demand_analyzer.py       # AI spec generation
    ├── pipeline_orchestrator.py # specify → plan → tasks flow
    ├── code_executor.py         # Claude Agent SDK + Docker sandbox
    └── pr_creator.py            # GitHub/GitLab PR creation
```

## Key Models

### IssueTrackerConfig
```python
# Connects a user's issue tracker to their repos
tracker_type: 'github_issues' | 'gitlab_issues' | 'jira' | 'linear'
filter_labels: list  # Labels that trigger autodev (e.g., ["autodev", "ai-implement"])
filter_assignee: bool  # Only process issues assigned to the user
credentials: EncryptedTextField  # Encrypted at rest
```

### AutoDevDemand
```python
status: 'detected' | 'analyzing' | 'awaiting_approval' | 'implementing' | 'pr_created' | 'failed' | 'skipped'
issue_url: str
issue_title: str
spec_content: str  # Generated spec.md content
plan_content: str  # Generated plan.md content
eligibility_score: float  # 0-1, determines if suitable for automation
```

### AutoDevPipeline
```python
# Tracks each step of the pipeline
demand: FK(AutoDevDemand)
step: 'specify' | 'plan' | 'implement' | 'review' | 'pr_create'
status: 'pending' | 'running' | 'completed' | 'failed'
input_tokens: int
output_tokens: int
duration_seconds: float
error_message: str  # If failed
```

## Celery Tasks

### poll_issue_trackers (periodic, every 5 min)
```python
@app.task
def poll_issue_trackers():
    """Poll all active issue tracker configs for new issues."""
    configs = IssueTrackerConfig.objects.filter(is_active=True)
    for config in configs:
        engine = IssueTrackerSyncEngine(config)
        new_issues = engine.fetch_new_issues()
        for issue in new_issues:
            create_demand_and_analyze.delay(str(config.id), issue.to_dict())
```

### process_demand (triggered per new demand)
```python
@app.task(bind=True, max_retries=3)
def process_demand(self, demand_id: str):
    """Analyze demand and generate spec via AI."""
    demand = AutoDevDemand.objects.get(id=demand_id)
    analyzer = DemandAnalyzer(demand)

    spec = analyzer.generate_spec()  # LiteLLM call
    demand.spec_content = spec
    demand.status = 'awaiting_approval' if config.approval_mode == 'manual' else 'implementing'
    demand.save()

    if demand.status == 'implementing':
        execute_pipeline.delay(demand_id)
```

### execute_pipeline (triggered after approval)
```python
@app.task(bind=True, max_retries=1, time_limit=3600)  # 1 hour max
def execute_pipeline(self, demand_id: str):
    """Execute full SpecKit flow: plan → implement → PR."""
    demand = AutoDevDemand.objects.get(id=demand_id)
    orchestrator = PipelineOrchestrator(demand)

    # Step 1: Generate plan
    plan = orchestrator.generate_plan()

    # Step 2: Execute in sandbox
    executor = CodeExecutor(demand, plan)
    result = executor.run()  # Claude Agent SDK

    # Step 3: Create PR
    if result.success:
        pr = PRCreator(demand, result).create_pr()
        demand.pr_url = pr.url
        demand.status = 'pr_created'
        demand.save()
```

## Provider Pattern for Issue Trackers

New trackers must implement `IssueTrackerProvider`:

```python
# backend/autodev/services/issue_tracker.py
class IssueTrackerProvider(Protocol):
    def fetch_new_issues(self, since_cursor: str) -> list[Issue]: ...
    def get_issue(self, issue_id: str) -> Issue: ...
    def post_comment(self, issue_id: str, comment: str) -> None: ...

class GitHubIssuesProvider:
    """Implements IssueTrackerProvider for GitHub Issues."""
    def fetch_new_issues(self, since_cursor: str) -> list[Issue]:
        # Use PyGithub or direct REST API
        ...
```

## Frontend — AutoDev Dashboard

```typescript
// src/pages/admin/AutoDevPage.tsx
// Shows pipeline status for all demands

// src/components/admin/AutoDevDashboard.tsx
// Real-time updates via polling (useQuery with refetchInterval)
const { data: demands } = useQuery({
  queryKey: ['autodev', 'demands'],
  queryFn: () => api.get<AutoDevDemand[]>('/api/v1/autodev/demands/'),
  refetchInterval: 10_000,  // Poll every 10 seconds
});

// src/components/admin/AutoDevDemandDetail.tsx
// Shows: issue → spec → plan → tasks → PR with full traceability
```

## Eligibility Scoring

Before processing a demand, score it 0-1 for automation suitability:

```python
# demand_analyzer.py
def score_eligibility(self, issue: Issue) -> float:
    score = 0.0

    # Positive signals
    if len(issue.description) > 100: score += 0.2  # Well-described
    if issue.has_label('bug'): score += 0.2          # Clear type
    if issue.has_label('good-first-issue'): score += 0.1
    if self._estimated_complexity(issue) == 'small': score += 0.3

    # Negative signals
    if 'design' in issue.title.lower(): score -= 0.3   # Design decisions need humans
    if issue.has_label('needs-discussion'): score -= 0.4

    return max(0.0, min(1.0, score))

# Only proceed if score >= 0.6
```

## Safety Constraints

- **Sandbox always** — CodeExecutor runs in isolated Docker container
- **Human approval gate** — `AutoDevConfig.approval_mode = 'manual'` stops before implementing
- **Max complexity** — Skip issues estimated > L (4+ hours)
- **Rate limits** — Max 3 concurrent pipelines per user
- **Token budget** — Configurable max tokens per pipeline step
