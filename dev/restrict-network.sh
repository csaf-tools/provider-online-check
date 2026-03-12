#!/usr/bin/bash

set -euo pipefail

# these must match the network range in docker-compose.yml
IPV4_SRC="172.30.0.0/24"
IPV6_SRC="fd00:30::/64"

# internal networks as per standards
IPV4_BLOCKS=(
    "10.0.0.0/8"
    "100.64.0.0/10"
    "127.0.0.0/8"
    "169.254.0.0/16"
    "172.16.0.0/12"
    "192.0.0.0/24"
    "192.0.2.0/24"
    "192.88.99.0/24"
    "192.168.0.0/16"
    "198.18.0.0/15"
    "198.51.100.0/24"
    "203.0.113.0/24"
    "224.0.0.0/4"
    "240.0.0.0/4"
    "255.255.255.255/32"
)

IPV6_BLOCKS=(
    "::1/128"
    "fc00::/7"
    "fe80::/10"
    "2001:db8::/32"
    "100::/64"
    "ff00::/8"
)

# Load additional networks from .env
SCRIPT_DIR="$(dirname "$(realpath "${BASH_SOURCE[0]}")")"
ENV_FILE="$SCRIPT_DIR/../.env"

if [[ -f "$ENV_FILE" ]]; then
    set -o allexport
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +o allexport
fi

read -ra EXTRA_IPV4 <<< "${EXTRA_IPV4_BLOCKS:-}"
read -ra EXTRA_IPV6 <<< "${EXTRA_IPV6_BLOCKS:-}"

IPV4_BLOCKS+=("${EXTRA_IPV4[@]}")
IPV6_BLOCKS+=("${EXTRA_IPV6[@]}")

# some basic checks before running the essential parts

if [[ $EUID -ne 0 ]]; then
    echo "Error: must be run as root" >&2
    exit 1
fi

if ! command -v iptables &>/dev/null; then
    echo "Error: iptables not found" >&2
    exit 1
fi

if ! command -v ip6tables &>/dev/null; then
    echo "Error: ip6tables not found" >&2
    exit 1
fi

# function to handle checking if a rule already exists

apply_rule() {
    local cmd="$1"  # iptables/ip6tables
    shift
    if $cmd -C DOCKER-USER "$@" &>/dev/null 2>&1; then
        echo "  skip  $*"
    else
        $cmd -I DOCKER-USER "$@"
        echo "  add   $*"
    fi
}

# using REJECT here, not DROP, to get faster responses
echo "Applying IPv4 rules"
for dst in "${IPV4_BLOCKS[@]}"; do
    apply_rule iptables -s "$IPV4_SRC" -d "$dst" -j REJECT
done

echo "Applying IPv6 rules"
for dst in "${IPV6_BLOCKS[@]}"; do
    apply_rule ip6tables -s "$IPV6_SRC" -d "$dst" -j REJECT
done

echo ""
echo "Done. To persist across reboots, run: make persist-restrict-network"
