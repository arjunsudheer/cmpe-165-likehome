# Contributing Guidelines

Welcome to the project! To maintain a clean history and high code quality, please adhere to the following standards for branching, commits, and pull requests.

## 🌿 Branching Strategy

Always ensure your local environment is up to date before starting:
`git checkout main && git pull && git checkout -b your-branch-name`

We use a structured branching model. All new work must be performed in a dedicated branch.

### Branch Naming Convention

All branch names must follow this specific pattern:
`category/us-[ID]-[issue-name]`

1. **Category:** Your branch must start with one of the following:
    * `feat/` : New functionality or enhancements.
    * `fix/` : Fixing a bug or error.
    * `chore/` : Maintenance tasks (dependencies, build configs).
    * `docs/` : Documentation-only changes.
2. **User Story ID:** Must include `us-` followed by a sequence of up to 4 alphanumeric characters (e.g., `us-a01`). The user story ID must refer to the open issue you are addressing.
3. **Issue Name:** A description of the open issue you are addressing.

## 💬 Commit Message Standards

We aim for a history that is easy to read and searchable.

* **Make Small Commits:** Each commit should do **one thing**, not five things at once.
* **Write Clear Messages:** Start with a **verb**. Avoid vague terms like "stuff" or "changes.
  * **Good:** `Add login endpoint`
  * **Good:** `Fix reservation date validation`
  * **Bad:** `Updated search filter query — not stuff or changes`

## 🛡️ Branch Protection Rules

To protect the integrity of the `main` branch, the following rules are strictly enforced:

* **No Direct Pushes:** All changes must be submitted via a **Pull Request**. Direct pushes to `main` are blocked.
* **Mandatory Reviews:** At least one peer review is required before a PR can be merged.
* **Status Checks:** All automated tests and linters must pass before merging.
* **Squash and Merge:** We use "Squash and Merge" to keep the `main` history linear and clean by condensing feature branch commits into a single high-quality commit.

## 🚀 The Contribution Workflow

1. **Sync:** Pull the latest changes from `main`.
2. **Branch:** Create your branch using the `category/us-xxxx-issue-name` format.
3. **Commit:** Write clear, concise commit messages using the `type: description` format.
4. **Push:** Push your branch to the remote repository.
5. **PR:** Open a Pull Request. Reference the issue number in the description (e.g., "Closes #12").
6. **Review:** Address any comments or requested changes from your teammates.
7. **Merge:** Once approved and checks pass, squash and merge!
