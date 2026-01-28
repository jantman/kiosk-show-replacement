# Kiosk Show Replacement

[![CI](https://github.com/jantman/kiosk-show-replacement/actions/workflows/ci.yml/badge.svg)](https://github.com/jantman/kiosk-show-replacement/actions/workflows/ci.yml)
[![Release](https://github.com/jantman/kiosk-show-replacement/actions/workflows/release.yml/badge.svg)](https://github.com/jantman/kiosk-show-replacement/actions/workflows/release.yml)

A self-hosted digital signage solution built with Flask, serving as a replacement for the defunct kiosk.show service.

## Features

- **Web-based Management**: Create and manage slideshows through an intuitive web interface
- **Modern Admin Interface**: React-based admin panel with real-time updates and responsive design
- **Kiosk Display Mode**: Full-screen slideshow display optimized for kiosk devices
- **Multiple Content Types**: Support for images, videos, web pages, text slides, and Skedda calendar displays
- **Flexible Timing**: Customizable display duration for each slide
- **Real-time Updates**: Dynamic slideshow management without restarts
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **RESTful API**: Full API for programmatic management
- **Modern Python**: Built with Flask, SQLAlchemy, and modern Python practices
- **Modern Frontend**: React 18 with TypeScript, Bootstrap 5, and Vite build system

## Quick Start

Docker is the only supported deployment method for production. The application supports
both x86_64 and ARM64 architectures (including Raspberry Pi).

### Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jantman/kiosk-show-replacement.git
   cd kiosk-show-replacement
   ```

2. **Configure environment:**
   ```bash
   cp .env.docker.example .env

   # Generate a secure secret key
   python -c "import secrets; print(secrets.token_hex(32))"

   # Edit .env and set required values:
   # - SECRET_KEY (use generated key)
   # - MYSQL_ROOT_PASSWORD
   # - MYSQL_PASSWORD
   # - KIOSK_ADMIN_PASSWORD
   ```

3. **Start the application:**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Access the application:**
   - **Admin Interface**: http://localhost:5000/admin
   - **API**: http://localhost:5000/api/v1/

Default admin credentials are `admin`/`admin` unless you set `KIOSK_ADMIN_PASSWORD` in your environment.

For detailed deployment instructions, environment variables, NewRelic APM setup,
production checklist, and troubleshooting, see the [Deployment Guide](docs/deployment.rst).

## Usage

### Admin Interface

The modern React admin interface provides the best user experience:

1. **Access the admin interface**: http://localhost:5000/admin
2. **Login**: Use `admin`/`admin` (change in production!)
3. **Dashboard**: View system statistics and quick actions
4. **Manage Slideshows**: Create, edit, and organize slideshow content
5. **Manage Displays**: Monitor display devices and assign slideshows
6. **View History**: Track slideshow assignment changes

### Creating a Slideshow

1. Navigate to the admin interface
2. Click "Create New Slideshow"
3. Enter a name and optional description
4. Click "Create Slideshow"

### Adding Slides

1. Go to the slideshow edit page
2. Select content type (Image, Video, Web Page, Text, or Skedda Calendar)
3. Enter the content details (upload file or provide URL)
4. Set display duration in seconds (auto-detected for videos)
5. Click "Add Slide"

**Skedda Calendar:** For displaying booking/reservation calendars from Skedda,
select "Skedda Calendar" as the content type and enter your Skedda iCal feed URL.
The calendar will display as a visual grid showing time slots and space reservations.

**Video Requirements:** Uploaded videos must use browser-compatible codecs
(H.264, VP8, VP9, Theora, or AV1). MP4 with H.264 is recommended for maximum
compatibility. Videos with unsupported codecs will be rejected with a helpful
error message.

### Displaying a Slideshow

1. From the admin interface, click "Display" on any slideshow
2. The slideshow will open in full-screen kiosk mode
3. Press `Escape` to exit kiosk mode

## API Endpoints

### Slideshows

- `GET /api/slideshows` - List all slideshows
- `POST /api/slideshows` - Create a new slideshow
- `GET /api/slideshows/{id}` - Get slideshow details
- `POST /api/slideshows/{id}/slides` - Add slide to slideshow

### Slides

- `PUT /api/slides/{id}` - Update a slide
- `DELETE /api/slides/{id}` - Delete a slide

## Development

For local development setup using Python and Poetry, see [docs/development.rst](docs/development.rst).

### Project Structure

```
kiosk-show-replacement/
├── kiosk_show_replacement/          # Main application package
│   ├── api/                         # API blueprints
│   ├── app.py                       # Flask application factory
│   ├── cli/                         # CLI commands
│   ├── config/                      # Configuration management
│   ├── display/                     # Display blueprints
│   ├── models/                      # Database models
│   ├── slideshow/                   # Slideshow management
│   ├── static/                      # Static assets
│   │   └── dist/                    # Built React admin interface
│   ├── templates/                   # Jinja2 templates
│   └── utils/                       # Utility functions
├── frontend/                        # React admin interface
│   ├── src/                         # React source code
│   │   ├── components/              # React components
│   │   ├── pages/                   # Page components
│   │   ├── contexts/                # React contexts
│   │   ├── hooks/                   # Custom hooks
│   │   ├── types/                   # TypeScript types
│   │   └── utils/                   # Frontend utilities
│   ├── package.json                 # Node.js dependencies
│   ├── vite.config.ts              # Vite configuration
│   └── tsconfig.json               # TypeScript configuration
├── tests/                           # Test suite
├── docs/                            # Documentation
├── pyproject.toml                   # Poetry configuration
└── run.py                           # Development server
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure code quality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the original kiosk.show service
- Built with Flask, Bootstrap, and modern web technologies
- Designed for self-hosting and digital signage use cases
