#!/usr/bin/env bash
# Merge NousResearch/hermes-agent main into this fork and keep HUNTINGTON-AGENT's removals removed.
#
#   scripts/huntington/sync-upstream.sh            # fetch + merge upstream/main, re-delete removed paths
#   scripts/huntington/sync-upstream.sh --apply    # only re-delete removed paths (no fetch/merge)
#
# Every path in huntington/removed-paths.txt is deleted again after the merge. That turns the
# modify/delete conflicts upstream's edits would cause into automatic resolutions, and also drops
# any new file upstream adds under a removed directory. Files in huntington/fork-owned-paths.txt
# keep the fork's version on conflict. scripts/huntington/rebrand.py is re-run over the merged tree,
# and a conflict the rebrand alone causes is re-merged with upstream's side rebranded. Conflicts
# that remain (an upstream change next to one of the fork's hooks) are left for you to resolve;
# the script stops and lists them.
set -euo pipefail

root=$(git rev-parse --show-toplevel)
cd "$root"
manifest=huntington/removed-paths.txt
owned=huntington/fork-owned-paths.txt
upstream_url=https://github.com/NousResearch/hermes-agent.git
upstream_branch=${UPSTREAM_BRANCH:-main}

# A manifest line is a path or a glob (`plugin-catalog/*.yaml`); a `!path` line keeps that path even
# when a glob matches it. Globs also drop files upstream adds later under the same pattern.
remove_paths() {
    local pattern path keep IFS=$'\n'
    keep=$(grep '^!' "$manifest" | cut -c2- || true)
    grep -v '^\s*[#!]' "$manifest" | sed '/^\s*$/d' | while IFS= read -r pattern; do
        for path in $( { git ls-files -- "$pattern"; compgen -G "$pattern" || true; } | sort -u); do
            if printf '%s\n' "$keep" | grep -qxF -- "$path"; then
                continue
            fi
            git rm -r -q --cached --ignore-unmatch -- "$path" >/dev/null
            rm -rf -- "$path"
        done
    done
}

if [ "${1:-}" = "--apply" ]; then
    remove_paths
    echo "Removed paths re-applied. Review with: git status"
    exit 0
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "Working tree has uncommitted changes; commit or stash them first." >&2
    exit 1
fi

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "$upstream_url"
git fetch upstream "$upstream_branch"

keep_fork_owned() {
    local path
    grep -v '^\s*#' "$owned" | sed '/^\s*$/d' | while IFS= read -r path; do
        if git diff --name-only --diff-filter=U -- "$path" | grep -q .; then
            git checkout --ours -- "$path" && git add -- "$path"
        fi
    done
}

python_bin=${HERMES_PYTHON:-$( [ -x .venv/bin/python ] && echo .venv/bin/python || command -v python3 )}
rebrand() { "$python_bin" scripts/huntington/rebrand.py "$@"; }

# Re-merge a conflicted file with the rebrand applied to upstream's side and to the merge base,
# so a conflict the rebrand alone causes (upstream edited a line the fork rebranded) resolves.
remerge_rebranded() {
    local path tmp
    git diff --name-only --diff-filter=U | while IFS= read -r path; do
        git cat-file -e ":1:$path" 2>/dev/null && git cat-file -e ":2:$path" 2>/dev/null \
            && git cat-file -e ":3:$path" 2>/dev/null || continue
        tmp=$(mktemp -d)
        git show ":2:$path" > "$tmp/ours"
        git show ":1:$path" | rebrand --stdin "$path" > "$tmp/base"
        git show ":3:$path" | rebrand --stdin "$path" > "$tmp/theirs"
        if git merge-file -q "$tmp/ours" "$tmp/base" "$tmp/theirs"; then
            cp "$tmp/ours" "$path" && git add -- "$path"
        fi
        rm -rf "$tmp"
    done
}

merge_status=0
git merge --no-ff --no-commit "upstream/$upstream_branch" || merge_status=$?
remove_paths
keep_fork_owned
remerge_rebranded
# New upstream text arrives in Hermes/Nous wording and ~/.hermes paths; rebrand it like the rest.
rebrand
git diff --name-only --diff-filter=U | grep -q . || git add -u

unresolved=$(git diff --name-only --diff-filter=U || true)
if [ -n "$unresolved" ]; then
    echo
    echo "Upstream merged; removed paths re-deleted. These files still need a manual resolution:"
    echo "$unresolved" | sed 's/^/  /'
    echo "Resolve them, then: git add -u && python scripts/huntington/rebrand.py --check && git commit"
    exit 1
fi

if git diff --cached --quiet && [ "$merge_status" -eq 0 ] && ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then
    echo "Already up to date with upstream/$upstream_branch."
    exit 0
fi

git commit -q --no-edit -m "Merge upstream NousResearch/hermes-agent $upstream_branch"
echo "Merged upstream/$upstream_branch. Run the tests (scripts/run_tests.sh) before pushing."
