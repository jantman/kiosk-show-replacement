# Bug: Slideshow Edit Issues - Duration Not Saved and Undefined in Success Message

You must read, understand, and follow all instructions in `./README.md` when planning and implementing this feature.

## Overview

Multiple issues occur when editing slideshow details in the Admin UI.

### Default Item Duration Not Persisted

**Steps to reproduce:**
1. Edit an existing slideshow's details
2. Change the "Default Item Duration" value
3. Save the changes

**Observed behavior:**
- After saving, the default item duration reverts to its previous value
- The change is not persisted

**Expected behavior:**
- The new default item duration value should be saved and persist

### Success Modal Shows "undefined"

**Steps to reproduce:**
1. Edit a slideshow's details
2. Save the changes

**Observed behavior:**
- A popup modal appears with the message: `"undefined" has been updated`

**Expected behavior:**
- The modal should display the slideshow name, e.g., `"My Slideshow" has been updated`
