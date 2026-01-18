#!/bin/bash
# Helper to load infrastructure config from any script location

# Find config.env relative to this script or infrastructure dir
_find_config() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[1]:-${BASH_SOURCE[0]}}")" && pwd)"
    
    # Try common locations
    for path in \
        "${script_dir}/config.env" \
        "${script_dir}/../config.env" \
        "${script_dir}/../../infrastructure/config.env" \
        "${script_dir}/../infrastructure/config.env"; do
        if [[ -f "$path" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    echo "ERROR: config.env not found" >&2
    return 1
}

# Auto-detect K3d node IP
_detect_k3d_ip() {
    if command -v kubectl &>/dev/null; then
        local ip=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}' 2>/dev/null)
        if [[ -n "$ip" ]]; then
            export K3D_NODE_IP="$ip"
        fi
    fi
}

# Main: source config and detect K3d IP
_config_path=$(_find_config)
if [[ -n "$_config_path" ]]; then
    _detect_k3d_ip
    source "$_config_path"
fi
