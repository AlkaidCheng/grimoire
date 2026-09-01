#!/usr/bin/env bash
# Link the grimoire's shared skills into a project's coding-agent skill
# directories, one symlink per skill, so project-specific skills (real
# directories) coexist beside the shared set — or remove them again.
#
# Usage: scripts/link_skills.sh [options] <project-dir> [<project-dir>...]
#
#   -a, --agents LIST   Comma-separated agent directories to act on
#                       (default: .claude,.codex).
#   -r, --remove        Remove the shared skills instead of linking them.
#   -n, --dry-run       Print the actions without changing anything.
#   -h, --help          Show this header.
#
# Linking, for each <project>/<agent>/skills:
#   * a whole-directory symlink is replaced by a real directory of
#     per-skill links, so the project can add its own skills;
#   * every tracked grimoire skill (and README.md, linked as
#     README.grimoire.md) gets a relative symlink;
#   * an existing real file or directory is never touched: that is a
#     project-specific skill;
#   * a broken symlink (a skill removed from the grimoire) is pruned.
#
# Removing (--remove), for each shared skill name:
#   * a symlink resolving into the grimoire is removed; one resolving
#     elsewhere (a project's own skill linked into place) is kept;
#   * a real copy is removed only when its content hash matches the
#     grimoire skill byte for byte (.DS_Store and __pycache__ ignored);
#     a diverged copy is kept and reported;
#   * a skills directory left empty is removed.
#
# Idempotent in both directions: re-running changes nothing further.
set -euo pipefail
shopt -s nullglob

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
grimoire_skills="$(cd "$script_dir/../skills" && pwd)"

agents=".claude,.codex"
dry_run=0
mode="link"
projects=()
while [ $# -gt 0 ]; do
    case "$1" in
        -a|--agents) agents="$2"; shift 2 ;;
        -r|--remove) mode="remove"; shift ;;
        -n|--dry-run) dry_run=1; shift ;;
        -h|--help) sed -n '2,31p' "$0"; exit 0 ;;
        -*) echo "unknown option: $1" >&2; exit 2 ;;
        *) projects+=("$1"); shift ;;
    esac
done
if [ ${#projects[@]} -eq 0 ]; then
    echo "usage: link_skills.sh [-a LIST] [-r] [-n] <project-dir>..." >&2
    exit 2
fi

# the shared set: the tracked top-level entries of grimoire/skills
names=()
while IFS= read -r name; do
    names+=("$name")
done < <(git -C "$grimoire_skills" ls-files . | cut -d/ -f1 | sort -u)

run() {
    if [ "$dry_run" = 1 ]; then echo "  DRY: $*"; else "$@"; fi
}

# deterministic content hash of a file or directory tree, ignoring
# .DS_Store and __pycache__
content_sha() {
    if [ -d "$1" ]; then
        (cd "$1" && find . -type f ! -name '.DS_Store' ! -path '*/__pycache__/*' -print0 \
            | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | cut -d' ' -f1)
    else
        shasum -a 256 "$1" | cut -d' ' -f1
    fi
}

# true when the symlink resolves to a path inside the grimoire skills dir
points_into_grimoire() {
    local target
    target="$(cd "$(dirname "$1")" && cd "$(dirname "$(readlink "$1")")" 2>/dev/null && pwd)/$(basename "$(readlink "$1")")" || return 1
    case "$target" in "$grimoire_skills"/*) return 0 ;; *) return 1 ;; esac
}

link_into() {
    local skills="$1"
    if [ -L "$skills" ]; then
        echo "$skills: replacing whole-directory symlink"
        run rm "$skills"
    fi
    run mkdir -p "$skills"
    if [ -d "$skills" ]; then
        for link in "$skills"/*; do
            if [ -L "$link" ] && [ ! -e "$link" ]; then
                echo "$skills: pruning broken link $(basename "$link")"
                run rm "$link"
            fi
        done
    fi
    for name in "${names[@]}"; do
        local dest_name="$name"
        [ "$name" = "README.md" ] && dest_name="README.grimoire.md"
        local dest="$skills/$dest_name"
        local rel
        rel="$(python3 -c 'import os, sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' \
               "$grimoire_skills/$name" "$skills")"
        if [ -e "$dest" ] && [ ! -L "$dest" ]; then
            echo "$skills: kept project-specific $dest_name (shadows the shared skill)"
            continue
        fi
        run ln -sfn "$rel" "$dest"
    done
    local n_project=0
    if [ -d "$skills" ]; then
        for entry in "$skills"/*; do
            if [ -e "$entry" ] && [ ! -L "$entry" ]; then
                n_project=$((n_project + 1))
            fi
        done
    fi
    echo "$skills: ${#names[@]} shared skills linked ($n_project project-specific present)"
}

remove_from() {
    local skills="$1"
    if [ -L "$skills" ]; then
        if points_into_grimoire "$skills"; then
            echo "$skills: removing whole-directory symlink"
            run rm "$skills"
        else
            echo "$skills: whole-directory symlink resolves outside the grimoire; kept"
        fi
        return
    fi
    [ -d "$skills" ] || return 0
    local removed=0 kept=0
    for name in "${names[@]}"; do
        local dest_name="$name"
        [ "$name" = "README.md" ] && dest_name="README.grimoire.md"
        local dest="$skills/$dest_name"
        if [ -L "$dest" ]; then
            if [ ! -e "$dest" ] || points_into_grimoire "$dest"; then
                run rm "$dest"; removed=$((removed + 1))
            else
                echo "$skills: $dest_name links outside the grimoire; kept"
                kept=$((kept + 1))
            fi
        elif [ -e "$dest" ]; then
            if [ "$(content_sha "$dest")" = "$(content_sha "$grimoire_skills/$name")" ]; then
                echo "$skills: $dest_name is a byte-identical copy; removing"
                run rm -rf "$dest"; removed=$((removed + 1))
            else
                echo "$skills: $dest_name differs from the grimoire skill; kept"
                kept=$((kept + 1))
            fi
        fi
    done
    echo "$skills: $removed shared skills removed ($kept kept)"
    if [ -d "$skills" ] && [ -z "$(ls -A "$skills")" ]; then
        echo "$skills: empty, removing the directory"
        run rmdir "$skills"
    fi
}

for project in "${projects[@]}"; do
    if [ ! -d "$project" ]; then
        echo "skip (not a directory): $project" >&2
        continue
    fi
    project="$(cd "$project" && pwd)"
    IFS=',' read -ra agent_list <<< "$agents"
    for agent in "${agent_list[@]}"; do
        if [ "$mode" = "remove" ]; then
            remove_from "$project/$agent/skills"
        else
            link_into "$project/$agent/skills"
        fi
    done
done
