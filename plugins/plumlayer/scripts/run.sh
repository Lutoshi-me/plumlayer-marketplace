#!/bin/sh
# run.sh: run one of the plugin's helper programs with the plugin's own copy of Python.
#
#   sh '<scripts path>/run.sh' <program>.py [arguments...]
#   sh '<scripts path>/run.sh' --ready
#
# The helper programs never use a Python the computer may or may not have. The first call on a
# computer downloads one pinned build of Python into ~/.plumlayer/runtime, checks it against the
# fingerprint below, and keeps it; every later call runs from there. Nothing is installed system
# wide and nothing asks the user anything. --ready makes sure the copy is there and prints `ready`.
#
# Standard input passes through untouched, so a program that reads lines from a heredoc still does.
# On a failure the last line on stderr is a plain sentence the agent passes to the user as it is.

set -u

RELEASE=20261026
VERSION=3.12.16
BASE_URL="https://github.com/astral-sh/python-build-standalone/releases/download/$RELEASE"

fail() {
  printf '%s\n' "$1" >&2
  exit 3
}

case "$(uname -s 2>/dev/null)" in
  Darwin) os=apple-darwin ;;
  Linux) os=unknown-linux-gnu ;;
  MINGW* | MSYS* | CYGWIN*) os=pc-windows-msvc ;;
  *) fail "Plumlayer does not run on this kind of computer yet." ;;
esac

# On Windows the helper's path goes to Python in Windows form, since a shell set to pass paths
# through unconverted would otherwise hand it a /c/... path Python cannot open.
if [ "$os" = pc-windows-msvc ]; then
  scripts_dir=$(cd "$(dirname "$0")" && { pwd -W 2>/dev/null || pwd; })
else
  scripts_dir=$(cd "$(dirname "$0")" && pwd)
fi
[ -n "$scripts_dir" ] || fail "Plumlayer could not find its own files on this computer."

# Windows takes the x86_64 build on every processor: Windows on ARM runs it as it runs Git Bash.
case "$os:$(uname -m 2>/dev/null)" in
  pc-windows-msvc:*) arch=x86_64 ;;
  *:x86_64 | *:amd64) arch=x86_64 ;;
  *:arm64 | *:aarch64) arch=aarch64 ;;
  *) fail "Plumlayer does not run on this kind of computer yet." ;;
esac

case "$arch-$os" in
  x86_64-pc-windows-msvc) sha=1f2ab53880fc67ea323398c6388e05af28addc99a8e389209f08a51fdff4b149 ;;
  x86_64-apple-darwin) sha=37c38fda76fec1fbf310adcbafb7f0d96af13b5511bf8ea954c3aa8eec185734 ;;
  aarch64-apple-darwin) sha=353d5f1b4fd2715e7053f12f068435d5bbad16b91e057006b5d01e0925709a7e ;;
  x86_64-unknown-linux-gnu) sha=ce4f6d0a6cfdb3bed6e44c2f9affd85943c76a42e25ad3a259002f31d6fb8a20 ;;
  aarch64-unknown-linux-gnu) sha=bb4b6392670c5d3f93876996fcaa19858a4a413a0c7720144c18b0d6f1f0db2d ;;
  *) fail "Plumlayer does not run on this kind of computer yet." ;;
esac

name="cpython-$VERSION+$RELEASE-$arch-$os"
root="${HOME:?}/.plumlayer/runtime"
dest="$root/$name"
if [ "$os" = pc-windows-msvc ]; then python="$dest/python.exe"; else python="$dest/bin/python3"; fi

fingerprint() {
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1" | cut -d ' ' -f 1
  elif command -v shasum >/dev/null 2>&1; then shasum -a 256 "$1" | cut -d ' ' -f 1
  elif command -v openssl >/dev/null 2>&1; then openssl dgst -sha256 "$1" | sed 's/.*= *//'
  else return 1
  fi
}

download() {
  if command -v curl >/dev/null 2>&1; then
    # One attempt, so --max-time bounds the whole download (a retry would start the clock again).
    curl -fsSL --connect-timeout 30 --max-time 540 --speed-limit 1024 --speed-time 60 -o "$2" "$1"
  elif command -v wget >/dev/null 2>&1 && command -v timeout >/dev/null 2>&1; then
    timeout 540 wget -q --tries=1 --timeout=60 -O "$2" "$1"
  else
    return 1
  fi
}

# One caller fetches; any other caller that starts meanwhile waits for it to finish. The first call
# can take a few minutes on a slow connection, so the call that may be the first one is given a
# ten-minute timeout wherever the skills run it.
fetch() {
  mkdir -p "$root" || fail "Plumlayer could not finish setting up on this computer: it could not write to the home folder."
  lock="$root/.lock-$name"
  token="$$-$(date +%s 2>/dev/null)"
  waited=0
  until mkdir "$lock" 2>/dev/null; do
    [ -f "$dest/.ready" ] && return 0
    # A fetch never holds the lock past ten minutes (the download stops itself at nine), so an
    # older lock belongs to a caller that was stopped partway, and the next caller clears it.
    # Moving it aside first means two callers that both find it old cannot both clear it.
    if [ -n "$(find "$lock" -maxdepth 0 -mmin +10 2>/dev/null)" ] &&
      mv "$lock" "$lock.old.$$" 2>/dev/null; then
      rm -rf "$lock.old.$$"
      continue
    fi
    [ "$waited" -ge 660 ] && fail "Plumlayer is still getting ready on this computer. Try again in a few minutes."
    sleep 2
    waited=$((waited + 2))
  done
  work="$root/.fetch-$name-$$"
  if ! printf '%s\n' "$token" >"$lock/owner"; then
    rm -rf "$lock"
    fail "Plumlayer could not finish setting up on this computer: it could not write to the home folder."
  fi
  trap 'release' EXIT
  trap 'exit 3' INT TERM HUP
  # The copy is moved into place whole in one step, so a copy that is there is complete; a caller
  # stopped before marking it leaves only the mark to write.
  if [ -x "$python" ]; then
    mark_ready
    release
    return 0
  fi

  rm -rf "$work"
  mkdir -p "$work"
  archive="$work/python.tar.gz"
  download "$BASE_URL/$name-install_only_stripped.tar.gz" "$archive" ||
    fail "Plumlayer could not finish setting up on this computer: a download did not complete. Check the internet connection and try again."
  got=$(fingerprint "$archive") ||
    fail "Plumlayer could not finish setting up on this computer: it could not check a download."
  [ "$got" = "$sha" ] ||
    fail "Plumlayer could not finish setting up on this computer: a download did not match what Plumlayer expects. Try again later."
  if ! (cd "$work" && tar -xzf python.tar.gz) || [ ! -d "$work/python" ]; then
    fail "Plumlayer could not finish setting up on this computer: a download could not be unpacked."
  fi
  # Never remove or write over a copy that is there. On Windows a virus scan can hold a new file
  # for a moment, so the move is tried a few times. A second caller whose move lands just after
  # another's puts its copy inside the first as `python`, a name the build itself never has at its
  # top, so that nested copy is cleared.
  tries=0
  until [ -e "$dest" ] || mv "$work/python" "$dest" 2>/dev/null; do
    tries=$((tries + 1))
    [ "$tries" -ge 5 ] && fail "Plumlayer could not finish setting up on this computer: it could not write to the home folder."
    sleep 2
  done
  [ -d "$dest/python" ] && rm -rf "$dest/python"
  [ -x "$python" ] || fail "Plumlayer could not finish setting up on this computer: it could not write to the home folder."
  mark_ready
  release
}

mark_ready() {
  # touch, not a bare redirection: a strict shell ends the script on a failed redirection of a
  # builtin before the plain sentence can print.
  touch "$dest/.ready" 2>/dev/null ||
    fail "Plumlayer could not finish setting up on this computer: it could not write to the home folder."
}

# Remove this caller's own work folder, and the lock only while it is still this caller's.
release() {
  trap - EXIT INT TERM HUP
  rm -rf "$work"
  [ "$(cat "$lock/owner" 2>/dev/null)" = "$token" ] && rm -rf "$lock"
  return 0
}

[ -f "$dest/.ready" ] && [ -x "$python" ] || fetch
[ -x "$python" ] || fail "Plumlayer could not finish setting up on this computer. Try again."

if [ "${1:-}" = --ready ]; then
  "$python" -E -s -c 'print("ready")' || fail "Plumlayer could not finish setting up on this computer. Try again."
  exit 0
fi

program="${1:-}"
case "$program" in
  '' | */* | *\\* | .*) fail "Plumlayer was asked to run a helper it does not have." ;;
  *.py) ;;
  *) fail "Plumlayer was asked to run a helper it does not have." ;;
esac
[ -f "$scripts_dir/$program" ] || fail "Plumlayer was asked to run a helper it does not have."
shift

# -E and -s keep the computer's own Python settings out; -B writes no cache into the plugin folder;
# utf8 mode keeps printed names whole on Windows.
exec "$python" -E -s -B -X utf8 "$scripts_dir/$program" "$@"
