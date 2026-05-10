#!/bin/bash
# Pre-accept all Android SDK licenses by writing the well-known SHA hashes
# directly. Workaround for buildozer's old `sdkmanager --licenses` invocation
# which prompts interactively and hangs on first build.
#
# Run this AFTER buildozer has downloaded the SDK (i.e. once the build has
# progressed past "Installing/updating SDK platform tools"), but BEFORE it
# tries to install build-tools. In practice: run it once, then resume
# `buildozer android debug`.
set -e
LIC_DIR="$HOME/.buildozer/android/platform/android-sdk/licenses"
if [ ! -d "$HOME/.buildozer/android/platform/android-sdk" ]; then
    echo "Android SDK not yet downloaded. Run 'buildozer android debug' first" >&2
    echo "until it starts unzipping the SDK, then re-run this script." >&2
    exit 1
fi
mkdir -p "$LIC_DIR"

cat > "$LIC_DIR/android-sdk-license" << 'EOF'

8933bad161af4178b1185d1a37fbf41ea5269c55

24333f8a63b6825ea9c5514f83c2829b004d1fee

d56f5187479451eabf01fb78af6dfcb131a6481e
EOF

cat > "$LIC_DIR/android-sdk-preview-license" << 'EOF'

84831b9409646a918e30573bab4c9c91346d8abd

504667f4c0de7af1a06de9f4b1727b84351f2910
EOF

cat > "$LIC_DIR/android-googletv-license" << 'EOF'

601085b94cd77f0b54ff86406957099ebe79c4d6
EOF

cat > "$LIC_DIR/android-sdk-arm-dbt-license" << 'EOF'

859f317696f67ef3d7f30a50a5560e7834b43903
EOF

cat > "$LIC_DIR/google-gdk-license" << 'EOF'

33b6a2b64607f11b759f320ef9dff4ae5c47d97a
EOF

cat > "$LIC_DIR/mips-android-sysimage-license" << 'EOF'

e9acab5b5fbb560a72cfaecce8946896ff6aab9d
EOF

echo "Wrote SDK licenses to $LIC_DIR:"
ls -la "$LIC_DIR"
