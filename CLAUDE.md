# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Claude Code Security Reviewer - a GitHub Action that provides AI-powered security analysis for pull requests using Claude. The action analyzes code changes for security vulnerabilities with deep semantic understanding and automatically comments on PRs with findings.

## Development Commands

### Testing
```bash
# Run all tests
pytest claudecode -v

# Run specific test modules
pytest claudecode/test_*.py -v

# Run eval framework tests on specific PRs
python -m claudecode.evals.run_eval owner/repo#123 --verbose
```

### JavaScript Components
```bash
# Test the PR commenting scripts (in scripts/ directory)
cd scripts
bun test
# or
bun test --watch
```

### Local Development with Eval Framework
```bash
# Test the security scanner locally against a specific PR
python -m claudecode.evals.run_eval example/repo#123 --verbose --output-dir ./eval_results
```

## Architecture

### Core Components

- **`github_action_audit.py`** - Main entrypoint for GitHub Actions that orchestrates the security analysis
- **`prompts.py`** - Security audit prompt templates for Claude Code
- **`findings_filter.py`** - Advanced false positive filtering using both hard rules and Claude API
- **`claude_api_client.py`** - Claude API client for false positive filtering
- **`json_parser.py`** - Robust JSON parsing utilities with fallbacks

### Key Workflows

1. **PR Analysis**: Fetches PR diff and metadata via GitHub API
2. **Security Review**: Runs Claude Code with specialized security prompts
3. **False Positive Filtering**: Two-stage filtering (hard exclusions + Claude API analysis)
4. **PR Comments**: Posts findings as review comments on specific code lines

### Configuration Options

The action supports extensive configuration via environment variables and file inputs:
- Custom false positive filtering instructions (`FALSE_POSITIVE_FILTERING_INSTRUCTIONS`)
- Custom security scan instructions (`CUSTOM_SECURITY_SCAN_INSTRUCTIONS`)
- Directory exclusions (`EXCLUDE_DIRECTORIES`)
- Claude model selection (`CLAUDE_MODEL`)

## Security Analysis Capabilities

The tool detects vulnerabilities across multiple categories:
- Input validation (SQL injection, command injection, XXE, etc.)
- Authentication & authorization bypasses
- Cryptographic issues and hardcoded secrets
- Code execution vulnerabilities (RCE, deserialization, XSS)
- Data exposure and PII handling violations

## Testing Approach

- Unit tests for individual components (`test_*.py` files)
- Integration tests for the full workflow
- Evaluation framework for testing on real PRs (`claudecode/evals/`)
- JavaScript tests for PR commenting scripts

## Important Implementation Details

- Hard exclusion rules filter out DOS, rate limiting, and resource management findings
- Memory safety findings are only valid for C/C++ files
- Markdown files are excluded from security analysis
- SSRF findings in HTML files are excluded (client-side context)
- The system includes retry logic for Claude API calls and prompt size management

## Development Environment

- Python 3.9+ with dependencies in `claudecode/requirements.txt`
- Bun/Node.js for JavaScript components in `scripts/`
- GitHub CLI (`gh`) for API access in eval framework
- Environment variables: `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`