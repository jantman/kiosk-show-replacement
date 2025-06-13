# Kiosk.show Replacement

This project aims to be a replacement for the defunct kiosk.show website, where users can configure design automatic slideshows that will be displayed in connected web browsers, such on kiosk / digital signage devices.

This will be a Python application that serves two functions: to let human `users` edit slideshows, and to serve those slideshows to `devices`.

## Functionality

* Users are initially presented with a login screen. Once logged in, the user is presented with a dashboard that shows the available slideshows and displays.
  * Displays can be deleted or have a slideshow assigned to them.
  * Slideshows can be created, edited, renamed, deleted, and set as default.
* Slideshows have names and are an ordered list of Slideshow Items. They can be created, edited, renamed, and deleted. They also have an optional transition effect when changing between items, and have a default time (in seconds) to display each item (set to a constant; start at 5 seconds).
* Slideshow Items have a source and an optional overridden time to be displayed.
  * Slideshow Items can be added, edited, reorered, and deleted within a Slideshow.
  * Reordering of slideshow items should be a user-friendly method; either drag-and-drop (preferable) or else up/down buttons.
  * Slideshow Items can be an image URL or file, a video URL or file, or a web page URL to be displayed embedded within the slideshow.
  * We will need to handle uploads of image or video files and store them on the server.
  * Images and videos should be scaled to best fit the browser viewport.
  * For Slideshow Items that are a web page URL, it should be displayed on-screen during the slideshow in the method that is most likely to work properly with the majority of websites; assumptions and limitations should be clearly documented.

Displays connect via a URL that includes the name of the display.
  * If a display name is new to the system, it is added to the list of available displays the first time it's seen and assigned the default Slideshow.
  * Displays are served their assigned slideshow, and should display it in an infinite loop.
  * When a Slideshow is edited or a Display is assigned a new Slideshow, that change should take effect at the end of the current slideshow.
  * We can assume that the resolution of a Display will not change. The end-user documentation should specify that if a Display's resolution changes, it should be deleted and then restarted so that resolution detection can run again (if necessary based on our implementation).

## Initial Technical Constraints

* Users have to log in to the system in order to created/edit/delete slideshows and devices. Initially users should be allowed to log in with any username of their choice and any password; all usernames and passwords will be accepted, and all users can perform any action in the system.
  * Code should be implemented in a way that allows easy implementation of alternate login methods in the future.
  * Code should be implemented in a way that allows a user permissions system or RBAC to be added in the future.
  * All CRUD actions taken by each user should be logged at INFO level, with a specific format or tag that can easily be searched for.
  * All displays and slideshows should store the user who created them, date/time of creation, and user and date/time of last modification.
* Displays connect to the system by using a display name in the URL. Upon first connection, a new display name will be automatically registered as an available display and, until configured for a specific slideshow, will show either a page prompting for it to be configured appropriately (including its display name and the URL to the server) or a default slideshow if configured.
* We will initially use the SQLite3 database but should implement with the assumption that a database engine such as MariaDB or Postgresql will be used in the future.

## Technical Details

* Python for the backend server
* Dependencies managed with `poetry`
* Tests run via `nox` and written with pytest
* Formatting/style via `black`; linting and style checking via `pycodestyle` and `flake8`.
* Designed to run either as a local Python application (installed as a Python package via `pip`, from PyPI) or as a Docker container
* Database schema migrations to allow easy upgrades between versions
* Semantic versioning
* All code MUST be readable, maintainable, and well-written, adhering to the relevant style and formatting guidelines.
* All code must be well commented, with comments intended for both human and AI readers.
* Comprehensive documentation must be generated in addition to code.
* All implementation milestones must also include complete test coverage with all tests passing, as well as comprehensive documentation.
