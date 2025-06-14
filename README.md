# Kiosk Show Replacement

A self-hosted digital signage solution built with Flask, serving as a replacement for the defunct kiosk.show service.

## Features

- 🖥️ **Web-based Management**: Create and manage slideshows through an intuitive web interface
- 📺 **Kiosk Display Mode**: Full-screen slideshow display optimized for kiosk devices
- 🎯 **Multiple Content Types**: Support for images, web pages, and text slides
- ⏱️ **Flexible Timing**: Customizable display duration for each slide
- 🔄 **Real-time Updates**: Dynamic slideshow management without restarts
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🛠️ **RESTful API**: Full API for programmatic management
- 🐍 **Modern Python**: Built with Flask, SQLAlchemy, and modern Python practices

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jantman/kiosk-show-replacement.git
   cd kiosk-show-replacement
   ```

2. **Install dependencies:**
   ```bash
   poetry install
   ```

3. **Initialize the database:**
   
   **Option A: Using Poetry script shortcut (Recommended)**
   ```bash
   # Basic database setup
   poetry run kiosk-init-db
   
   # Or with sample data for testing
   poetry run kiosk-init-db --sample-data
   ```
   
   **Option B: Using the script directly**
   ```bash
   # Basic database setup
   poetry run python scripts/init_db.py
   
   # Or with sample data for testing
   poetry run python scripts/init_db.py --sample-data
   ```

4. **Start the development server:**
   ```bash
   poetry run python run.py
   ```

5. **Open your browser:**
   Navigate to `http://localhost:5000` to access the application.

### Database Initialization Details

The database initialization script (`scripts/init_db.py`) provides several options:

- `--sample-data` / `-s`: Creates demonstration slideshows with sample content
- `--database-url` / `-d`: Override the database URL from environment
- `--force` / `-f`: Force initialization even if tables already exist

**Examples:**
```bash
# Initialize with custom database URL
poetry run python scripts/init_db.py -d "sqlite:///custom.db"

# Initialize with sample data for testing
poetry run python scripts/init_db.py --sample-data

# Force reinitialize (preserves existing data)
poetry run python scripts/init_db.py --force --sample-data
```

The sample data includes:
- **Welcome Demo**: A comprehensive slideshow showcasing different content types
- **Simple Announcements**: Basic text-only slides for announcements

## Usage

### Creating a Slideshow

1. Navigate to the home page
2. Click "Create New Slideshow"
3. Enter a name and optional description
4. Click "Create Slideshow"

### Adding Slides

1. Go to the slideshow edit page
2. Select content type (Image, Web Page, or Text)
3. Enter the content details
4. Set display duration in seconds
5. Click "Add Slide"

### Displaying a Slideshow

1. From the home page or manage page, click "Display" on any slideshow
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
│   ├── templates/                   # Jinja2 templates
│   └── utils/                       # Utility functions
├── tests/                           # Test suite
├── docs/                            # Documentation
├── pyproject.toml                   # Poetry configuration
└── run.py                           # Development server
```

### Running Tests

```bash
poetry run pytest
```

### Test Database Setup

For testing, you may want to set up a separate test database:

```bash
# Set up test database with sample data
DATABASE_URL="sqlite:///test.db" poetry run python scripts/init_db.py --sample-data

# Run tests against test database
DATABASE_URL="sqlite:///test.db" poetry run pytest
```

### Code Quality

```bash
# Format code
poetry run black .

# Check code style
poetry run flake8

# Type checking
poetry run mypy kiosk_show_replacement/
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
```

Key configuration options:

- `FLASK_ENV`: Environment mode (development/production)
- `SECRET_KEY`: Flask secret key for sessions
- `DATABASE_URL`: Database connection string
- `UPLOAD_FOLDER`: Directory for uploaded files

## Deployment

### Using Docker (Recommended)

```bash
# Build image
docker build -t kiosk-show-replacement .

# Run container
docker run -p 5000:5000 -v ./data:/app/data kiosk-show-replacement
```

### Manual Deployment

1. Install dependencies in production mode:
   ```bash
   poetry install --without dev
   ```

2. Set environment variables:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   export DATABASE_URL=postgresql://user:pass@localhost/kiosk_show
   ```

3. Initialize database:
   ```bash
   poetry run kiosk-init-db
   # Or with sample data for initial testing:
   # poetry run kiosk-init-db --sample-data
   ```

4. Run with a production WSGI server:
   ```bash
   poetry run gunicorn "kiosk_show_replacement.app:create_app()" -b 0.0.0.0:5000
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
