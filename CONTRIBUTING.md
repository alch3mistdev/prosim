# Contributing to ProSim

Thank you for your interest in contributing to ProSim! We welcome bug reports,
feature requests, documentation improvements, and pull requests from the
community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Running Tests](#running-tests)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Reporting Bugs](#reporting-bugs)
- [Requesting Features](#requesting-features)

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this standard. Please report
unacceptable behavior by opening a GitHub issue.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/prosim.git
   cd prosim
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/alch3mistdev/prosim.git
   ```

## Development Setup

### Backend (Python ≥ 3.11)

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install the package with development dependencies
pip install -e ".[dev]"

# Copy the environment template and fill in your API key
cp .env.example .env
```

Set `ANTHROPIC_API_KEY` in `.env` to enable workflow generation tests that call
the Claude API.

### Frontend (Node.js ≥ 20)

```bash
cd frontend
npm install
```

## Making Changes

1. Create a feature branch off `main`:
   ```bash
   git checkout -b feat/my-feature
   ```
2. Follow the existing code style:
   - **Python**: [PEP 8](https://peps.python.org/pep-0008/) with Pydantic models
     for data structures and `pytest` for tests.
   - **TypeScript/React**: strict TypeScript, functional components, Tailwind CSS
     utility classes.
3. Keep commits focused and write clear commit messages.
4. Add or update tests to cover your changes (see [Running Tests](#running-tests)).

## Running Tests

### Python backend

```bash
pytest tests/ -v
```

For coverage:

```bash
pytest tests/ --cov=src/prosim --cov-report=term-missing
```

### Frontend (type-check + production build)

```bash
cd frontend && npx next build
```

### Manual API verification

With the backend running (`prosim serve --port 8000`):

```bash
./scripts/verify-api.sh
```

## Submitting a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feat/my-feature
   ```
2. Open a pull request against the `main` branch of this repository.
3. Fill in the PR template, describing *what* changed and *why*.
4. Ensure all existing tests pass and add new tests where appropriate.
5. A maintainer will review your PR and may request changes before merging.

## Reporting Bugs

Please open a [GitHub issue](https://github.com/alch3mistdev/prosim/issues) and
include:

- A clear and descriptive title.
- Steps to reproduce the problem.
- Expected and actual behaviour.
- ProSim version, Python version, and OS.
- Relevant log output or error messages.

## Requesting Features

Open a [GitHub issue](https://github.com/alch3mistdev/prosim/issues) with the
label **enhancement** and describe:

- The problem you are trying to solve.
- Your proposed solution or workflow.
- Any alternatives you have considered.

We appreciate every contribution, big or small. Thank you for helping make
ProSim better!
