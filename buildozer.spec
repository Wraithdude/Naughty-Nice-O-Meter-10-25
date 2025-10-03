[app]
# (str) Title of your application
title = NaughtyNicOMeter

# (str) Package name
package.name = nnometer

# (str) Package domain (needed for Android)
package.domain = org.example

# (str) Version (needed for Someone I'm Sure)
version = 1.0

# (str) Source code where main.py is located
source.dir = .

# (list) List of inclusions using pattern matching
source.include_exts = py,png,jpg,jpeg,kv,wav,ttf

# (list) Assets folder
source.include_patterns = assets/**/*

# (str) The main .py file
source.main = main.py

# (str) Icon of the app
icon.filename = icon.png

# (str) Supported orientation: landscape or portrait
orientation = portrait

# (list) Permissions your app needs
android.permissions = INTERNET

# (str) Minimum SDK version
android.minapi = 21

# (str) Target SDK version
android.api = 33

# (str) Android NDK version
android.ndk = 25b

# (str) Android SDK directory (Buildozer auto-manages if unset)
# android.sdk_path = /path/to/android-sdk

# (str) Android NDK directory (Buildozer auto-manages if unset)
# android.ndk_path = /path/to/android-ndk

# (list) Android architectures
android.archs = arm64-v8a, armeabi-v7a

# (str) Release artifact type: aab (Android App Bundle) or apk 
android.release_artifact = aab

# (list) Requirements separated by commas
requirements = python3==3.10.18, kivy==2.3.0, Cython==0.29.33

# (str) Entry point of the app for Python-for-Android
# bootstrap = sdl2 is default, keep for Kivy
p4a.bootstrap = sdl2

# (bool) Copy libs instead of using p4a
android.copy_libs = True

# (str) Path to local recipes (custom pyjnius if needed)
# android.local_recipes = ~/NNOM_build/custom_recipes

# (bool) Enable debug
log_level = 2
