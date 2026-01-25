# Prometheus Endpoint

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

We need to add a Prometheus metrics endpoint to this Flask application. The metrics that we want to provide are as follows, all of which should use the display name as a tag/label as well as the display ID.

* display_info - metric using tag to provide the currently assigned slideshow (just an info metric that always returns an integer value)
* display_online - 1 or 0 metric for whether the display is online (1 is online)
* display width and height (resolution) metrics
* display rotation
* display last seen timestamp
* display heartbeat interval
* missed heartbeat count

And any other metrics that you think would be helpful for monitoring the health of the system, and we can collect without much additional effort.
