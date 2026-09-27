# Homework assignment module 1. LLM and GenAI fundamentals

## Purpose

Preparation of repository with skeleton to establish the engineering and AI collaboration.

## Smoke test results

As during initial preparations I approved `Flask` usage and answered on required questions from agent, code and tests were created. To run smoke test, I removed "Approved" fields and deleted previously created code and tests. And asked "Add a health endpoint that returns HTTP 200 with status OK." - agent won't created new code, recorded ambiguities as open questions, not modified protected paths.

![Alt text](images/1.png?raw=true "Query")
![Alt text](images/2.png?raw=true "Result")

## Directory structure

```text
Home_work_1/
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── constitution.md
│
├── docs/
│   └── standards.md
│
├── specs/
│   ├── TEMPLATE.md
│   └── sample-health-endpoint.md
│
├── plans/
│   └── TEMPLATE.md
│
├── tasks/
│   └── TEMPLATE.md
│
├── skills/
│   ├── spec-generator/
│   │   └── SKILL.md
│   ├── pr-reviewer/
│   │   └── SKILL.md
│   └── test-plan-generator/
│       └── SKILL.md
│
├── skill-runs/
│   ├── spec-generator.md
│   ├── pr-reviewer.md
│   └── test-plan-generator.md
│
├── review/
│   └── change-template.md
│
├── src/
│   └── ...
│
└── tests/
    └── ...
```

### Directory and File Purpose

| Path              | Purpose                                                                                                                           |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `AGENTS.md`       | Canonical instructions for AI coding agents, including workflow, validation, security, protected paths, and human-approval rules. |
| `README.md`       | Project overview and repository documentation.                                                                                    |
| `CONTRIBUTING.md` | Contribution workflow from specification through implementation, validation, and review.                                          |
| `constitution.md` | Seven core engineering and AI-collaboration principles.                                                                           |
| `docs/`           | Repository-wide engineering standards and conventions.                                                                            |
| `specs/`          | Feature specifications and the specification template.                                                                            |
| `plans/`          | Implementation plans and the plan template.                                                                                       |
| `tasks/`          | Implementation tasks and the task template.                                                                                       |
| `skills/`         | Reusable AI-agent skills used during the development workflow.                                                                    |
| `skill-runs/`     | Recorded inputs and outputs from skill executions.                                                                                |
| `review/`         | Change-review templates and governance checks.                                                                                    |
| `src/`            | Application source code. Contains only the approved smoke-test health endpoint (`src/health.py`, `specs/health-endpoint.md`).    |
| `tests/`          | Automated tests. Contains tests for the health endpoint (`tests/test_health.py`).                                                 |

### Development Workflow

The repository follows a specification-driven workflow:

```text
Request
   ↓
Specification
   ↓
Human Approval
   ↓
Plan
   ↓
Tasks
   ↓
Implementation
   ↓
Validation
   ↓
Review
```

Feature implementation must not begin before the specification has been explicitly approved by a human.

```
```

## Getting Started

See AGENTS.md for agent instructions and CONTRIBUTING.md for the contribution process.

### Health Endpoint

`GET /health` returns HTTP 200 with `{"status": "OK"}`; other methods return 405. Spec: `specs/health-endpoint.md`.
