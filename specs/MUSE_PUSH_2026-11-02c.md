Push the local commits of ~/projects/forge to GitHub (the user asked Muse Code to publish).
1. Run `git status --short` and `git log --oneline origin/main..HEAD | wc -l` and report both.
2. Run `git push origin main` (normal push; NEVER --force, never push other branches such as backup-*).
3. Run `git log --oneline -1 origin/main` and report it.
Do not change, add or commit any file. If the push is rejected, stop and report the exact error.
