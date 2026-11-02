#!/usr/bin/env bash
set -eu
root=$(git rev-parse --show-toplevel)
printf '#!/usr/bin/env bash\nexec "%s/scripts/check-public.sh"\n' "$root" > "$root/.git/hooks/pre-commit"
chmod +x "$root/.git/hooks/pre-commit"
echo "pre-commit hook installed"
