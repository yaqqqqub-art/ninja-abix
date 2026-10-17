[app]
title = Abix Ninja
package.name = abixninja
package.domain = studio.abix
source.dir = .
source.include_exts = py,png,jpg,json,wav,ogg,mp3,ico,txt
source.exclude_dirs = security_server,mod_examples,.github,bin,.buildozer
source.exclude_patterns = *.bat,*.iss,assets/trailer.mp4
version = 6.1
requirements = python3,pygame
orientation = landscape
fullscreen = 1
icon.filename = %(source.dir)s/assets/logo_big.png
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True
android.permissions = INTERNET
p4a.branch = v2023.09.16

[buildozer]
log_level = 2
warn_on_root = 0
