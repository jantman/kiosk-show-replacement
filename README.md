# Kiosk Show Replacement

A self-hosted digital signage solution built with Flask, serving as a replacement for the defunct kiosk.show service.

## Features

- 🖥️ **Web-based Management**: Create and manage slideshows through an intuitive web interface
- 🎛️ **Modern Admin Interface**: React-based admin panel with real-time updates and responsive design
- 📺 **Kiosk Display Mode**: Full-screen slideshow display optimized for kiosk devices
- 🎯 **Multiple Content Types**: Support for images, web pages, and text slides
- ⏱️ **Flexible Timing**: Customizable display duration for each slide
- 🔄 **Real-time Updates**: Dynamic slideshow management without restarts
- 📱 **Responsive Design**: Works on desktop, tablet, and mobile devices
- 🛠️ **RESTful API**: Full API for programmatic management
- 🐍 **Modern Python**: Built with Flask, SQLAlchemy, and modern Python practices
- ⚡ **Modern Frontend**: React 18 with TypeScript, Bootstrap 5, and Vite build system

## Quick Start

### Prerequisites

- Python 3.9 or higher
- Poetry (for dependency management)
- Node.js 18.0 or higher and npm (for the React admin interface)

### Important: Environment Activation

**Before starting work with this project in any new terminal session, you MUST run:**

```bash
eval $(poetry env activate)
```

This activates the Poetry virtual environment **once per terminal session** and allows you to run all subsequent commands without the `poetry run` prefix. All examples in this documentation assume you have already activated the environment in your current terminal session.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jantman/kiosk-show-replacement.git
   cd kiosk-show-replacement
   ```

2. **Install dependencies and activate environment:**
   ```bash
   # Install Python dependencies
   poetry install
   eval $(poetry env activate)
   
   # Install Node.js dependencies for React admin interface
   cd frontend
   npm install
   cd ..
   ```

3. **Initialize the database:**
   
   **Option A: Using Poetry script shortcut (Recommended)**
   ```bash
   # Basic database setup
   kiosk-init-db
   
   # Or with sample data for testing
   kiosk-init-db --sample-data
   ```
   
   **Option B: Using the script directly**
   ```bash
   # Basic database setup
   python scripts/init_db.py
   
   # Or with sample data for testing
   python scripts/init_db.py --sample-data
   ```

4. **Build the React admin interface:**
   ```bash
   cd frontend
   npm run build
   cd ..
   ```

5. **Start the development server:**
   ```bash
   python run.py
   ```

6. **Open your browser:**
   - **Admin Interface**: http://localhost:5000/admin (login: admin/admin)  
   - **Legacy Interface**: http://localhost:5000
   - **API**: http://localhost:5000/api/v1/

### Development Mode (Frontend Hot Reload)

For frontend development with hot reload:

1. **Start the Flask backend:**
   ```bash
   eval $(poetry env activate)
   python run.py
   ```

2. **In a separate terminal, start the React dev server:**
   ```bash
   cd frontend
   npm run dev
   ```

This provides:
- **Flask Backend**: http://localhost:5000 (API and display endpoints)
- **React Frontend**: http://localhost:3000 (Admin interface with hot reload)

### Database Initialization Details

The database initialization script (`scripts/init_db.py`) provides several options:

- `--sample-data` / `-s`: Creates demonstration slideshows with sample content
- `--database-url` / `-d`: Override the database URL from environment
- `--force` / `-f`: Force initialization even if tables already exist

**Examples:**
```bash
# First, activate the environment
eval $(poetry env activate)

# Initialize with custom database URL
python scripts/init_db.py -d "sqlite:///custom.db"

# Initialize with sample data for testing
python scripts/init_db.py --sample-data

# Force reinitialize (preserves existing data)
python scripts/init_db.py --force --sample-data
```

The sample data includes:
- **Welcome Demo**: A comprehensive slideshow showcasing different content types
- **Simple Announcements**: Basic text-only slides for announcements

## Usage

### Admin Interface (Recommended)

The modern React admin interface provides the best user experience:

1. **Access the admin interface**: http://localhost:5000/admin
2. **Login**: Use `admin`/`admin` (change in production!)
3. **Dashboard**: View system statistics and quick actions
4. **Manage Slideshows**: Create, edit, and organize slideshow content
5. **Manage Displays**: Monitor display devices and assign slideshows
6. **View History**: Track slideshow assignment changes

### Legacy Interface

The original Flask-based interface is still available at the root URL.

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

### Running Tests

The project includes comprehensive testing for both backend and frontend:

**Backend Tests:**

```bash
# First, activate the environment
eval $(poetry env activate)

# Run unit tests
nox -s test

# Run integration tests
nox -s test-integration

# Run end-to-end tests (requires Chrome/Chromium)
nox -s test-e2e

# Run all tests with coverage
nox -s test-all
```

**Frontend Tests:**

```bash
# Navigate to frontend directory
cd frontend

# Run tests
npm test

# Run tests with coverage
npm run test:run

# Run tests with UI
npm run test:ui
```

**Test Types:**
- **Backend Unit Tests**: Test individual components in isolation
- **Backend Integration Tests**: Test component interactions using Flask test client
- **Backend E2E Tests**: Test complete user workflows using browser automation
- **Frontend Tests**: Test React components with Vitest and React Testing Library

**E2E Test Requirements:**
E2E tests require Chrome or Chromium browser installed:

```bash
# ArchLinux
sudo pacman -S google-chrome
# or chromium

# Ubuntu/Debian  
sudo apt install google-chrome-stable
# or chromium-browser

# Fedora
sudo dnf install google-chrome-stable
# or chromium
```

### Test Database Setup

For testing, you may want to set up a separate test database:

```bash
# First, activate the environment
eval $(poetry env activate)

# Set up test database with sample data
DATABASE_URL="sqlite:///test.db" python scripts/init_db.py --sample-data

# Run tests against test database
DATABASE_URL="sqlite:///test.db" nox -s test
```

### Code Quality

**Backend Quality Checks:**

```bash
# First, activate the environment
eval $(poetry env activate)

# Format code
nox -s format

# Check code style
nox -s lint

# Type checking
nox -s type_check

# Run all quality checks
nox  # Runs format, lint, and test by default
```

**Frontend Quality Checks:**

```bash
cd frontend

# Type checking
npm run type-check

# Build check
npm run build

# Development server
npm run dev
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

Docker provides the easiest deployment method with support for both x86_64 and ARM64 (Raspberry Pi).

**Quick Start (Production with MariaDB):**

```bash
# Copy and configure environment
cp .env.docker.example .env
# Edit .env with your passwords and secret key

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Access at http://localhost:5000/admin
```

**Development with Docker (SQLite):**

```bash
# Start development environment
docker-compose up

# Access at http://localhost:5000/admin (login: admin/admin)
```

For detailed deployment instructions, production checklist, and troubleshooting, see the [Deployment Guide](docs/deployment.rst).

### Manual Deployment

1. Install dependencies in production mode:
   ```bash
   poetry install --without dev
   eval $(poetry env activate)
   ```

2. Set environment variables:
   ```bash
   export FLASK_ENV=production
   export SECRET_KEY=your-secure-secret-key
   export DATABASE_URL=postgresql://user:pass@localhost/kiosk_show
   ```

3. Initialize database:
   ```bash
   kiosk-init-db
   # Or with sample data for initial testing:
   # kiosk-init-db --sample-data
   ```

4. Run with a production WSGI server:
   ```bash
   gunicorn "kiosk_show_replacement.app:create_app()" -b 0.0.0.0:5000
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
