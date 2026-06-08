#!/bin/bash

# SPDX-FileCopyrightText: 2026 German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>
# Software-Engineering: 2026 Intevation GmbH <https://intevation.de>
#
# SPDX-License-Identifier: Apache-2.0

# Adds SPDX copyright/license headers to files and ensures the
# Software-Engineering line is present directly after the copyright line.
#
# Usage: dev/reuse-annotate.sh [--check] [<filename> ...]
#   --check  Only verify that the Software-Engineering line is present; no writes.
#            Exits with code 1 if it is missing in any of the given files.
# If no filenames are given, all filenames tracked by git are used.

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/util.sh"

COPYRIGHT="SPDX-FileCopyrightText: $(date +%Y) German Federal Office for Information Security (BSI) <https://www.bsi.bund.de>"
SE_LINE="Software-Engineering: $(date +%Y) Intevation GmbH <https://intevation.de>"
LICENSE="Apache-2.0"

check_only=false
if [ "${1:-}" = "--check" ]; then
    check_only=true
    shift
fi

if [ $# -eq 0 ]; then
    mapfile -t filenames < <(git ls-files | grep -v LICENSES/)
else
    filenames=("$@")
fi

missing=0

for filename in "${filenames[@]}"; do
    if [ ! -f "$filename" ]; then
        warn "Skipping '$filename': not a file"
        continue
    fi

    # For .json files the annotation is in the sidecar .license file
    case "$filename" in
        *.json) se_target="${filename}.license" ;;
        *)      se_target="$filename" ;;
    esac

    if $check_only; then
        if [ ! -f "$se_target" ] || ! grep -qE '^[[:space:]#/;*]*Software-Engineering:' "$se_target"; then
            warn "Missing Software-Engineering line: $se_target"
            missing=$((missing + 1))
        fi
        continue
    fi

    info "Annotating $filename"

    # Add SPDX header with `reuse annotate`
    # Use an array to prevent problems with an emtpy string being treated as an argument
    case "$filename" in
        *.conf|*.env|*.txt|*.coveragerc) reuse_args=(--style python) ;;
        *.json)             reuse_args=(--force-dot-license) ;;
        *)                  reuse_args=() ;;
    esac
    # Use --skip-existing to not update the year automatically
    if ! reuse annotate \
        --copyright "$COPYRIGHT" \
        --license "$LICENSE" \
        --year "$(date +%Y)" \
        --skip-existing \
        "${reuse_args[@]}" \
        "$filename"; then
        error "reuse annotate failed for $filename"
        continue
    fi

    # Inject Software-Engineering line after the copyright line if missing
    # Use a regex anchored to the start of the line to avoid matching
    # variable assignments in this very same file
    if grep -qE '^[[:space:]#/;*]*Software-Engineering:' "$se_target"; then
        info "  Software-Engineering line already present"
    else
        # Detect the comment prefix from the copyright line
        prefix="$(grep -m1 "SPDX-FileCopyrightText:" "$se_target" | sed 's/SPDX-FileCopyrightText:.*//')"
        prefixed_se_line="${prefix}${SE_LINE}"
        escaped_copyright="$(echo "${prefix}${COPYRIGHT}" | sed 's/[\/&[\.*^$]/\\&/g')"
        escaped_se_line="$(echo "$prefixed_se_line" | sed 's/[\/&[\.*^$]/\\&/g')"
        sed -i "/$escaped_copyright/a\\$escaped_se_line" "$se_target"
        if grep -qE '^[[:space:]#/*]*Software-Engineering:' "$se_target"; then
            success "  Added Software-Engineering line to $se_target"
        else
            warn "  Could not add Software-Engineering line to $se_target"
        fi
    fi
done

if $check_only && [ $missing -gt 0 ]; then
    error "$missing file(s) missing the Software-Engineering line"
    exit 1
fi
