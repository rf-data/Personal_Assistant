````
source ="https://gist.github.com/MangaD/6a85ee73dd19c833270524269159ed6e#4-installing-and-setting-up-pre-commit"
````

```
https://github.com/pre-commit/pre-commit
````

# The Comprehensive Guide to `pre-commit`

## Table of Contents

1. [Introduction: What is `pre-commit`?](#1-introduction-what-is-pre-commit)
2. [Why Use `pre-commit`?](#2-why-use-pre-commit)
3. [How `pre-commit` Works](#3-how-pre-commit-works)
4. [Installing and Setting Up `pre-commit`](#4-installing-and-setting-up-pre-commit)
5. [Configuring `.pre-commit-configyaml`](#5-configuring-pre-commit-configyaml)
6. [Built-in and Community Hooks](#6-built-in-and-community-hooks)
7. [How to Run and Use `pre-commit`](#7-how-to-run-and-use-pre-commit)
8. [Popular Use Cases](#8-popular-use-cases)
9. [Writing Custom Hooks](#9-writing-custom-hooks)
10. [Advanced Configuration and Features](#10-advanced-configuration-and-features)
11. [Integrating with CI/CD](#11-integrating-with-cicd)
12. [Best Practices](#12-best-practices)
13. [Troubleshooting and Common Issues](#13-troubleshooting-and-common-issues)
14. [Alternatives and Related Tools](#14-alternatives-and-related-tools)
15. [Resources](#15-resources)

------



## 1. Introduction: What is `pre-commit`?

[`pre-commit`](https://pre-commit.com/) is an open-source framework for managing and maintaining multi-language pre-commit hooks. In software development, **Git hooks** are scripts that run automatically on specific Git events (e.g., commit, push). `pre-commit` makes it easy to install and run hooks for code quality, security, style, and more—before code gets committed.

It is language-agnostic and supports everything from Python, JavaScript, Go, and Shell scripts, to Rust, Ruby, and more.

------



## 2. Why Use `pre-commit`?

- **Automate Code Quality**: Catch formatting errors, linting issues, and security flaws *before* they reach your repo.
- **Consistency Across Teams**: Ensures everyone runs the same checks, reducing “works on my machine” problems.
- **Developer Productivity**: Automates repetitive checks, freeing up dev time.
- **Multi-language Support**: Works across codebases with multiple languages and ecosystems.
- **Easy CI/CD Integration**: Hooks can be run manually or in CI to ensure consistency.

------



## 3. How `pre-commit` Works

- You define a list of hooks (scripts) in a `.pre-commit-config.yaml` file.
- `pre-commit` installs and manages isolated, language-specific environments for each hook (virtualenvs, Node, Ruby, system tools, etc.).
- When you run `git commit`, `pre-commit` runs all the enabled hooks on the files you’re committing.
- If a hook fails, the commit is blocked.

------



## 4. Installing and Setting Up `pre-commit`

### Installation

- **Python users**:

  ```sh
  pip install pre-commit
  ```

- **Homebrew (macOS/Linux)**:

  ```sh
  brew install pre-commit
  ```

- **Other**:
   Install via `conda`, `pipx`, or download from [GitHub](https://github.com/pre-commit/pre-commit).

### Setting Up

1. **Add to your project**:

   ```sh
   pre-commit sample-config > .pre-commit-config.yaml
   ```

2. **Install the Git hook scripts**:

   ```sh
   pre-commit install
   ```

   This sets up `.git/hooks/pre-commit` to run `pre-commit` on every commit.

3. **Run on all files (initial run)**:

   ```sh
   pre-commit run --all-files
   ```

------



## 5. Configuring `.pre-commit-config.yaml`

This YAML file tells `pre-commit` which hooks to use and how to run them.

### Example

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0  # Use the latest stable tag
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.4.8
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/psf/black
    rev: 24.3.0
    hooks:
      - id: black
```

**Key Fields**:

- `repo`: URL or path to the repo with hooks
- `rev`: Version tag or commit hash
- `hooks`: List of hook definitions (id, args, files, etc.)

### Hook Options

- `id`: The hook’s unique name.
- `args`: Custom arguments for the hook.
- `files`: Regex for files to include.
- `exclude`: Regex for files to exclude.
- `language_version`: Set the language version (e.g., python3.11).

------



## 6. Built-in and Community Hooks

There’s a huge [list of pre-commit hooks](https://pre-commit.com/hooks.html):

- **Official**: [`pre-commit/pre-commit-hooks`](https://github.com/pre-commit/pre-commit-hooks)
  - E.g., trailing whitespace, debug statements, end-of-file fixes.
- **Language Formatters**:
  - [Ruff](https://github.com/astral-sh/ruff-pre-commit) (Python linter & formatter; replaces flake8, isort, pyupgrade, and more)
  - [Black](https://github.com/psf/black) (Python)
  - [isort](https://github.com/PyCQA/isort) (import sorting)
  - [Prettier](https://github.com/prettier/prettier) (JS/TS/HTML/CSS)
- **Linters**:
  - [Ruff](https://github.com/astral-sh/ruff-pre-commit) (Python, fast, all-in-one)
  - [flake8](https://github.com/pycqa/flake8) (legacy Python projects)
  - [eslint](https://github.com/pre-commit/mirrors-eslint)
  - [shellcheck](https://github.com/koalaman/shellcheck)
- **Security**:
  - [bandit](https://github.com/PyCQA/bandit), [detect-secrets](https://github.com/Yelp/detect-secrets)
- **Others**: License checks, secret detection, file size checks, etc.

------



## 7. How to Run and Use `pre-commit`

- **On every commit**: Automatically runs via the installed hook.

- **Manually on staged files**:

  ```sh
  pre-commit run
  ```

- **On all files**:

  ```sh
  pre-commit run --all-files
  ```

- **On a specific hook**:

  ```sh
  pre-commit run black --all-files
  ```

- **Update all hooks**:

  ```sh
  pre-commit autoupdate
  ```

------



## 8. Popular Use Cases

- **Enforce code style** (formatters, linters)
- **Check for secrets** (AWS keys, passwords)
- **Fix whitespace, newlines, EOF issues**
- **Enforce commit message format**
- **Check for large files or merge conflicts**
- **Security vulnerability checks**

------



## 9. Writing Custom Hooks

You can write your own hooks in any language.

### Local Hook Example (in `.pre-commit-config.yaml`):

```yaml
repos:
  - repo: local
    hooks:
      - id: my-linter
        name: My Custom Linter
        entry: ./scripts/my_linter.sh
        language: script
        files: \.py$
```

### Local Python Hook Example

```yaml
      - id: check-todo
        name: Check for TODOs
        entry: python scripts/check_todo.py
        language: python
        files: .*
```

**Hook script must accept a list of filenames as arguments. Return 0 for pass, non-zero for fail.**

------



## 10. Advanced Configuration and Features

- **Staged-only or all files**: Use `always_run`, `pass_filenames`, and `stages` options.
- **Multiple stages**: Use `stages: [commit, push, manual]`.
- **Parallel execution**: By default, hooks run in parallel.
- **Failing gracefully**: Hooks can be set as `required` or `optional`.
- **Excluding files**: Use the `exclude` regex for large/irrelevant files.
- **Languages**: Hooks support many languages (`python`, `node`, `golang`, `docker`, `system`, etc.).
- **Hook ordering**: Hooks run in the order they’re listed.

------



## 11. Integrating with CI/CD

- **Why**: Ensures code quality checks run in CI, not just on developer machines.

- **How**:

  - In your CI job, install `pre-commit` and run:

    ```sh
    pre-commit run --all-files --show-diff-on-failure
    ```

  - For some CIs (e.g., GitHub Actions), there are pre-built actions:
     [pre-commit/action](https://github.com/pre-commit/action)

- **Fail the build** if hooks fail.

------



## 12. Best Practices

- **Pin hook versions**: Always use specific `rev` values, never `master`/`main`.

- **Run `pre-commit run --all-files` after adding new hooks.**

- **Add `.pre-commit-config.yaml` to source control.**

- **Document setup in `CONTRIBUTING.md`.**

- **Keep hooks fast**—slow hooks slow down developer flow.

- **Autoupdate hooks regularly**:

  ```sh
  pre-commit autoupdate
  ```

- **Review hook changes on update** (some hooks change behavior across versions).

------



## 13. Troubleshooting and Common Issues

- **Hook not running?**
   Did you run `pre-commit install`?

- **Hook fails but works manually?**
   Check environment—`pre-commit` uses isolated environments for each hook.

- **Can’t find a hook or dependency?**
   Sometimes you need to manually install system packages (e.g., `libyaml-dev`).

- **Files modified by hooks?**
   By default, if a hook modifies files (e.g., a formatter), you must `git add` them and recommit.

- **Want to skip `pre-commit` just once?**

  ```sh
  git commit --no-verify
  ```

- **Speed up repeated runs**:
   Use `pre-commit run --files ...` or only staged files.

- **Cross-platform issues**:
   Some hooks may have trouble on Windows—test in your team’s environments.

------



## 14. Alternatives and Related Tools

- **prek** (Rust-based, faster alternative to pre-commit; smaller ecosystem, not a drop-in replacement)
- **Husky** (JavaScript-centric, popular in frontend projects)
- **lefthook** (Go, cross-platform, fast)
- **Overcommit** (Ruby)
- **git hooks** (native, but more manual)
- **uv** (fast Python package manager; complementary to pre-commit, which manages hook environments independently)

`pre-commit` is the most widely used and language-agnostic solution. `prek` can offer faster startup times, but `pre-commit` remains the ecosystem standard with broader hook support and documentation.

------



## 15. Resources

- [pre-commit.com documentation](https://pre-commit.com/)
- [Official hook index](https://pre-commit.com/hooks.html)
- [Writing custom hooks](https://pre-commit.com/#creating-new-hooks)
- [GitHub topic: pre-commit hooks](https://github.com/topics/pre-commit-hooks)
- [Sample `.pre-commit-config.yaml` (from the pre-commit repo)](https://github.com/pre-commit/pre-commit/blob/main/.pre-commit-config.yaml)

------

## TL;DR / Executive Summary

- **pre-commit** is a framework for managing and running Git hooks.
- It is configured via `.pre-commit-config.yaml` and supports many languages.
- You install it, configure hooks, and let it run checks/formatters automatically on commit.
- It boosts code quality, developer experience, and consistency.

------

## Have a specific use case or problem with `pre-commit`?

Let me know—I'm happy to go even deeper into any area, write advanced examples, or help troubleshoot!