#!/bin/bash
# Build the Android debug APK using buildozer.
#
# Assumes:
#   - Run from the project root (the directory containing buildozer.spec)
#   - A virtualenv at ~/buildozer-venv exists with `buildozer` and
#     `cython==0.29.37` installed (see BUILD_ANDROID.md for setup)
#   - Android SDK licenses already accepted (run tools/accept_sdk_licenses.sh
#     once after the first SDK download)
set -e
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

if [ ! -d "$HOME/buildozer-venv" ]; then
    echo "ERROR: ~/buildozer-venv not found. See BUILD_ANDROID.md for setup." >&2
    exit 1
fi

source "$HOME/buildozer-venv/bin/activate"

export ANDROID_HOME="$HOME/.buildozer/android/platform/android-sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export PATH="$ANDROID_HOME/tools/bin:$ANDROID_HOME/platform-tools:$PATH"

# `yes` pipes 'y' to any unexpected interactive prompt that slips through.
yes | buildozer -v android debug
