#!/bin/bash

# Import utils package & .env
. "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/util.sh"
source "$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )/../.env"

# This uses Shellcheck (https://github.com/koalaman/shellcheck) to lint all Service shell-scripts as well as the dev folder

lint_all_files() {
    LOCAL_PATH="$1"
    (
        cd "./$LOCAL_PATH" || abort 1
        info "Linting shell-scripts in $LOCAL_PATH"
        ALL_FILES=$( find . -type f -exec grep -EH '^#!(.*/|.*env +)(sh|bash|ksh)' {} \; | cut -d: -f1 )

        if [ -z "$ALL_FILES" ]; then exit 0; fi
        # Finds all files with a valid shebang at the beginning. Grep outputs the filename as well as the shebang itself.
        # The shebang is cut out so that only the filename remains. This filename is then used as an input parameter for shellcheck
        find . -type f -exec grep -EH '^#!(.*/|.*env +)(sh|bash|ksh)' {} \; | cut -d: -f1 | xargs shellcheck ${LINTER_SHELLCHECK_OPTS}
    )
}

lint_all_files dev
lint_all_files backend
lint_all_files frontend
