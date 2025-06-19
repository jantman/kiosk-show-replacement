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

## Data Model & Business Rules

### Core Data Model
The application centers around four main entities with the following relationships:

* **Users**: Store authentication and audit information
  * `id` (primary key)
  * `username` (unique)
  * `created_at`, `last_login`
  * Initially, any username/password combination is accepted

* **Displays**: Represent connected kiosk devices
  * `id` (primary key)
  * `name` (unique, derived from URL)
  * `resolution_width`, `resolution_height` (detected on first connection)
  * `assigned_slideshow_id` (foreign key to Slideshows, nullable)
  * `created_by` (foreign key to Users)
  * `created_at`, `modified_at`, `modified_by`
  * `last_seen` (for heartbeat monitoring)

* **Slideshows**: Collections of slideshow items
  * `id` (primary key)
  * `name` (unique per user)
  * `default_item_duration` (seconds, default: 5)
  * `transition_effect` (nullable, for future implementation)
  * `is_default` (boolean, system-wide default slideshow)
  * `created_by` (foreign key to Users)
  * `created_at`, `modified_at`, `modified_by`

* **Slideshow Items**: Individual content items within slideshows
  * `id` (primary key)
  * `slideshow_id` (foreign key to Slideshows)
  * `order_index` (integer, for ordering within slideshow)
  * `content_type` (enum: 'image_url', 'image_file', 'video_url', 'video_file', 'web_page')
  * `content_source` (URL or file path)
  * `duration_override` (seconds, nullable - uses slideshow default if null)
  * `created_at`, `modified_at`, `modified_by`

### User Isolation and Multi-tenancy Rules
* **Shared System Model**: This is a single-tenant system where all users share the same data space
* **User Visibility**: All users can see and edit all slideshows and displays (initially - RBAC hooks provided for future enhancement)
* **Ownership Tracking**: While users can access all content, ownership is tracked via `created_by` fields for audit purposes
* **Display Sharing**: Displays are shared resources - any user can assign any slideshow to any display
* **Future Isolation**: The data model includes user foreign keys to enable future multi-tenant or RBAC implementations

### Default Slideshow Management
* **System Default**: Only one slideshow can be marked as `is_default = true` at a time
* **Auto-Assignment**: New displays are automatically assigned the default slideshow upon first connection
* **No Default Scenario**: If no default slideshow exists, new displays show a configuration prompt page with:
  * Display name
  * Server URL for admin access
  * Instructions for configuring the display
* **Default Changes**: When a different slideshow is set as default, existing displays keep their current assignments (only new displays get the new default)
* **Default Deletion**: If the default slideshow is deleted, the system automatically selects the oldest remaining slideshow as the new default (or shows config prompt if no slideshows exist)

### Display Resolution and Content Scaling
* **Resolution Detection**: Display resolution is detected via JavaScript on first connection and stored in the database
* **Static Resolution Assumption**: Once set, display resolution is assumed to remain constant (as per user requirements)
* **Content Scaling Strategy**:
  * **Images**: Scaled to "best fit" the display resolution while maintaining aspect ratio (CSS `object-fit: contain`)
  * **Videos**: Same scaling strategy as images, centered with letterboxing/pillarboxing as needed
  * **Web Pages**: Displayed at native resolution within iframe, with CSS scaling if the page exceeds display dimensions
* **Resolution Change Handling**: If a display's resolution changes, the user must delete the display from the admin interface and restart the display device to trigger re-detection
* **Responsive Design**: The admin interface (React SPA) is responsive and adapts to different screen sizes, but display content is optimized for the detected resolution

### Video Playback Requirements
* **Audio Policy**: All videos play muted by default to comply with browser autoplay policies and kiosk environment expectations
* **Autoplay**: Videos must autoplay when their turn comes in the slideshow rotation
* **Loop Behavior**: Videos play once and then the slideshow advances to the next item (no video looping within the slideshow timing)
* **Duration Handling**: Video duration is controlled by the slideshow item duration setting, not the video's natural length
  * If item duration < video length: video is stopped and slideshow advances
  * If item duration > video length: video ends and slideshow waits for remaining time before advancing
* **Format Support**: Support modern web-compatible formats (MP4, WebM) with H.264/VP8+ codecs for maximum compatibility
* **Fallback Handling**: If a video fails to load or play, the slideshow skips to the next item after a brief timeout

## Technical Details

### Backend Architecture
* **Web Framework**: Flask for the backend server
* **Database**: SQLite3 initially, designed for easy migration to MariaDB or PostgreSQL
* **Database Migrations**: Flask-Migrate (Alembic) for schema versioning and upgrades
* **ORM**: SQLAlchemy for database abstraction and future database engine flexibility

### Frontend Architecture (Hybrid Approach)
* **Display Interface**: Server-side rendering with Jinja2 templates
  * Simpler and more reliable for kiosk devices with limited processing power
  * Minimal JavaScript dependencies for better stability
  * Basic JavaScript for slideshow transitions and Server-Sent Events (SSE) for real-time updates
  * Optimized for consistent rendering across different browsers and devices
* **User Management Interface**: React Single Page Application (SPA)
  * Rich interactive experience for complex operations (drag-and-drop, file uploads)
  * Real-time updates and dynamic content management
  * Responsive design for various screen sizes
  * Advanced form handling and validation

### URL Structure and Routing
* **Display Routes**: `/display/<display_name>` → Jinja2 templates for kiosk displays
* **User Management Routes**: `/admin/*` → React SPA for user interface
* **API Routes**: `/api/*` → REST API endpoints for React frontend communication
* **Static File Routes**: `/uploads/*` → Served uploaded media files
* **Authentication Routes**: `/auth/*` → Login/logout endpoints

### API Design
* **REST API**: JSON-based API for React frontend communication
* **Endpoints Structure**:
  * `/api/slideshows/` - CRUD operations for slideshows
  * `/api/slideshow-items/` - CRUD operations for slideshow items
  * `/api/displays/` - Display management and assignment
  * `/api/uploads/` - File upload handling
  * `/api/auth/` - Authentication endpoints
* **Traditional Flask Routes**: For display rendering and file serving
* **API Versioning**: `/api/v1/` prefix for future API evolution

### Real-time Communication
* **Server-Sent Events (SSE)** for real-time updates:
  * **Display Updates**: `/api/display/<display_name>/events` - Notify displays of slideshow changes
  * **Dashboard Updates**: `/api/admin/events` - Real-time display status and system notifications
  * **Change Propagation**: Updates take effect at the end of current slideshow cycle
* **Fallback Polling**: For clients that don't support SSE

### File Storage and Management
* **Storage Location**: Local filesystem with organized directory structure
* **Directory Structure**: 
  ```
  uploads/
  ├── images/
  │   └── <user_id>/
  │       └── <slideshow_id>/
  └── videos/
      └── <user_id>/
          └── <slideshow_id>/
  ```
* **File Serving**: Flask serves uploaded files with proper MIME types and caching headers
* **Supported Formats**:
  * **Images**: JPEG, PNG, GIF, WebP
  * **Videos**: MP4, WebM, AVI (with size limitations)
* **File Size Limits**: 
  * Images: 50MB max
  * Videos: 500MB max
* **File Cleanup**: Automatic cleanup of orphaned files when slideshows/items are deleted

### Security Considerations
* **File Upload Security**:
  * File type validation based on content, not just extension
  * Filename sanitization to prevent directory traversal
  * Virus scanning integration point for future enhancement
* **Content Security Policy**: Strict CSP headers for admin interface, relaxed for display interface to allow embedded content
* **Web Page Embedding**: 
  * Use `<iframe>` with sandbox attributes for external URLs
  * Document limitations: some sites block iframe embedding (X-Frame-Options)
  * Fallback to screenshot capture for problematic sites (future enhancement)
* **HTTPS Enforcement**: Configurable HTTPS redirect for production deployments
* **Session Security**: Secure session cookies with appropriate flags
* **Input Validation**: Comprehensive validation for all user inputs and API endpoints

### Error Handling and Resilience
* **Display Error Handling**:
  * **Network Failures**: Displays should gracefully handle connectivity loss
  * **Media Loading Failures**: Skip failed items with user-configurable retry attempts
  * **Fallback Content**: Continue with available content
* **File Upload Error Handling**:
  * Progress indicators with error recovery
  * Partial upload resumption capability
  * Clear error messages for file format/size issues
* **Database Error Handling**: 
  * Connection pooling and retry logic
  * Graceful degradation for read-only operations during maintenance
* **API Error Responses**: Consistent JSON error format with appropriate HTTP status codes

### Configuration Management
* **Environment-based Configuration**: Separate configs for development, testing, production
* **Configuration Sources**: Environment variables
* **Key Configuration Options**:
  * Database connection string
  * File upload directory and size limits
  * Session secret key
  * HTTPS enforcement
  * Default slideshow timeout
  * Debug mode settings

### Performance and Monitoring
* **Caching Strategy**: 
  * Static file caching with appropriate headers
  * Database query optimization with SQLAlchemy
  * Optional Redis integration for session storage and caching
* **Logging and Monitoring**:
  * Structured logging with JSON format
  * Request/response logging for debugging
  * Performance metrics collection points
  * Display heartbeat monitoring
* **Resource Management**:
  * File size monitoring and cleanup
  * Database connection pooling
  * Memory usage optimization for large file uploads

### Development and Deployment
* Dependencies managed with `poetry`
* Tests run via `nox` and written with pytest
* Formatting/style via `black`; linting and style checking via `pycodestyle` and `flake8`.
* Designed to run either as a local Python application (installed as a Python package via `pip`, from PyPI) or as a Docker container
* **Docker Configuration**: Multi-stage builds for optimized production images
* **Environment Setup**: Docker Compose for development environment
* Database schema migrations to allow easy upgrades between versions
* Semantic versioning
* **CI/CD Integration Points**: GitHub Actions workflow templates
* All code MUST be readable, maintainable, and well-written, adhering to the relevant style and formatting guidelines.
* All code must be well commented, with comments intended for both human and AI readers.
* Comprehensive documentation must be generated in addition to code.
* All implementation milestones must also include complete test coverage with all tests passing, as well as comprehensive documentation.

## Implementation Phases

### Phase 1: Core Backend and Basic Display
* Flask application setup with basic routing
* SQLAlchemy models and database schema
* Basic authentication system (permissive initial implementation)
* Simple slideshow display with Jinja2 templates
* Basic CRUD operations for slideshows and items
* Comprehensive testing and documentation of these items

### Phase 2: User Management Interface
* React SPA setup and build integration
* REST API implementation
* File upload functionality
* Advanced slideshow management (drag-and-drop reordering)
* User dashboard with display management
* Comprehensive testing and documentation of these items

### Phase 3: Real-time Features and Polish
* Server-Sent Events implementation
* Real-time display updates
* Enhanced error handling and resilience
* Performance optimization and caching
* Comprehensive testing and documentation

### Phase 4: Production Readiness
* Security hardening
* Docker containerization
* Production deployment documentation
* Monitoring and logging enhancements
* Package distribution setup (PyPI)
