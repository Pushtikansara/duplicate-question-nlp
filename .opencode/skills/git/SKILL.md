---
name: git
description: Use when using Git for version control. Covers branching, rebasing, merging, workflows, and advanced commands.
---

# Git Skill

## Instructions

Git is a distributed version control system that tracks changes in files and coordinates work among multiple developers. It is the de facto standard for source code management. This skill covers Git fundamentals, branching strategies, merging, rebasing, advanced operations, and best practices for individual and team workflows.

### Core Concepts

**Repository (repo)**: A directory containing the project files and the entire history of changes.

**Commit**: A snapshot of changes at a point in time, identified by a SHA-1 hash.

**Branch**: A movable pointer to a specific commit, enabling parallel development.

**Remote**: A version of the repository hosted on a server (GitHub, GitLab, Bitbucket).

**Working Directory**: The actual files on your file system.

**Staging Area (Index)**: An intermediate area where changes are prepared before committing.

**HEAD**: A pointer to the current commit or branch.

### Basic Configuration

```bash
# Set identity
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Set default branch name
git config --global init.defaultBranch main

# Enable color output
git config --global color.ui auto

# Set default editor
git config --global core.editor "code --wait"

# Configure aliases
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --decorate --all"
git config --global alias.unstage "reset HEAD --"

# View configuration
git config --list
git config --global --list
```

### Initializing and Cloning

```bash
# Initialize new repository
git init

# Clone existing repository
git clone https://github.com/user/repo.git

# Clone with specific branch
git clone -b develop https://github.com/user/repo.git

# Shallow clone (recent history only)
git clone --depth 1 https://github.com/user/repo.git
```

## Examples

### Example 1: Basic Workflow

```bash
# Check status
git status

# Add files to staging
git add file.txt              # Single file
git add .                     # All files in current directory
git add -p                    # Interactive staging (hunk by hunk)

# Commit with message
git commit -m "Add user authentication feature"

# Commit with detailed message
git commit -m "Add user authentication" -m "- Implements JWT-based login
- Adds password hashing with bcrypt
- Includes refresh token rotation"

# Commit with editor
git commit                     # Opens configured editor

# Amend last commit (don't amend pushed commits)
git commit --amend -m "Corrected message"

# View commit history
git log                        # Full history
git log --oneline              # Compact one-line format
git log --oneline --graph      # With branch graph
git log --oneline -10          # Last 10 commits
git log --author="user"        # Filter by author
git log --since="2 weeks ago"  # Filter by date
git log --grep="fix"           # Search commit messages
```

### Example 2: Branching and Merging

```bash
# List branches
git branch                     # Local branches
git branch -r                  # Remote branches
git branch -a                  # All branches

# Create and switch branches
git branch feature/login       # Create branch
git checkout feature/login     # Switch to branch
git checkout -b feature/login  # Create and switch

# Modern switch/restore (Git 2.23+)
git switch feature/login       # Switch branch
git switch -c feature/login    # Create and switch
git switch -                   # Switch to previous branch

# Merge branches
git checkout main              # Switch to target branch
git merge feature/login        # Merge feature into main

# Merge with explicit strategy
git merge --no-ff feature/login     # Always create merge commit
git merge --squash feature/login    # Squash all commits into one

# Delete branches
git branch -d feature/login         # Delete merged branch
git branch -D feature/login         # Force delete unmerged branch
git push origin --delete feature/login  # Delete remote branch

# View branch differences
git diff main..feature              # Show differences
git log main..feature               # Commits in feature not in main
git log --oneline --graph --all     # Visualize branches
```

### Example 3: Rebasing

```bash
# Rebase current branch onto another
git checkout feature
git rebase main

# Interactive rebase (edit history)
git rebase -i HEAD~5            # Rebase last 5 commits
git rebase -i main              # Rebase all commits since branching from main

# Interactive rebase commands:
# pick    = use commit
# reword  = use commit but edit message
# edit    = use commit but stop for amending
# squash  = combine with previous commit
# fixup   = like squash but discard message
# drop    = remove commit

# Rebase with conflict resolution
git rebase main
# ... resolve conflicts ...
git add resolved-file.txt
git rebase --continue

# Abort rebase if things go wrong
git rebase --abort

# Rebase onto specific commit
git rebase --onto main feature-1 feature-2  # Rebase feature-2 onto main, off feature-1

# Pull with rebase instead of merge
git pull --rebase
# Or configure as default:
git config --global pull.rebase true
```

### Example 4: Handling Conflicts

```bash
# Check for conflicts
git status                       # Shows "both modified" files

# View conflict markers
<<<<<<< HEAD
# Current branch's changes
=======
# Incoming branch's changes
>>>>>>> feature-branch

# Conflict resolution tools
git mergetool                    # Launch configured merge tool
git diff                         # Show conflict details

# Resolve by accepting one side
git checkout --ours file.txt     # Keep our version
git checkout --theirs file.txt   # Keep their version

# After resolving:
git add file.txt
git commit                       # For merge conflicts
git rebase --continue            # For rebase conflicts

# Abort operations
git merge --abort
git rebase --abort
```

### Example 5: Stashing and Cleaning

```bash
# Save uncommitted changes
git stash                        # Stash tracked files
git stash push -m "WIP: login form"  # With message
git stash -u                     # Include untracked files
git stash -a                     # Include all files (including ignored)

# List stashes
git stash list

# Apply stashes
git stash apply                  # Apply latest stash (keeps in list)
git stash pop                    # Apply and remove from list
git stash apply stash@{2}        # Apply specific stash

# Drop stashes
git stash drop stash@{2}         # Remove specific stash
git stash clear                  # Remove all stashes

# Show stash contents
git stash show -p stash@{0}      # Show diff of stash

# Create branch from stash
git stash branch new-branch stash@{0}

# Clean untracked files
git clean -n                     # Dry run (show what would be deleted)
git clean -f                     # Force remove untracked files
git clean -fd                    # Remove untracked files and directories
git clean -fx                    # Remove ignored files too
```

### Example 6: Advanced History Manipulation

```bash
# Find commits by content
git log -S "functionName"        # Commits that change "functionName"
git log -G "pattern"             # Commits matching regex pattern
git log -p -- file.txt           # Show patches for specific file

# Blame (find who changed each line)
git blame file.txt
git blame -L 10,20 file.txt      # Lines 10-20

# Revert commits
git revert HEAD                  # Revert latest commit (creates new commit)
git revert HEAD~3..HEAD          # Revert range of commits

# Reset (be careful with published history)
git reset --soft HEAD~1          # Move HEAD, keep changes staged
git reset --mixed HEAD~1         # Move HEAD, keep changes working (default)
git reset --hard HEAD~1          # Move HEAD, discard changes (DANGER)
git reset --hard origin/main     # Reset to match remote

# Cherry-pick specific commits
git cherry-pick commit-hash
git cherry-pick commit1..commit5 # Range of commits
git cherry-pick --no-commit abc123  # Apply but don't commit

# Bisect (find commit that introduced bug)
git bisect start
git bisect bad                   # Current commit is bad
git bisect good v1.0             # Tag v1.0 is good
# Git checks out middle commit; test and mark:
git bisect good                  # or git bisect bad
git bisect reset                 # End bisect session
```

### Example 7: Remote Operations

```bash
# Add remote
git remote add origin https://github.com/user/repo.git
git remote add upstream https://github.com/original/repo.git

# List remotes
git remote -v

# Fetch changes
git fetch origin                # Fetch all branches
git fetch origin main           # Fetch specific branch
git fetch --prune origin        # Fetch and remove deleted remote branches
git fetch --tags                # Fetch tags

# Push changes
git push origin main            # Push branch
git push -u origin feature      # Push and set upstream
git push --force-with-lease     # Force push safely (preferred)
git push origin --delete feature  # Delete remote branch
git push --tags                 # Push tags

# Pull changes
git pull origin main            # Fetch and merge
git pull --rebase origin main   # Fetch and rebase

# Sync fork with upstream
git fetch upstream
git checkout main
git merge upstream/main
git push origin main
```

## Best Practices

### Commit Practices

- Write clear, concise commit messages (50-char subject, 72-char body)
- Use the imperative mood ("Add feature" not "Added feature")
- Separate subject from body with a blank line
- Keep commits atomic and focused on a single change
- Commit early, commit often (logical checkpoints)
- Never commit generated files, dependencies, or secrets
- Use `.gitignore` to exclude unnecessary files
- Review changes before committing with `git diff` or `git add -p`

### Branching Practices

- Use descriptive branch names: `feature/login`, `fix/typo`, `chore/update-deps`
- Keep branches short-lived; merge frequently to avoid divergence
- Delete branches after merging (both local and remote)
- Use `git worktree` for working on multiple branches simultaneously
- Protect main branches with branch protection rules
- Use commit signing (GPG) for important branches

### History Management

- Prefer rebase over merge for keeping linear history in feature branches
- Squash commits before merging to main for clean history
- Use `--force-with-lease` over `--force` for safer force pushes
- Never rebase published commits that others may have based work on
- Use `git reflog` to recover lost commits (safety net)
- Document important merge points with tags

### Collaboration Practices

- Communicate before rebasing shared branches
- Resolve conflicts in your own branch before merging
- Use pull requests or merge requests for code review
- Keep PRs small and focused for easier review
- Use draft PRs for work in progress
- Enable branch protection on main branches

## Common Mistakes

- **Committing sensitive information**: Committed secrets (passwords, API keys) remain in history forever. Use `git-secrets` pre-commit hooks and rotate exposed secrets immediately.
- **Force pushing to shared branches**: Force pushing rewrites history and causes chaos for collaborators. Use `--force-with-lease` and communicate before force pushing.
- **Large files in repository**: Binary files, media, and large datasets bloat the repository. Use Git LFS for large files.
- **Not using `.gitignore`**: Generated files, dependencies (node_modules, vendor), and IDE files should be ignored. Set up `.gitignore` at project initialization.
- **Unclear commit messages**: "Fix bug" or "Update" are unhelpful messages. Explain what and why, not how.
- **Merging without reviewing**: Always review changes via `git diff` or PR before merging.
- **Working directly on main**: Never commit directly to main. Use feature branches and pull requests.
- **Forgetting to pull before push**: Local commits diverge from remote quickly. Always pull/rebase before pushing.
- **Not resolving conflicts carefully**: Merge conflicts need manual review. Automatic resolution or mindless accept-all can introduce bugs.
- **Deep, long-running branches**: Branches that live for weeks accumulate massive conflicts. Keep branches short (1-2 days).

## Libraries

### Git Tools and GUIs

| Tool | Purpose |
|------|---------|
| Git CLI | Official command-line tool |
| GitKraken | Cross-platform Git GUI |
| Sourcetree | Free Git GUI (Windows/Mac) |
| GitHub Desktop | Simple Git client from GitHub |
| GitLens | VS Code Git extension |
| lazygit | Terminal-based Git UI |
| Tig | Text-mode Git interface |
| git-gui | Official Git GUI |
| magit | Emacs Git interface |
| fugitive.vim | Vim Git interface |

### Git Utilities

| Utility | Purpose |
|---------|---------|
| git-secrets | Prevent committing secrets |
| git-flow | GitFlow extension |
| pre-commit | Git hook framework |
| gh | GitHub CLI |
| glab | GitLab CLI |
| gitleaks | Secret scanning in repos |
| git-filter-repo | History rewriting tool |
| git-lfs | Large file storage |
| git-imerge | Incremental merge/rebase |

## Design Principles

### Atomic Commits

Each commit should represent a single logical change. This makes the history easier to understand, revert, and cherry-pick. If a change spans multiple files, that is fine as long as it is a single concept (e.g., "Add user authentication" might touch auth code, database schema, and tests).

### Linear History is Precious

A clean, linear commit history is easier to understand, bisect, and revert. Use rebasing to keep feature branches up to date with main, and squash commits before merging to eliminate the noise of working-in-progress commits.

### Distributed but Coordinated

Git is distributed, but teams still need coordination. Establish clear conventions for branching, commit messages, and history management. Automate what can be automated (hooks, CI checks) and document what cannot.

### Safety Nets

Git's reflog records every change to HEAD, making it possible to recover from most mistakes. Understanding `git reflog` and the difference between soft, mixed, and hard resets gives developers confidence to experiment.

## Coding Standards

### Commit Message Format

```
<type>(<scope>): <subject>        # 50 chars max
<BLANK LINE>
<body>                             # 72 chars per line
<BLANK LINE>
<footer>
```

### Commit Types

| Type | Description |
|------|-------------|
| feat | A new feature |
| fix | A bug fix |
| docs | Documentation changes |
| style | Code style changes (formatting, etc.) |
| refactor | Code refactoring (no functional change) |
| test | Adding or modifying tests |
| chore | Maintenance tasks, dependency updates |
| perf | Performance improvements |
| ci | CI/CD configuration changes |

### Branch Naming

```
<type>/<short-description>
# Examples:
feat/user-authentication
fix/login-validation
chore/update-dependencies
docs/api-endpoints
hotfix/critical-security-issue
```

### .gitignore Template

```
# Dependencies
node_modules/
vendor/
.pnp/
.pnp.js

# Build outputs
dist/
build/
*.tsbuildinfo

# Environment files
.env
.env.local
.env.*.local

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log
npm-debug.log*

# Coverage
coverage/
.nyc_output/
```
