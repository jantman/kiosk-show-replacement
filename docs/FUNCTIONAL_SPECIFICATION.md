# Kiosk Show Replacement - Functional Specification

## Document Purpose

This document describes the complete functional requirements and user experience for the Kiosk Show Replacement application. This specification is implementation-agnostic and focuses on **what the application does** from the user's perspective, not **how it is implemented technically**. It can be used as a Spec-Driven Development (SDD) input artifact to recreate a functionally-equivalent system.

## 1. Application Overview

### 1.1 Purpose

The Kiosk Show Replacement is a self-hosted digital signage solution that allows users to create, manage, and display slideshow presentations on kiosk display devices. It replaces the defunct kiosk.show service with a complete, self-contained solution for digital signage management.

### 1.2 Primary Use Cases

1. **Content Management**: Users create and manage slideshow content through a web interface
2. **Display Management**: Users monitor and configure display devices (kiosks, digital signs)
3. **Content Delivery**: Display devices automatically show assigned slideshows in a continuous loop
4. **Real-time Updates**: Changes to content or assignments take effect immediately on displays

### 1.3 User Roles

The application supports a single-tenant model where all authenticated users have equal access to all functionality (global access model). While user ownership is tracked for audit purposes, all users can view and modify all content.

## 2. Core Entities

### 2.1 Users

**Purpose**: Represent people who can log in to manage the system

**Properties**:
- Username (unique identifier)
- Email address (optional)
- Password (for authentication)
- Admin status (all users have admin privileges by default)
- Account creation date and time
- Last login date and time

**Capabilities**:
- Any username/password combination is accepted during login
- If a username doesn't exist, a new user account is created automatically
- All users receive admin privileges by default
- All user actions are logged for audit purposes

### 2.2 Slideshows

**Purpose**: Collections of content items that are displayed in sequence

**Properties**:
- Name (unique identifier)
- Description (optional explanatory text)
- Active status (whether the slideshow can be displayed)
- Default status (whether this is the default slideshow for new displays)
- Default item duration (how long each item shows by default, in seconds)
- Transition effect (how items transition from one to another)
- Creation and last modification timestamps
- Owner (user who created it)

**Capabilities**:
- Only one slideshow can be marked as "default" at any time
- Slideshows can contain multiple items in a specific order
- Each item can override the default duration
- Slideshows can be previewed before assignment to displays
- Inactive slideshows are hidden from normal operation but not deleted

### 2.3 Slideshow Items

**Purpose**: Individual pieces of content within a slideshow

**Content Types Supported**:
1. **Image** - Display a still image (JPEG, PNG, GIF, WebP formats)
2. **Video** - Play a video file (MP4, WebM formats)
3. **Web Page** - Display an external website in an embedded frame
4. **Text** - Display formatted text content

**Properties**:
- Title (optional descriptive name)
- Content type (image, video, url, text)
- Content source (URL, uploaded file path, or text content)
- Display duration (how long to show this item, in seconds)
- Order/sequence position in the slideshow
- Active status (whether to show this item)
- Creation and last modification timestamps

**Capabilities**:
- Items can be reordered within a slideshow (drag-and-drop or up/down controls)
- Each item can have its own duration that overrides the slideshow default
- Items can be temporarily deactivated without removal
- Images and videos can be uploaded as files or referenced by URL
- Uploaded files are stored and served by the application

**Display Behavior**:
- **Images**: Scaled to fit display while maintaining aspect ratio, centered with letterboxing/pillarboxing as needed
- **Videos**: Autoplay with audio muted, scaled to fit display, advance after specified duration (not video length)
- **Web Pages**: Displayed in iframe with security restrictions, some sites may block embedding
- **Text**: Centered display with responsive typography

### 2.4 Displays

**Purpose**: Represent physical kiosk devices or screens showing slideshows

**Properties**:
- Name (unique identifier, derived from display URL)
- Description (optional information about the display)
- Location (optional physical location information)
- Screen resolution (width and height in pixels)
- Rotation angle (0°, 90°, 180°, or 270° for portrait/landscape orientation)
- Active status (whether the display is operational)
- Online status (whether the display is currently connected)
- Last seen timestamp (when the display last contacted the server)
- Heartbeat interval (how often the display should check in)
- Assigned slideshow (which slideshow to display)
- Creation and last modification timestamps
- Owner (optional - displays can auto-register without owner)

**Capabilities**:
- Displays automatically register when first accessed via unique URL
- Screen resolution is detected automatically via JavaScript on first connection
- Displays send periodic "heartbeat" signals to indicate they're online
- A display is considered "offline" if it hasn't sent a heartbeat in 3x the heartbeat interval
- Displays can be archived (hidden but not deleted) and later restored
- Displays show configuration prompt if no slideshow is assigned
- Displays can be assigned to any slideshow by any authenticated user

### 2.5 Assignment History

**Purpose**: Track changes to display-slideshow assignments for audit and troubleshooting

**Properties**:
- Display (which display was affected)
- Previous slideshow (what was shown before, if any)
- New slideshow (what is now shown, if any)
- Action type (assign, unassign, or change)
- Reason for change (optional explanation)
- User who made the change
- Date and time of change

**Capabilities**:
- Automatically created when display assignments change
- Provides complete audit trail of all assignment changes
- Can be viewed per-display or system-wide
- Helps troubleshoot display configuration issues

### 2.6 Display Configuration Templates

**Purpose**: Save and reuse display configuration settings

**Properties**:
- Template name (unique per user)
- Configuration settings (location, rotation, description, etc.)
- Owner (user who created the template)
- Creation timestamp

**Capabilities**:
- Save common display configurations as reusable templates
- Apply template to one or many displays at once
- Speeds up setup of multiple similar displays
- Templates don't include slideshow assignments (only device settings)

## 3. User Interfaces

### 3.1 Authentication Interface

**Login Screen**:
- Username input field
- Password input field
- Login button
- No registration link (accounts are created automatically on first login)

**Behavior**:
- Any username and password combination is accepted
- If username doesn't exist, a new user account is created
- All new users automatically receive admin privileges
- After successful login, user is redirected to dashboard
- Login sessions persist across browser sessions
- Logout option available from navigation

### 3.2 Admin Management Interface (Primary Interface)

A modern, responsive web application accessible at `/admin` with the following pages:

#### 3.2.1 Dashboard

**Purpose**: Overview of system status and quick actions

**Information Displayed**:
- Total number of slideshows
- Number of active slideshows
- Total number of displays
- Number of online displays
- Number of offline displays
- Recent activity summary

**Quick Actions**:
- Create new slideshow
- View all slideshows
- View all displays
- View assignment history

**Real-time Updates**:
- Display online/offline status updates automatically
- System statistics refresh without page reload

#### 3.2.2 Slideshow Management

**Slideshow List View**:
- Table or card layout showing all slideshows
- For each slideshow shows:
  - Name and description
  - Number of items
  - Active/inactive status
  - Default slideshow indicator
  - Last modified date
  - Action buttons (view, edit, delete, set as default)
- Search and filter capabilities
- Sorting options (by name, date, status)
- Create new slideshow button

**Slideshow Create/Edit Form**:
- Slideshow name (required, must be unique)
- Description (optional)
- Default item duration (seconds, default: 30)
- Transition type selection (optional)
- Active status checkbox
- Save and Cancel buttons

**Slideshow Detail View**:
- Displays slideshow metadata
- Shows list of all items in order
- For each item shows:
  - Order number
  - Title or content preview
  - Content type indicator (icon or label)
  - Duration
  - Active status
- Add item button
- Reorder controls (drag-and-drop preferred)
- Edit and delete buttons for each item
- Preview slideshow button

**Slideshow Item Form**:
- Content type selector (image, video, URL, text)
- Content source (changes based on type):
  - **Image**: File upload or URL input
  - **Video**: File upload or URL input
  - **URL**: Web address input with validation
  - **Text**: Multi-line text area with formatting options
- Title (optional)
- Duration override (optional, uses slideshow default if not specified)
- Active status checkbox
- Save and Cancel buttons
- File upload shows progress indicator for large files

**Slideshow Actions**:
- **Preview**: Opens slideshow in new window/tab in display mode
- **Set as Default**: Makes this slideshow the default for new displays
- **Duplicate**: Creates copy of slideshow with all items
- **Delete**: Soft delete with confirmation (only if not assigned to displays)

#### 3.2.3 Display Management

**Display List View**:
- Table or card layout showing all displays
- For each display shows:
  - Name and location
  - Online/offline status (color-coded indicator)
  - Screen resolution
  - Assigned slideshow name
  - Last seen timestamp
  - Action buttons (view details, edit, archive, assign slideshow)
- Search and filter capabilities (by status, location, assignment)
- Sorting options (by name, status, last seen)
- Bulk selection for multi-display operations
- System monitoring button

**Display Detail View**:
- Display information:
  - Name, description, location
  - Screen resolution and rotation
  - Online status and last seen time
  - Heartbeat interval
  - Creation and update timestamps
- Current slideshow assignment:
  - Show assigned slideshow name and info
  - Assign/change slideshow dropdown or drag-drop area
  - Unassign button
- Assignment history:
  - Table of all assignment changes for this display
  - Shows date, user, old and new slideshows, reason
- Configuration:
  - Edit display settings button
  - Archive display button
  - Delete display button (with confirmation)

**Display Edit Form**:
- Name (unique, required)
- Description (optional)
- Location (optional)
- Rotation angle (0, 90, 180, 270 degrees)
- Active status checkbox
- Save and Cancel buttons

**Slideshow Assignment**:
- Available via display detail page or bulk operations
- Shows list of available slideshows
- Drag-and-drop interface (drag slideshow to display)
- Or dropdown selection with assign button
- Optional reason field for audit trail
- Confirmation before applying
- Assignment takes effect immediately on display

**Bulk Operations**:
- Select multiple displays with checkboxes
- Bulk assign slideshow to selected displays
- Bulk apply configuration template
- Status confirmation showing success/failure for each

**Display Archive Management**:
- View list of archived displays
- Restore archived displays
- Archived displays don't appear in normal list
- Archived displays cannot be assigned slideshows

**Configuration Templates**:
- View list of saved templates
- Create new template from current display settings
- Apply template to one or more displays
- Edit and delete templates
- Templates saved per-user

#### 3.2.4 Assignment History

**History List View**:
- Table showing all assignment changes system-wide
- Columns:
  - Date and time
  - Display name
  - Previous slideshow
  - New slideshow
  - Action type (assign/unassign/change)
  - User who made change
  - Reason (if provided)
- Filtering options:
  - By display
  - By date range
  - By user
  - By action type
- Sorting by any column
- Pagination for large history lists
- Export functionality (optional)

#### 3.2.5 System Monitoring (Optional/Advanced)

**Purpose**: View real-time system status and diagnostics

**Information Displayed**:
- Number of active connections
- Server-Sent Events (SSE) connection status
- Connection statistics per display
- System health metrics
- Recent events log
- Connection debugging information

### 3.3 Display Kiosk Interface

**Purpose**: Full-screen interface for displaying slideshows on kiosk devices

**Access Method**: Navigate to `/display/<display-name>` where `<display-name>` is a unique identifier

**Auto-Registration Behavior**:
- When a new display name is accessed, the display is automatically created in the system
- Screen resolution is detected automatically via JavaScript
- If a default slideshow exists, it is automatically assigned
- If no default slideshow exists, configuration prompt is shown

**Slideshow Display Mode**:
When a slideshow is assigned, the display shows:
- Full-screen slideshow interface (no navigation, minimal chrome)
- Current slideshow item filling the screen
- Progress bar or indicator showing position in slideshow
- Automatic progression through items based on duration
- Infinite loop (slideshow repeats automatically)
- Keyboard shortcut to exit (Escape key)

**Slideshow Behavior**:
- Items display for their specified duration
- Transitions occur between items (fade, slide, etc.)
- Videos autoplay with audio muted
- Videos advance after duration expires (not video natural length)
- If video fails to load, skip to next item
- If image fails to load, show error briefly then skip
- If web page fails to load, show error briefly then skip

**Configuration Prompt Mode**:
When no slideshow is assigned, display shows:
- Display name and unique identifier
- Message indicating no slideshow is assigned
- Server URL for administrators to access management interface
- List of available slideshows that can be assigned
- Instructions for assigning a slideshow
- This page refreshes automatically when slideshow is assigned

**Empty Slideshow Mode**:
When assigned slideshow has no active items:
- Display message indicating slideshow is empty
- Instructions for administrators
- Server URL for management interface

**Real-time Updates**:
- Display automatically detects when assigned slideshow changes
- Display automatically reloads when slideshow content is updated
- Changes take effect at the end of current slideshow cycle (not mid-item)
- Display sends periodic heartbeat signals to server
- Display reconnects automatically if connection is lost

**Heartbeat Behavior**:
- Display sends heartbeat signal every 30-60 seconds (configurable)
- Heartbeat includes current timestamp and browser information
- Heartbeat updates "last seen" timestamp on server
- Display uses Server-Sent Events (SSE) for real-time updates or falls back to polling

### 3.4 Legacy Web Interface (Optional/Deprecated)

A simpler Flask-rendered interface available at the root URL (`/`) for backwards compatibility:
- Basic slideshow list and management
- Simple display assignment interface
- Less feature-rich than admin interface
- May be removed in future versions

## 4. Functional Workflows

### 4.1 Initial System Setup

1. User installs and starts the application
2. User navigates to application URL in web browser
3. System redirects to login page
4. User enters any username and password
5. System creates new user account with admin privileges
6. User is logged in and redirected to dashboard
7. Dashboard shows empty system (no slideshows or displays)

### 4.2 Creating First Slideshow

1. From dashboard or slideshow list, click "Create New Slideshow"
2. Enter slideshow name and optional description
3. Set default item duration (or use system default of 30 seconds)
4. Click "Save" or "Create"
5. System creates slideshow and redirects to slideshow detail page
6. User sees empty slideshow with "Add Item" button

### 4.3 Adding Content to Slideshow

**Adding Image**:
1. Click "Add Item" button
2. Select "Image" as content type
3. Either:
   - Upload image file from computer (shows progress bar), OR
   - Enter URL of external image
4. Optionally enter title
5. Optionally set duration (overrides slideshow default)
6. Click "Save"
7. Item appears in slideshow item list

**Adding Video**:
1. Click "Add Item" button
2. Select "Video" as content type
3. Either:
   - Upload video file from computer (shows progress bar), OR
   - Enter URL of external video
4. Optionally enter title
5. Optionally set duration (determines how long to show, not video length)
6. Click "Save"
7. Item appears in slideshow item list

**Adding Web Page**:
1. Click "Add Item" button
2. Select "URL" or "Web Page" as content type
3. Enter web page URL
4. Optionally enter title
5. Optionally set duration
6. Click "Save"
7. Item appears in slideshow item list
8. **Note**: Some websites may not display in iframe due to security policies

**Adding Text**:
1. Click "Add Item" button
2. Select "Text" as content type
3. Enter text content in text area
4. Optionally enter title
5. Optionally set duration
6. Click "Save"
7. Item appears in slideshow item list

### 4.4 Reordering Slideshow Items

**Drag-and-Drop Method (Preferred)**:
1. On slideshow detail page, see list of items in current order
2. Click and hold on item to drag
3. Drag item to new position in list
4. Release mouse to drop in new position
5. System automatically saves new order
6. Order numbers update to reflect new sequence

**Alternative Method (Buttons)**:
1. Each item has up/down arrow buttons
2. Click up arrow to move item earlier in sequence
3. Click down arrow to move item later in sequence
4. System automatically saves new order

### 4.5 Setting Default Slideshow

1. From slideshow list or detail view
2. Click "Set as Default" button or action
3. System confirms action
4. System marks this slideshow as default
5. System removes default flag from any previous default
6. New displays will now be automatically assigned this slideshow

### 4.6 Setting Up New Display Device

**Physical Setup**:
1. Set up kiosk device with web browser
2. Configure browser to start in full-screen mode
3. Point browser to `/display/<unique-name>` where `<unique-name>` is a descriptive identifier (e.g., "lobby-display", "entrance-1")

**Automatic Registration**:
1. Display accesses unique URL for first time
2. System automatically creates display record
3. System detects and stores screen resolution via JavaScript
4. If default slideshow exists, system assigns it to display
5. Display begins showing assigned slideshow immediately

**Alternative: Configuration Prompt**:
1. If no default slideshow exists
2. Display shows configuration prompt
3. Configuration prompt displays:
   - Display unique name
   - Link to admin interface
   - Instructions for administrator
4. Administrator logs into admin interface
5. Administrator assigns slideshow to display
6. Display automatically detects assignment and begins showing slideshow

### 4.7 Assigning Slideshow to Display

**From Display Detail Page**:
1. Navigate to Displays section
2. Click on specific display to view details
3. In assignment section, see dropdown or drag-drop area
4. Select slideshow from dropdown OR drag slideshow card to display
5. Optionally enter reason for assignment
6. Click "Assign" or confirm action
7. System updates display assignment
8. System creates assignment history record
9. Display detects change within seconds and loads new slideshow

**From Display List (Bulk)**:
1. Navigate to Displays section showing list of displays
2. Select multiple displays using checkboxes
3. Click "Bulk Assign" button
4. Select slideshow from dropdown
5. Optionally enter reason
6. Confirm action
7. System assigns slideshow to all selected displays
8. Each display detects change and updates

**Using Drag-and-Drop**:
1. View split screen or separate sections showing slideshows and displays
2. Drag slideshow card or item
3. Drop onto display card or drop zone
4. System prompts for optional reason
5. Confirm action
6. Assignment is made immediately

### 4.8 Updating Slideshow Content

**Adding/Editing/Removing Items**:
1. Navigate to slideshow detail page
2. Make changes (add items, edit existing items, delete items, reorder)
3. Each change is saved immediately or on confirmation
4. System broadcasts update notification

**Real-time Effect on Displays**:
1. Displays showing this slideshow receive update notification via SSE
2. Display finishes showing current item
3. Display completes current slideshow cycle (reaches end of item list)
4. Display loads updated slideshow content
5. Display begins showing updated slideshow
6. Total time to update: typically less than duration of one complete slideshow cycle

### 4.9 Monitoring Display Status

**From Display List**:
1. Navigate to Displays section
2. View list of all displays with status indicators
3. Green/online indicator means display is connected and sending heartbeats
4. Red/offline indicator means display hasn't been seen recently (3x heartbeat interval)
5. Last seen timestamp shows when display last contacted server
6. Click on display to view detailed status

**From Display Detail**:
1. View online/offline status
2. View last seen timestamp with elapsed time
3. View assigned slideshow
4. View screen resolution and device information
5. View assignment history

**Real-time Updates**:
1. Display list updates automatically as displays come online/offline
2. No page refresh needed
3. Visual feedback when status changes

### 4.10 Archiving and Restoring Displays

**Archiving Display**:
1. Navigate to display detail page
2. Click "Archive" button
3. System confirms action
4. System marks display as archived
5. System clears slideshow assignment
6. System marks display as inactive
7. Display disappears from normal display list
8. Display stops receiving updates

**Viewing Archived Displays**:
1. Navigate to Displays section
2. Click "Show Archived" button or filter
3. View list of archived displays
4. Each shows archive date and who archived it

**Restoring Display**:
1. View archived displays list
2. Click "Restore" button on archived display
3. System confirms action
4. System marks display as active
5. System removes archived flag
6. Display reappears in normal display list
7. Display can be assigned slideshow again

### 4.11 Using Configuration Templates

**Creating Template**:
1. Configure a display with desired settings (location, rotation, description, etc.)
2. From display detail page, click "Save as Template"
3. Enter template name
4. System saves configuration as reusable template

**Applying Template to Single Display**:
1. Navigate to display detail page
2. Click "Apply Template" button
3. Select template from dropdown
4. Preview changes
5. Confirm application
6. System updates display configuration

**Applying Template to Multiple Displays (Bulk)**:
1. From display list, select multiple displays
2. Click "Apply Template" button
3. Select template from dropdown
4. Preview changes
5. Confirm application
6. System applies configuration to all selected displays
7. System shows success/failure for each display

### 4.12 Viewing Assignment History

**System-Wide History**:
1. Navigate to Assignment History section
2. View table of all assignment changes
3. See display name, previous slideshow, new slideshow, user, date/time, reason
4. Filter by date range, display, user, or action type
5. Sort by any column
6. Pagination for long lists

**Per-Display History**:
1. Navigate to display detail page
2. View assignment history section
3. See all assignment changes for this specific display
4. Same information as system-wide history, filtered to this display

**Using History for Troubleshooting**:
1. Display showing wrong content → check assignment history
2. See when assignment changed and who changed it
3. See reason for change if provided
4. Can trace back through all changes to understand current state

## 5. Content and Media Handling

### 5.1 File Upload Requirements

**Image Files**:
- Supported formats: JPEG, PNG, GIF, WebP
- Maximum file size: 50 MB per image
- Files stored on server in organized directory structure
- Files served with appropriate MIME types and caching headers
- Validation of file type based on content, not just extension

**Video Files**:
- Supported formats: MP4, WebM, AVI
- Maximum file size: 500 MB per video
- Files stored on server in organized directory structure
- Modern web-compatible codecs required (H.264, VP8+)
- No server-side transcoding or conversion

**Upload Process**:
- Progress indicator during upload
- Error messages for invalid files or size exceeded
- Upload can be cancelled during transfer
- Files associated with specific slideshow
- Files cleaned up when slideshow or item is deleted

### 5.2 File Storage Organization

Files are stored in an organized structure:
- Separate directories for images and videos
- Sub-directories by user and slideshow (for organization)
- Secure file naming to prevent conflicts and security issues
- Directory traversal protection
- Orphaned file cleanup when content is deleted

### 5.3 Content Source Options

For each content type, users can choose:

**Images**:
- Upload file from local computer
- Provide URL to external image
- Both options produce same display result

**Videos**:
- Upload file from local computer
- Provide URL to external video
- Both options produce same display result
- External videos must be web-accessible with CORS headers

**Web Pages**:
- Only URL option available
- Must be public web page
- Some sites block iframe embedding (X-Frame-Options header)
- Cannot guarantee all sites will work

**Text**:
- Only text input option
- Plain text or simple formatting
- No file upload needed

### 5.4 Content Scaling and Display

**Images**:
- Scaled to fit display resolution
- Aspect ratio maintained (no stretching)
- Letterboxing (black bars top/bottom) or pillarboxing (black bars left/right) as needed
- Centered on screen
- CSS `object-fit: contain` behavior

**Videos**:
- Same scaling behavior as images
- Autoplay when item is shown
- Audio muted to comply with browser autoplay policies
- Video does not loop within slideshow
- Display duration controls how long to show, not video's natural length
- If duration < video length: video stops and advances to next item
- If duration > video length: video ends, blank screen until duration expires
- If video fails to load: error shown briefly, then skip to next item

**Web Pages**:
- Displayed in iframe element
- Iframe sized to full display resolution
- Some sites may refuse to load in iframe (X-Frame-Options: DENY/SAMEORIGIN)
- Limited interaction capability (links generally don't work in kiosk context)
- May have scrollbars if page doesn't fit
- Sandboxed iframe for security

**Text**:
- Centered on screen
- Responsive typography sized for display
- Dark text on light background
- Wraps to fit display width
- Vertical centering for all content heights

### 5.5 Storage Management

**Storage Statistics**:
- View total storage used by all files
- Breakdown by file type (images vs videos)
- Number of files uploaded
- Files per user and per slideshow

**File Cleanup**:
- Files automatically deleted when slideshow is deleted
- Files automatically deleted when slideshow item is deleted
- Orphaned files detected and removed
- Admin can view storage usage and clean up if needed

## 6. Real-Time Communication and Updates

### 6.1 Real-Time Update Mechanism

The system uses Server-Sent Events (SSE) for real-time updates:

**For Admin Interface**:
- Dashboard receives real-time display status updates
- Display list updates when displays come online/offline
- Notifications when slideshows are modified
- System-wide event notifications

**For Display Devices**:
- Displays receive notifications when assigned slideshow changes
- Displays receive notifications when slideshow content is updated
- Displays receive configuration change notifications

**Fallback Mechanism**:
- If SSE is not supported or fails, system falls back to polling
- Polling checks for updates every 30-60 seconds
- Ensures updates work even with older browsers or network issues

### 6.2 Display Heartbeat System

**Purpose**: Track which displays are online and responsive

**Behavior**:
- Display sends heartbeat signal every 30-60 seconds (configurable per display)
- Heartbeat includes timestamp and browser information
- Server updates "last seen" timestamp
- Display considered "online" if heartbeat received within 3x heartbeat interval
- Display considered "offline" if no heartbeat for 3x heartbeat interval
- Admin interface shows online/offline status in real-time

**Connection Loss Handling**:
- Display attempts to reconnect if connection is lost
- Automatic retry with exponential backoff
- Display continues showing current slideshow while attempting reconnection
- When reconnection succeeds, display checks for any pending updates

### 6.3 Update Propagation Timing

**Immediate Updates**:
- Display online/offline status (within heartbeat interval)
- Assignment history records
- Admin interface statistics

**End-of-Cycle Updates**:
- Slideshow content changes take effect at end of current cycle
- Display assignment changes take effect at end of current cycle
- "Cycle" means completing display of all items and returning to first item

**Rationale for End-of-Cycle**:
- Prevents jarring mid-item interruption
- Ensures viewers see complete content items
- Provides predictable update timing
- Typical delay: duration of one complete slideshow cycle (often 1-5 minutes)

## 7. System Behavior and Business Rules

### 7.1 Authentication and Access

**Login**:
- Any username and password combination is accepted
- If username doesn't exist, new user account is created automatically
- All new users receive admin privileges by default
- No email verification or registration workflow
- Sessions persist across browser sessions

**Access Control**:
- All authenticated users have equal privileges (global access model)
- All users can create, modify, and delete all content
- All users can manage all displays
- All users can assign any slideshow to any display
- User ownership is tracked but not enforced

**Logout**:
- Logout button available in navigation
- Clears session and redirects to login page
- Display devices don't have logout (intended to stay logged in)

### 7.2 Slideshow Rules

**Naming**:
- Slideshow names must be unique system-wide (not just per-user)
- Names must be at least 2 characters
- Names can contain letters, numbers, spaces, and common punctuation

**Default Slideshow**:
- Only one slideshow can be default at any time
- Setting a slideshow as default removes default from previous default
- Default slideshow is automatically assigned to new displays
- Deleting default slideshow automatically selects oldest remaining slideshow as new default
- If no slideshows exist, new displays show configuration prompt

**Active/Inactive Status**:
- Inactive slideshows are hidden from assignment lists
- Displays already showing inactive slideshow continue showing it
- Setting slideshow to inactive doesn't un-assign it from displays
- Inactive is a "soft delete" - slideshow can be reactivated

**Deletion**:
- Slideshows can only be deleted if not assigned to any displays
- User must first un-assign from all displays before deletion
- Deleting slideshow deletes all its items
- Deleting slideshow deletes all associated uploaded files
- Deletion is permanent (not a soft delete)
- Assignment history records are preserved

### 7.3 Slideshow Item Rules

**Ordering**:
- Items are displayed in order from lowest to highest order_index
- Order indices can be any integers (typically 0, 1, 2, etc.)
- Reordering changes order_index values
- Gaps in order indices are acceptable (0, 10, 20)

**Duration**:
- Each item can have its own duration or use slideshow default
- Duration must be at least 1 second
- Duration maximum is 300 seconds (5 minutes) but can be configured
- Duration determines how long item is shown, regardless of natural content length
- For videos: duration may be shorter or longer than video length

**Active/Inactive Status**:
- Inactive items are skipped during playback
- Setting item inactive doesn't remove it from slideshow
- Inactive items can be reactivated without re-creating

**Content Validation**:
- URLs must be valid HTTP/HTTPS URLs
- Uploaded files must match declared content type
- File size limits enforced during upload
- Malformed data is rejected with error message

### 7.4 Display Rules

**Naming**:
- Display names must be unique system-wide
- Names derived from URL path when display first connects
- Names can be changed by admin after creation
- Name changes don't affect display's access URL (uses ID internally)

**Auto-Registration**:
- Accessing `/display/<new-name>` creates display record automatically
- Display is created with owner_id = null (no owner)
- Screen resolution detected via JavaScript and saved
- If default slideshow exists, automatically assigned
- If no default slideshow, shows configuration prompt

**Resolution Detection**:
- Resolution detected once on first connection via JavaScript `window.screen` API
- Resolution assumed to remain constant after initial detection
- If physical display resolution changes, admin must:
  1. Delete display record from admin interface
  2. Restart display device to trigger re-detection
  3. System will re-detect new resolution

**Online/Offline Status**:
- Display is "online" if heartbeat received within 3x heartbeat interval
- Display is "offline" if no heartbeat for 3x heartbeat interval
- Default heartbeat interval is 60 seconds
- Status updates automatically in admin interface
- Offline displays continue in database (not deleted)

**Rotation**:
- Display can be rotated 0°, 90°, 180°, or 270° clockwise
- Rotation is for displays mounted in portrait mode or unusual orientations
- Rotation setting is advisory (display client must implement CSS transform)
- Default is 0° (normal landscape)

**Archiving**:
- Archived displays are hidden from normal lists
- Archived displays cannot be assigned slideshows
- Archived displays are marked inactive
- Archiving clears current slideshow assignment
- Archiving tracks who archived and when
- Archived displays can be restored to active state

**Deletion**:
- Deleting display is permanent
- Display can be deleted even if assigned to slideshow
- Deletion removes display record completely
- If display device accesses URL again, new display record is created (re-registration)

### 7.5 Assignment History Rules

**Automatic Creation**:
- History record created automatically whenever display assignment changes
- No manual creation by user
- Cannot be edited or deleted
- Permanent audit trail

**Information Captured**:
- Which display was affected
- Previous slideshow (null if first assignment)
- New slideshow (null if un-assignment)
- User who made the change
- Date and time of change
- Optional reason provided by user

**Action Types**:
- **Assign**: Display had no slideshow, now has one
- **Unassign**: Display had slideshow, now has none
- **Change**: Display slideshow changed from one to another

### 7.6 Configuration Template Rules

**Creation**:
- Templates saved per-user (each user has their own templates)
- Template names must be unique per user
- Templates save display settings but NOT slideshow assignment

**Settings Included**:
- Location
- Description
- Rotation
- Heartbeat interval
- Custom configuration values

**Settings NOT Included**:
- Display name (unique per display)
- Assigned slideshow (managed separately)
- Resolution (detected, not configured)
- Online status (derived from heartbeats)

**Application**:
- Can apply to one display or multiple displays
- Application overwrites existing settings on target displays
- Preview shows what will change before applying
- Bulk application shows success/failure per display

## 8. Error Handling and Edge Cases

### 8.1 Content Loading Failures

**Image Loading Failure**:
- Display attempts to load image
- If fails (404, network error, invalid format):
  - Show error message briefly (2-3 seconds)
  - Automatically skip to next item
  - Log error for administrator

**Video Loading Failure**:
- Display attempts to load video
- If fails (404, network error, unsupported format):
  - Show error message briefly (2-3 seconds)
  - Automatically skip to next item
  - Log error for administrator

**Web Page Loading Failure**:
- Display attempts to load web page in iframe
- If fails (404, network error, X-Frame-Options block):
  - Show error message with explanation
  - Display for shorter duration (5-10 seconds)
  - Automatically skip to next item
  - Cannot detect all failure modes (some blocked sites show blank)

**Text Rendering Failure**:
- Text content always renders (no external dependencies)
- If text is empty or null, show for 1 second then skip

### 8.2 Empty or Invalid Slideshows

**Slideshow with No Items**:
- If slideshow has no items at all:
  - Display shows "empty slideshow" message
  - Message includes instructions for administrator
  - Message persists until items are added
  - Display checks periodically for added items

**Slideshow with Only Inactive Items**:
- Treated same as slideshow with no items
- All items skipped during playback
- Results in empty slideshow message

**Slideshow with All Failed Items**:
- If all items fail to load during playback:
  - Continue attempting to show items (retry)
  - If all items consistently fail:
    - Show error message indicating problem
    - Display instructions for administrator
    - Continue retry loop in case items become available

### 8.3 Display Connection Issues

**Network Disconnection**:
- Display loses network connection
- Display continues showing current slideshow item
- Display attempts to reconnect automatically
- When network returns:
  - Display reconnects to server
  - Display checks for updates
  - Display continues or updates as needed

**Server Unavailable**:
- Display cannot reach server
- Display continues showing last loaded slideshow
- Display retries connection periodically
- When server returns, display updates if needed

**Browser Crash or Reload**:
- Display browser crashes or is reloaded
- Browser returns to display URL
- Display re-registers (updates heartbeat)
- Display reloads currently assigned slideshow
- Display resumes from beginning of slideshow

### 8.4 Admin Interface Error Scenarios

**Duplicate Names**:
- User attempts to create slideshow or display with existing name
- System shows error message
- User must choose different name

**Deleting Assigned Slideshow**:
- User attempts to delete slideshow assigned to displays
- System prevents deletion
- System shows error message listing which displays are using it
- User must un-assign from all displays first

**File Upload Failures**:
- File too large: Error message with size limit
- Invalid file type: Error message with allowed types
- Network interruption during upload: Upload fails, user must retry
- Server storage full: Error message, user cannot upload until space freed

**Invalid Content URLs**:
- User enters malformed URL
- Client-side validation catches common errors
- Server-side validation provides detailed error message
- URL must be valid HTTP/HTTPS format

**Permission Errors** (Future Enhancement):
- Current version: all users have all permissions
- Future: some users may have limited permissions
- Error message indicates insufficient permissions
- User must contact administrator

### 8.5 Race Conditions and Conflicts

**Simultaneous Assignment Changes**:
- Two users change display assignment simultaneously
- Last change wins (standard database behavior)
- Both changes recorded in assignment history
- No data loss or corruption

**Simultaneous Slideshow Edits**:
- Two users edit same slideshow simultaneously
- Last save wins for each field (standard behavior)
- No version conflict resolution
- No locking mechanism
- Users should coordinate to avoid confusion

**Display Re-Registration**:
- Display is deleted from admin interface
- Display device remains running and accesses URL
- System creates new display record (re-registration)
- New record has different ID from deleted record
- Assignment history from old record preserved separately

## 9. Performance and Scalability Expectations

### 9.1 Supported Scale

**Number of Users**:
- System designed for small to medium organizations
- Expected: 5-50 concurrent admin users
- Can support more with appropriate server resources
- No hard limit, performance depends on server

**Number of Displays**:
- Expected: 10-100 displays
- Can support more with appropriate server resources
- Each display maintains heartbeat connection
- Scales with server's connection limit

**Number of Slideshows**:
- Expected: 10-100 slideshows
- Can support thousands with appropriate database
- No significant performance impact from many slideshows
- Limited by database and storage capacity

**File Storage**:
- Expected: 1-10 GB of media files
- Can support much more with appropriate storage
- Limited by server disk space
- No application-imposed limit

### 9.2 Performance Expectations

**Page Load Times**:
- Admin interface: < 2 seconds for initial load
- Admin interface pages: < 1 second for navigation
- Display interface: < 5 seconds for initial load
- Slideshow updates on display: < 10 seconds to take effect

**API Response Times**:
- CRUD operations: < 200ms typical
- File uploads: Limited by network bandwidth
- Large file uploads: Progress indicator, no timeout

**Real-Time Updates**:
- Display status changes: < 5 seconds to appear in admin interface
- Slideshow content changes: < 1 minute to take effect on displays
- Assignment changes: < 10 seconds to take effect on displays

**Heartbeat Frequency**:
- Default: Every 60 seconds
- Configurable per display: 30-300 seconds
- More frequent heartbeats = faster online/offline detection
- Less frequent heartbeats = lower server load

### 9.3 Resource Requirements

**Client (Admin Interface)**:
- Modern web browser (Chrome, Firefox, Safari, Edge)
- JavaScript must be enabled
- Minimum 1024x768 screen resolution
- Recommended: 1920x1080 or higher for comfortable use

**Client (Display Device)**:
- Web browser with HTML5 video support
- JavaScript must be enabled
- Any screen resolution (detected automatically)
- Recommended: Stable network connection
- Recommended: Browser in kiosk/full-screen mode

**Server**:
- Requirements vary based on scale
- Small deployment (10 displays): Single core, 512MB RAM, 10GB storage
- Medium deployment (50 displays): 2-4 cores, 2GB RAM, 50GB storage
- Large deployment (100+ displays): 4+ cores, 4GB+ RAM, 100GB+ storage
- Network: Stable internet connection, adequate bandwidth for file uploads

## 10. Security and Access Control

### 10.1 Authentication Security

**Password Security**:
- Passwords are hashed using industry-standard methods
- Passwords never stored in plain text
- Password complexity not enforced (user responsibility)
- No password reset mechanism (any password accepted on re-login)

**Session Security**:
- Sessions use secure cookies with appropriate flags
- Sessions persist across browser sessions
- No session timeout (user must explicitly logout)
- HTTPS enforcement configurable for production

**No Registration Required**:
- Reduces security risk from open registration
- Reduces spam and abuse potential
- Trade-off: Weak authentication for ease of use
- Suitable for internal networks or VPN access

### 10.2 File Upload Security

**File Type Validation**:
- File type verified based on content, not just extension
- Prevents malicious file uploads masquerading as images/videos
- Invalid files rejected with error message

**File Size Limits**:
- Images: 50 MB maximum
- Videos: 500 MB maximum
- Prevents abuse and ensures reasonable storage usage

**Filename Sanitization**:
- Uploaded filenames sanitized to prevent directory traversal
- Special characters removed or escaped
- Files stored with secure generated names

**Storage Location**:
- Files stored in organized directory structure
- Files not executable (served with appropriate MIME types)
- Directory listings disabled

**Virus Scanning** (Future Enhancement):
- Current version: No virus scanning
- Future: Integration point for virus scanning tools
- Recommended for production deployments

### 10.3 Content Security

**Web Page Embedding**:
- External web pages displayed in sandboxed iframe
- Sandbox attributes restrict capabilities (scripts, forms, etc.)
- Provides basic protection from malicious embedded content
- Some sites may not display due to X-Frame-Options headers

**Content Security Policy**:
- Admin interface has strict CSP headers
- Display interface has relaxed CSP to allow embedded content
- Protects against XSS and other injection attacks

**Input Validation**:
- All user input validated on both client and server
- SQL injection prevented by parameterized queries
- XSS prevented by proper output encoding
- URL validation ensures proper format

### 10.4 API Security

**Authentication Required**:
- All API endpoints require authentication
- Unauthenticated requests return 401 Unauthorized
- Display endpoints (/display/*) are exception (no auth required)

**CSRF Protection** (Future Enhancement):
- Current version: Basic protection via SameSite cookies
- Future: CSRF tokens for all state-changing operations

**Rate Limiting** (Future Enhancement):
- Current version: No rate limiting
- Future: Rate limits on API endpoints
- Prevents abuse and DoS attacks

### 10.5 Display Security

**No Authentication Required**:
- Display endpoints publicly accessible (no login)
- Necessary for kiosk devices to function
- Trade-off: Anyone can view display URLs
- Mitigated: Display names are unique identifiers, not easily guessable

**Heartbeat Data**:
- Heartbeat includes minimal information
- No sensitive data transmitted
- Display name in URL is primary identifier

**Configuration Changes**:
- Display configuration requires admin authentication
- Display cannot modify its own configuration
- All changes tracked in audit log

## 11. User Experience Principles

### 11.1 Admin Interface Design

**Modern and Intuitive**:
- Clean, uncluttered interface
- Consistent visual design
- Responsive layout for various screen sizes
- Bootstrap-based styling for familiarity

**Real-Time Feedback**:
- Status indicators update without page refresh
- Loading indicators during operations
- Success/error messages after actions
- Progress bars for file uploads

**Efficient Workflows**:
- Minimal clicks to accomplish tasks
- Bulk operations for managing multiple items
- Drag-and-drop for intuitive interactions
- Keyboard shortcuts where appropriate

**Clear Navigation**:
- Persistent navigation bar or sidebar
- Breadcrumb navigation for deep pages
- Clear section labels
- Consistent page layouts

**Helpful Error Messages**:
- Specific error descriptions (not generic "error occurred")
- Actionable guidance (what to do to fix)
- Examples of correct input format
- No technical jargon for end users

### 11.2 Display Interface Design

**Minimal Chrome**:
- Full-screen display (no browser UI visible)
- No navigation elements
- No distracting UI elements
- Focus entirely on content

**Smooth Transitions**:
- Pleasant transitions between items
- Fade effects preferred over jarring cuts
- Configurable transition types
- Performance optimized for smooth animation

**Content-First**:
- Content fills screen optimally
- Appropriate use of letterboxing/pillarboxing
- No distortion or stretching
- High-quality rendering

**Reliability**:
- Graceful error handling
- Automatic recovery from errors
- Continuous operation without intervention
- Automatic reconnection after network issues

### 11.3 Accessibility Considerations

**Web Content Accessibility**:
- Proper semantic HTML structure
- ARIA labels where appropriate
- Keyboard navigation support
- Sufficient color contrast
- Readable font sizes

**Display Content Accessibility**:
- Text content uses readable fonts and sizes
- Sufficient contrast for text on background
- Content duration long enough to read
- No rapidly flashing content (seizure risk)

**Alternative Content** (Future Enhancement):
- Captions for videos
- Alt text for images
- Screen reader support
- High contrast mode

## 12. Future Enhancement Opportunities

While the current specification defines a complete, functional system, these areas represent potential future enhancements:

### 12.1 Content Features
- Scheduled slideshows (show different content at different times/days)
- Slideshow templates and presets
- Content libraries and asset management
- Support for live data feeds (weather, news, social media)
- HTML widgets and interactive content
- Multi-zone displays (multiple regions on one screen)
- Playlist scheduling and day-parting

### 12.2 Display Features
- Display groups (manage multiple displays as one)
- Display health monitoring and diagnostics
- Remote display control (reboot, reload, power)
- Display orientation auto-detection
- Touch interactivity support
- Display snapshots/screenshots
- Emergency override mode

### 12.3 Management Features
- Role-based access control (RBAC)
- Multi-tenancy support
- Advanced reporting and analytics
- Content performance metrics (views, duration)
- Slideshow preview with annotations
- Content approval workflows
- Version history for content changes
- Advanced search and filtering

### 12.4 Integration Features
- API webhooks for events
- Third-party integrations (Google Drive, Dropbox, etc.)
- Single Sign-On (SSO) authentication
- LDAP/Active Directory integration
- Content management system (CMS) integration
- Calendar integration for scheduling
- Social media content import

### 12.5 Technical Enhancements
- CDN integration for media delivery
- Video transcoding and optimization
- Mobile app for management
- Offline mode for displays
- Content caching and preloading
- Multi-server deployment
- Database replication and high availability

## 13. Glossary

**Admin Interface**: The web-based management interface where users create and manage content

**Assignment**: The connection between a display and a slideshow, determining what content the display shows

**Archived Display**: A display that has been hidden from normal operation but not deleted

**Configuration Template**: A reusable set of display settings that can be applied to multiple displays

**Content Type**: The kind of content in a slideshow item (image, video, URL, or text)

**Default Slideshow**: The slideshow automatically assigned to newly registered displays

**Display**: A physical device (kiosk, digital sign) that shows slideshow content

**Display Device**: See "Display"

**Heartbeat**: Periodic signal sent by display to server indicating it's online and responsive

**Item**: A single piece of content within a slideshow (image, video, web page, or text)

**Kiosk**: A display device, typically in a public location, showing slideshow content

**Kiosk Interface**: See "Display Interface"

**SSE**: Server-Sent Events, a technology for real-time server-to-client updates

**Offline Display**: A display that hasn't sent a heartbeat signal recently

**Online Display**: A display that is actively sending heartbeat signals

**Order Index**: The numeric position of an item within a slideshow, determining play order

**Real-Time Updates**: Changes that take effect on displays without manual refresh

**Slideshow**: An ordered collection of content items displayed in sequence

**Slideshow Cycle**: One complete playthrough of all items in a slideshow

**Soft Delete**: Marking something as inactive rather than permanently deleting it

---

## Document Change History

**Version 1.0 - January 2026**
- Initial functional specification created from analysis of kiosk-show-replacement repository
- Comprehensive specification covering all implemented features as of Milestone 11
- Includes admin interface, display management, real-time updates, and all core functionality

---

*End of Functional Specification*
