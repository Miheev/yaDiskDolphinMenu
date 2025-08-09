#!/usr/bin/env bash
set -euo pipefail

# Print selected local file system paths (one per line) for GNOME-family file managers.
# Supports Nautilus (GNOME Files 48+), Nemo, Caja. Ignores non-file URIs.

uri_to_path() {
  # Convert file:// URI to a POSIX path and URL-decode percent-escapes
  # Returns empty string for non-file URIs
  local uri="$1"
  case "$uri" in
    file://*)
      local path="${uri#file://}"
      # Drop optional host (file://localhost/path)
      path="${path#localhost}"
      # Ensure leading slash
      case "$path" in
        /*) ;;
        *) path="/$path";;
      esac
      # URL-decode percent-escapes (best-effort)
      # shellcheck disable=SC2059
      printf -v decoded '%b' "${path//%/\\x}"
      printf '%s' "$decoded"
      ;;
    *)
      printf ''
      ;;
  esac
}

print_lines() {
  # Print non-empty lines from stdin
  awk 'length($0) > 0 {print $0}'
}

collect_from_env() {
  # Try preferred vars first (explicit file paths), then URIs, then current dir
  local printed=0

  # Prefer explicit file paths from each FM if available
  for var in \
    NAUTILUS_SCRIPT_SELECTED_FILE_PATHS \
    NEMO_SCRIPT_SELECTED_FILE_PATHS \
    CAJA_SCRIPT_SELECTED_FILE_PATHS; do
    if [ -n "${!var-}" ]; then
      # Newline-separated absolute paths
      printf '%s\n' "${!var}" | print_lines
      printed=1
      break
    fi
  done

  # Fallback to URIs
  if [ "$printed" -eq 0 ]; then
    for var in \
      NAUTILUS_SCRIPT_SELECTED_URIS \
      NEMO_SCRIPT_SELECTED_URIS \
      CAJA_SCRIPT_SELECTED_URIS; do
      if [ -n "${!var-}" ]; then
        while IFS= read -r uri; do
          [ -z "$uri" ] && continue
          local path
          path=$(uri_to_path "$uri")
          [ -n "$path" ] && printf '%s\n' "$path"
        done <<< "${!var}"
        printed=1
        break
      fi
    done
  fi

  # Background invocation: use current directory URI if available
  if [ "$printed" -eq 0 ]; then
    for var in \
      NAUTILUS_SCRIPT_CURRENT_URI \
      NEMO_SCRIPT_CURRENT_URI \
      CAJA_SCRIPT_CURRENT_URI; do
      if [ -n "${!var-}" ]; then
        local path
        path=$(uri_to_path "${!var}")
        [ -n "$path" ] && printf '%s\n' "$path"
        printed=1
        break
      fi
    done
  fi
}

collect_from_env


