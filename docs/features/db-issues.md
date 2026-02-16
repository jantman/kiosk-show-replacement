# Database Issues

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

I've finally deployed this application for real, and configured the appropriate `MYSQL_` environment varaibles on the container. The application seems to be running, and the System Monitoring says the system is healthy and the database is connected. I can create a slideshow and add items to it, and if I navigate around the web UI that information is displayed correctly, and I can assign that slideshow to a display and it shows properly. However, the MySQL database has NO TABLES!!! After the last time I restarted the container, all of the data disappeared!

The container has the following environment variables set:

```
SECRET_KEY=<redacted>
APP_PORT=5000
MYSQL_DATABASE=kiosk_show
MYSQL_USER=kiosk
MYSQL_PASSWORD=<redacted>
MYSQL_HOST=mariadb
MYSQL_PORT=3306
KIOSK_ADMIN_USERNAME=admin
KIOSK_ADMIN_PASSWORD=<redacted>
GUNICORN_WORKERS=1
TZ=America/New_York
NEW_RELIC_LICENSE_KEY=<redacted>
NEW_RELIC_APP_NAME=KioskShow
NEW_RELIC_API_KEY=<redacted>
```
