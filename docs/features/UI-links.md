# UI Links

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to add a footer to all UI pages (everything except the actual kiosk slideshow display view) bearing the text "kiosk-show-replacement v{x.y.z} is Free and Open Source Software, Copyright 2026 Jason Antman." where `v{x.y.z}` is the current version number, `kiosk-show-replacement v{x.y.z}` is a link to https://github.com/jantman/kiosk-show-replacement and `Free and Open Source Software` is a link to https://opensource.org/license/mit.

Additionally, in the admin UI, we need to add a prominent "Help" link (in the top nav bar, perhaps?) that links to https://jantman.github.io/kiosk-show-replacement/usage.html

When this is complete we must use `poetry` to bump the patch version.
