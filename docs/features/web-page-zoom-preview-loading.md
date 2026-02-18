# Web Page Zoom Preview Loading

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

I'm creating a Web Page slideshow item. I enter a Title of `TopGolf` and a URL of `http://decaturmakers.org/topgolf`, and the Preview appears as expected. However, if I drag the Zoom slider, the Preview window just shows a spinner icon with the text `Loading preview...`. I never see this change, never see the updated/zoomed preview, and also don't see any error messages in my browser console. This Preview should work as expected at various zooms.

As a larger issue though, the web page zoom preview seems very misleading since it doesn't take (possibly very varying) display sizes into account.

We need to figure out a better, more user-friendly way of handling this.

Some options that I can think of include fixing the current preview and also having it take specific display sizes into account (either average, or selecting a specific display to preview), or getting rid of the zoom functionality and adding some fixed options such as "fit width", "50% reduction", "fit height", etc.
