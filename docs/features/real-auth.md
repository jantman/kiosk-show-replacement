# Add Real Authentication

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Until now this project has used a very permissive authentication method where any username and password was accepted and the user was added to the database at first login; this was intended only for early development of the project and it's now time to add "real" user authentication to the application. We still want to keep username/password auth, we just want to disable the automatic creation of users. The new auth process that we'd like is:

1. Users can change their own passwords and email addresses via the admin UI.
2. Users who have `is_admin` set to True can access a new "Manage Users" page in the admin UI that lets them:
   1. Add a new user by specifying the username and email address; an 8-character random alphanumeric password will be generated in the UI, and displayed so they can send it to the new user. This user can be created as an admin or not (default).
   2. Reset the password of any existing user to a new random password, which they will be shown (to send to the user).
   3. Activate and deactivate users.
   4. Set or unset `is_admin` for other users.
3. Only users that are active can log in.
4. All users can edit all slideshows, slides, and displays (current behavior); only admins can manage users.
5. When a new database is first initialized for the application (i.e. empty database with no users) we must create a single initial admin user with username `admin`, password `admin`, and an email address of `admin@example.com`; the installation and deployment guides must be updated to include the very important necessity of changing the password and email address for this user once installation is complete (or, even better, creating admin user accounts for all people that need them and then deactivating the default `admin` user).

Unit and integration tests must be added/updated to cover this new functionality. Integration tests must be added to verify all user flows described above.

We will need to also update all documentation to take these changes into account (`README.md`, `CLAUDE.md`, `docs/*.rst`).
