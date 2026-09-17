---
draft: false
weight: 10
showAuthor: true
showDate: true
showWordCount: true
showReadingTime: true
date: 2026-08-09
title: "git worktree Lets You Check Out Multiple Branches at Once"
tags: [git]
categories: [Tooling]
---

`git worktree add ../foo-bugfix bugfix-branch` checks out `bugfix-branch` into a separate directory, sharing the same `.git` history — no need to stash or switch branches in your main working copy.

This is useful when you need to run a long build or test suite on one branch while continuing to edit another, or when you want to compare behavior between two branches side by side without juggling stashes.

Remove a worktree when you're done with it via `git worktree remove ../foo-bugfix` (or `git worktree prune` after manually deleting the directory).

```
git worktree add ../foo-bugfix bugfix-branch
git worktree list
git worktree remove ../foo-bugfix
```
