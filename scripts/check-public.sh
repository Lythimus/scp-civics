#!/usr/bin/env bash
# Fails if the tree holds something that should not reach a public repository.
# Personal terms live in the untracked .context/private-terms.txt, one regex per line,
# because a committed list of them would publish exactly what it is meant to catch.
set -u
cd "$(git rev-parse --show-toplevel)" || exit 2
status=0

report() {
  echo "check-public: $1" >&2
  status=1
}

email=$(git config user.email)
case "$email" in
  *@users.noreply.github.com) ;;
  *) report "git user.email is not a GitHub noreply address, so commits would publish it" ;;
esac

generic='/Users/|/home/[a-z]|~/Documents|~/\.claude'
if hits=$(git grep --cached -nIE "$generic" -- . ':!scripts/check-public.sh' ':!CLAUDE.md'); then
  report "local paths in tracked files:"
  echo "$hits" | cut -c1-160 >&2
fi

if tracked=$(git ls-files --cached | grep -E '(^|/)(\.context/|CLAUDE\.local\.md|\.DS_Store|__pycache__/|settings\.local\.json|\.pyc$)'); then
  report "private or machine-local files are tracked:"
  echo "$tracked" >&2
fi

terms=.context/private-terms.txt
if [ -f "$terms" ]; then
  if hits=$(git grep --cached -nIiE -f "$terms" -- .); then
    report "private terms in tracked files:"
    echo "$hits" | cut -c1-160 >&2
  fi
else
  echo "check-public: no $terms, so only generic checks ran" >&2
fi

[ "$status" -eq 0 ] && echo "check-public: clean"
exit "$status"
