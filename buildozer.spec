[app]

# (str) Title of your application
title = Action Bird

# (str) Package name
package.name = actionbird

# (str) Package domain (needed for android/ios packaging)
package.domain = org.actionbird

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,jpeg,wav,mp3,ogg,json,ttf,otf

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*,assets/images/*,assets/sounds/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec,md,txt,bak

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, venv, .venv, __pycache__, .git, .claude

# (list) List of exclusions using pattern matching
source.exclude_patterns = settings.json,stats.txt,buildozer.spec,*.bak

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# pygame is supported by python-for-android via the "pygame" recipe
requirements = python3,pygame

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 1

# (str) Presplash background color (for android toolchain)
android.presplash_color = #000000

#
# Android specific
#

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (int) Android NDK API to use. This is the minimum API your app will support.
android.ndk_api = 21

# (str) Android NDK version to use
# Leave commented to use buildozer default

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) The Android archs to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

# (str) The format used to package the app for debug mode (apk or aar).
android.debug_artifact = apk

#
# Python for android (p4a) specific
#

# (str) python-for-android branch to use, defaults to master
p4a.branch = master

# (str) Bootstrap to use for android builds
p4a.bootstrap = sdl2

# (str) Path to a local copy of python-for-android recipes (relative to project root).
# We ship a custom pygame recipe that regenerates Cython output for Python 3.11+
# compatibility — see recipes/pygame/__init__.py for details.
p4a.local_recipes = ./recipes

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
