Development
===========

Setting up Development Environment
---------------------------------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/jantman/kiosk-show-replacement.git
      cd kiosk-show-replacement

2. Install Poetry (if not already installed):

   .. code-block:: bash

      curl -sSL https://install.python-poetry.org | python3 -

3. Install dependencies and activate environment:

   .. code-block:: bash

      poetry install
      eval $(poetry env activate)

4. Set up the development environment:

   .. code-block:: bash

      nox -s dev-setup

Development Workflow
--------------------

This project uses `nox <https://nox.thea.codes/>`_ for development automation.

Available Commands
~~~~~~~~~~~~~~~~~~

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Then run the development commands:

.. code-block:: bash

   # Format code with black and isort
   nox -s format

   # Run linting (flake8, pycodestyle)
   nox -s lint

   # Run type checking with mypy
   nox -s type_check

   # Run unit tests
   nox -s test

   # Run integration tests
   nox -s test-integration

   # Run end-to-end tests with Playwright
   nox -s test-e2e

   # Run all tests with coverage
   nox -s test-all

   # Build documentation
   nox -s docs

   # Serve documentation locally
   nox -s docs-serve

   # Clean build artifacts
   nox -s clean

   # Check for security vulnerabilities
   nox -s safety

Default Development Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Running ``nox`` without arguments will run the default development session (format, lint, test):

.. code-block:: bash

   # After activating environment
   nox

Code Style
----------

This project uses several tools to maintain code quality:

* **Black**: Code formatting
* **isort**: Import sorting
* **flake8**: Linting and style checking
* **mypy**: Type checking

Configuration files:

* ``.flake8``: flake8 configuration
* ``pyproject.toml``: Black, isort, and mypy configuration

Testing
-------

The project uses pytest for testing with three types of tests:

1. **Unit Tests** (``tests/unit/``): Test individual functions and classes in isolation
2. **Integration Tests** (``tests/integration/``): Full-stack browser tests of React frontend + Flask backend
3. **End-to-End Tests** (``tests/e2e/``): Browser tests of Flask server-rendered pages

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Unit Tests
~~~~~~~~~~

Located in ``tests/unit/``, these test individual functions and classes in isolation.

.. code-block:: bash

   nox -s test

Integration Tests
~~~~~~~~~~~~~~~~~

Located in ``tests/integration/``, these test the complete React frontend + Flask backend integration through a real browser using Playwright.

**What Integration Tests Cover:**

* **Full-Stack Integration**: React frontend communicating with Flask backend through real HTTP requests
* **Real Browser Testing**: Uses Playwright to control system Chrome/Chromium browser
* **Complete User Workflows**: Full user journeys from login to dashboard interaction
* **Authentication Integration**: Tests session-based authentication across frontend and backend
* **API Communication**: Validates REST API endpoints work correctly with React frontend
* **Database Integration**: Tests data persistence across the full application stack

**Key Characteristics:**

* Use Playwright to automate a real Chrome/Chromium browser
* Start both Flask backend (port 5000) and Vite frontend (port 3001) servers
* Test actual user interactions (clicking, typing, form submission)
* Verify complete authentication workflows and dashboard functionality
* Include multi-step user journeys that span multiple application components
* Test real-world scenarios that users actually experience

**Examples:**

* Complete login workflow (visit frontend → authenticate → access dashboard → see content)
* Frontend-backend authentication integration (session cookies, API calls)
* Dashboard data loading from Flask backend APIs
* User interface responsiveness and error handling

.. code-block:: bash

   nox -s test-integration

**System Requirements for Integration Tests:**

Integration tests require a system-installed Chrome or Chromium browser and Node.js for the frontend development server. The test framework automatically detects and uses the first available browser from these common locations:

* ``/usr/bin/google-chrome-stable`` (Google Chrome on most Linux distributions)
* ``/usr/bin/chromium-browser`` (Chromium on Ubuntu/Debian)
* ``/usr/bin/google-chrome`` (Alternative Chrome location)
* ``/usr/bin/chromium`` (Chromium on Arch/Fedora)

End-to-End Tests
~~~~~~~~~~~~~~~~

Located in ``tests/e2e/``, these test complete user workflows using Playwright browser automation with a live Flask server (backend-only, no React frontend).

**What E2E Tests Cover:**

* **Flask Server Testing**: Tests run against a live Flask server instance with traditional Jinja2 templates
* **Browser Automation**: Use Playwright to control a real Chromium browser
* **Server-Rendered Pages**: Test traditional Flask views and forms (non-React pages)
* **Basic User Interactions**: Click buttons, fill forms, navigate pages like a real user
* **Authentication Workflows**: Complete login/logout cycles using Flask's built-in auth
* **Cross-page Navigation**: Verify navigation between different Flask template pages
* **Visual Verification**: Screenshots and videos captured on test failures

**Key Characteristics:**

* Use Playwright to control a real browser (Chromium)
* Test against a live Flask server with server-rendered templates
* Focus on traditional Flask web pages (not the React admin interface)
* Verify backend-only workflows and basic web functionality
* Include visual feedback (screenshots/videos on failure)
* Test browser behavior for server-rendered content

**Examples:**

* Basic server access and Flask template rendering
* Traditional Flask form submission and validation
* Server-side authentication and session management
* Flask route navigation and error handling

.. code-block:: bash

   nox -s test-e2e

**System Requirements for E2E Tests:**

E2E tests require a system-installed Chrome or Chromium browser. The test framework 
automatically detects and uses the first available browser from these common locations:

* ``/usr/bin/google-chrome-stable`` (Google Chrome on most Linux distributions)
* ``/usr/bin/chromium-browser`` (Chromium on Ubuntu/Debian)
* ``/usr/bin/google-chrome`` (Alternative Chrome location)
* ``/usr/bin/chromium`` (Chromium on Arch/Fedora)

**Installing Chrome/Chromium:**

.. code-block:: bash

   # ArchLinux
   sudo pacman -S google-chrome
   # or
   sudo pacman -S chromium
   
   # Ubuntu/Debian
   sudo apt install google-chrome-stable
   # or 
   sudo apt install chromium-browser
   
   # Fedora
   sudo dnf install google-chrome-stable
   # or
   sudo dnf install chromium

**E2E Test Configuration:**

E2E tests use Playwright with the following default settings:

* **Browser**: Chromium (headless by default)
* **Screenshots**: Captured only on test failures
* **Videos**: Recorded and retained only on test failures
* **Live Server**: Automatic Flask server startup for testing

**Running E2E Tests in Headed Mode:**

For development and debugging, you can run tests with a visible browser:

.. code-block:: bash

   # Set environment variable for headed mode
   PLAYWRIGHT_HEADED=1 nox -s test-e2e
   
   # Or run specific tests
   nox -s test-e2e -- --headed -k "test_login"

Test Configuration
~~~~~~~~~~~~~~~~~~

* ``pytest.ini``: Pytest configuration
* ``tests/conftest.py``: Shared test fixtures

Coverage
~~~~~~~~

Code coverage is measured using pytest-cov. Coverage reports are generated in:

* Terminal output (with ``--cov-report=term-missing``)
* HTML report in ``htmlcov/`` directory
* XML report as ``coverage.xml``

Database Testing
~~~~~~~~~~~~~~~~

Tests use an in-memory SQLite database for speed. The test database is automatically created and destroyed for each test session.

Test Type Summary
~~~~~~~~~~~~~~~~~

**When to use each test type:**

* **Unit Tests** (``nox -s test``): Testing individual functions, classes, or small components in isolation. Fast and focused.
* **Integration Tests** (``nox -s test-integration``): Testing the complete React + Flask application stack through a real browser. Use for validating user experiences and frontend-backend integration.
* **E2E Tests** (``nox -s test-e2e``): Testing Flask server-rendered pages (non-React) through a browser. Use for basic server functionality and traditional web page testing.

**Test execution speed:** Unit < E2E < Integration (Integration tests are slowest due to starting both servers)

Testing Session Distinctions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**test-integration Session**

* **Purpose**: Full-stack React frontend + Flask backend integration testing
* **Technology**: Playwright browser automation with dual server setup
* **Test Location**: ``tests/integration/``
* **What it tests**: Complete user workflows through React admin interface
* **Server Setup**: Starts both Flask (backend) and Vite (frontend) servers
* **Use Cases**:

  - React component interaction with Flask APIs
  - Authentication flows through React frontend
  - Real-time features (SSE) in React admin interface
  - Frontend-backend data synchronization
  - Complete user journeys (login → dashboard → management)

**test-e2e Session**

* **Purpose**: Flask server-rendered pages testing (traditional web)
* **Technology**: Playwright browser automation with Flask server only
* **Test Location**: ``tests/e2e/``
* **What it tests**: Traditional Flask Jinja2 templates and server-side functionality
* **Server Setup**: Starts only Flask server with template rendering
* **Use Cases**:

  - Basic server access and template rendering
  - Traditional Flask form submission
  - Server-side authentication workflows
  - Non-React page functionality
  - Flask route navigation and error handling

**Key Distinction Rules**

* **Integration tests** = React frontend + Flask backend integration
* **E2E tests** = Flask backend only (traditional web pages)
* **SSE functionality** belongs in integration tests (React admin interface feature)
* **Basic server access** belongs in E2E tests (fundamental Flask functionality)

Project Structure
-----------------

.. code-block:: text

   kiosk-show-replacement/
   ├── kiosk_show_replacement/       # Main package
   │   ├── __init__.py
   │   ├── app.py                    # Flask application factory
   │   ├── api/                      # REST API blueprints
   │   ├── auth/                     # Authentication (future)
   │   ├── cli/                      # Command-line interface
   │   ├── config/                   # Configuration management
   │   ├── display/                  # Display/kiosk blueprints
   │   ├── models/                   # Database models
   │   ├── slideshow/                # Slideshow management
   │   ├── static/                   # Static files
   │   ├── templates/                # Jinja2 templates
   │   └── utils/                    # Utility functions
   ├── tests/                        # Test suite
   │   ├── unit/                     # Unit tests
   │   ├── integration/              # Integration tests
   │   └── e2e/                      # End-to-end tests
   ├── docs/                         # Documentation
   ├── scripts/                      # Utility scripts
   ├── noxfile.py                    # Development automation
   ├── pyproject.toml               # Poetry configuration
   └── README.md

Adding New Features
-------------------

1. Create a new branch for your feature
2. Write tests first (TDD approach)
3. Implement the feature
4. Run the full test suite
5. Update documentation
6. Submit a pull request

Database Migrations
-------------------

This project uses Flask-Migrate for database migrations.

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Then run migration commands:

.. code-block:: bash

   # Create a new migration
   flask db migrate -m "Description of changes"

   # Apply migrations
   flask db upgrade

   # Rollback migrations
   flask db downgrade

Frontend Development
--------------------

The kiosk-show-replacement project includes a modern React-based admin interface alongside the Flask backend. This section covers everything you need to know about developing and maintaining the frontend.

Frontend Technology Stack
~~~~~~~~~~~~~~~~~~~~~~~~~~

The frontend uses modern web technologies:

**Core Technologies:**

* **React 18**: Modern React with hooks and functional components
* **TypeScript**: Type-safe JavaScript for better development experience
* **Vite**: Fast build tool and development server
* **React Router**: Client-side routing for single-page application

**UI Framework:**

* **React Bootstrap**: Bootstrap 5 components for React
* **Bootstrap 5**: CSS framework for responsive design
* **React Router Bootstrap**: Integration between React Router and Bootstrap

**Development Tools:**

* **npm**: Package manager for JavaScript dependencies
* **ESLint**: JavaScript/TypeScript linting (future enhancement)
* **Prettier**: Code formatting (future enhancement)

Frontend Project Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   frontend/                         # Frontend application root
   ├── package.json                  # npm dependencies and scripts
   ├── tsconfig.json                 # TypeScript configuration
   ├── vite.config.ts               # Vite build configuration
   ├── index.html                   # HTML entry point
   └── src/                         # Source code
       ├── main.tsx                 # Application entry point
       ├── App.tsx                  # Main app component
       ├── components/              # Reusable UI components
       │   ├── common/              # Common components (buttons, forms)
       │   ├── layout/              # Layout components (header, sidebar)
       │   └── ui/                  # Basic UI elements
       ├── pages/                   # Page components
       │   ├── Dashboard.tsx        # Admin dashboard
       │   ├── Login.tsx           # Login page
       │   ├── Slideshows.tsx      # Slideshow management
       │   └── Displays.tsx        # Display management
       ├── contexts/                # React contexts
       │   └── AuthContext.tsx     # Authentication state
       ├── hooks/                   # Custom React hooks
       │   ├── useAuth.ts          # Authentication hook
       │   ├── useApi.ts           # API client hook
       │   └── useLocalStorage.ts  # Local storage hook
       └── types/                   # TypeScript type definitions
           ├── api.ts              # API response types
           ├── auth.ts             # Authentication types
           └── slideshow.ts        # Slideshow data types

Setting Up Frontend Development
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Prerequisites:**

* Node.js 18+ and npm (for frontend development)
* Python 3.13+ and Poetry (for backend integration)

**Initial Setup:**

1. Navigate to the frontend directory:

   .. code-block:: bash

      cd frontend

2. Install frontend dependencies:

   .. code-block:: bash

      npm install

3. Start the Flask backend (in another terminal):

   .. code-block:: bash

      # From project root
      eval $(poetry env activate)
      python -m flask --app kiosk_show_replacement.app run --debug

4. Start the frontend development server:

   .. code-block:: bash

      # From frontend/ directory
      npm run dev

The frontend development server will start on http://localhost:3000 and proxy API requests to the Flask backend on http://localhost:5000.

Frontend Development Commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Development Server:**

.. code-block:: bash

   cd frontend
   npm run dev          # Start development server with hot reload

**Building for Production:**

.. code-block:: bash

   cd frontend
   npm run build        # Build optimized production assets
   npm run preview      # Preview production build locally

**Package Management:**

.. code-block:: bash

   cd frontend
   npm install          # Install dependencies
   npm install <package>    # Add new dependency
   npm install --save-dev <package>  # Add development dependency
   npm update           # Update dependencies
   npm audit            # Check for security vulnerabilities

**TypeScript:**

.. code-block:: bash

   cd frontend
   npx tsc --noEmit     # Type check without building
   npx tsc --watch      # Watch mode type checking

Frontend-Backend Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The frontend integrates with the Flask backend through several mechanisms:

**Development Mode:**
* Vite dev server runs on port 3000
* API requests are proxied to Flask backend on port 5000
* Hot reload for immediate feedback during development

**Production Mode:**
* Frontend builds to ``kiosk_show_replacement/static/dist/``
* Flask serves the built React app at ``/admin`` routes
* All assets served through Flask for single-server deployment

**API Communication:**
* REST API endpoints at ``/api/v1/*``
* Session-based authentication shared between frontend and backend
* Axios client with automatic authentication handling

**Configuration in vite.config.ts:**

.. code-block:: typescript

   export default defineConfig({
     plugins: [react()],
     server: {
       port: 3000,
       proxy: {
         '/api': 'http://localhost:5000',
         '/auth': 'http://localhost:5000',
         '/uploads': 'http://localhost:5000'
       }
     },
     build: {
       outDir: '../kiosk_show_replacement/static/dist'
     }
   })

Authentication Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

The frontend uses the same session-based authentication as the Flask backend:

**Login Flow:**
1. User submits credentials to ``/api/v1/auth/login``
2. Flask creates session and returns user data
3. Frontend stores authentication state in React context
4. Subsequent API requests include session cookies automatically

**Protected Routes:**
* React Router guards routes requiring authentication
* Redirects to login page if not authenticated
* Preserves intended destination for post-login redirect

**API Client (useApi hook):**

.. code-block:: typescript

   const api = useApi();
   
   // Authenticated requests automatically include session
   const slideshows = await api.get('/api/v1/slideshows');
   const newSlideshow = await api.post('/api/v1/slideshows', data);

Adding New Frontend Features
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. Adding a New Page:**

.. code-block:: typescript

   // src/pages/NewPage.tsx
   import React from 'react';
   import { Container } from 'react-bootstrap';
   
   const NewPage: React.FC = () => {
     return (
       <Container>
         <h1>New Page</h1>
         {/* Page content */}
       </Container>
     );
   };
   
   export default NewPage;

**2. Adding to Navigation:**

.. code-block:: typescript

   // src/components/layout/Sidebar.tsx
   import { LinkContainer } from 'react-router-bootstrap';
   import { Nav } from 'react-bootstrap';
   
   <LinkContainer to="/new-page">
     <Nav.Link>New Page</Nav.Link>
   </LinkContainer>

**3. Adding Route:**

.. code-block:: typescript

   // src/App.tsx
   import { Routes, Route } from 'react-router-dom';
   import NewPage from './pages/NewPage';
   
   <Routes>
     <Route path="/new-page" element={<NewPage />} />
   </Routes>

**4. Adding API Integration:**

.. code-block:: typescript

   // Custom hook for API operations
   const useNewFeature = () => {
     const api = useApi();
     
     const fetchData = async () => {
       return await api.get('/api/v1/new-endpoint');
     };
     
     const createItem = async (data: NewItemType) => {
       return await api.post('/api/v1/new-endpoint', data);
     };
     
     return { fetchData, createItem };
   };

Common Frontend Development Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Managing State:**

* Use React Context for global state (authentication, settings)
* Use useState for local component state
* Use useEffect for side effects and API calls

**Handling Forms:**

.. code-block:: typescript

   const [formData, setFormData] = useState({ name: '', description: '' });
   
   const handleSubmit = async (e: React.FormEvent) => {
     e.preventDefault();
     try {
       await api.post('/api/v1/endpoint', formData);
       // Handle success
     } catch (error) {
       // Handle error
     }
   };

**Error Handling:**

.. code-block:: typescript

   const [error, setError] = useState<string | null>(null);
   const [loading, setLoading] = useState(false);
   
   const handleApiCall = async () => {
     setLoading(true);
     setError(null);
     try {
       const result = await api.get('/api/v1/data');
       // Handle success
     } catch (err) {
       setError(err instanceof Error ? err.message : 'An error occurred');
     } finally {
       setLoading(false);
     }
   };

**Responsive Design:**

Use Bootstrap classes and React Bootstrap components for responsive layouts:

.. code-block:: typescript

   <Container>
     <Row>
       <Col xs={12} md={6} lg={4}>
         <Card>
           <Card.Body>Content</Card.Body>
         </Card>
       </Col>
     </Row>
   </Container>

TypeScript Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Define Types for API Responses:**

.. code-block:: typescript

   // src/types/api.ts
   export interface ApiResponse<T> {
     success: boolean;
     data: T;
     message?: string;
   }
   
   export interface Slideshow {
     id: number;
     name: string;
     description: string;
     active: boolean;
     items: SlideshowItem[];
   }

**Use Proper Component Props Types:**

.. code-block:: typescript

   interface SlideshowCardProps {
     slideshow: Slideshow;
     onEdit: (slideshow: Slideshow) => void;
     onDelete: (id: number) => void;
   }
   
   const SlideshowCard: React.FC<SlideshowCardProps> = ({
     slideshow,
     onEdit,
     onDelete
   }) => {
     // Component implementation
   };

**Custom Hook Type Safety:**

.. code-block:: typescript

   interface UseApiResult {
     get: <T>(url: string) => Promise<T>;
     post: <T>(url: string, data: any) => Promise<T>;
     put: <T>(url: string, data: any) => Promise<T>;
     delete: (url: string) => Promise<void>;
   }
   
   const useApi = (): UseApiResult => {
     // Hook implementation
   };

Troubleshooting Frontend Issues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Common Issues:**

1. **Build Errors:**
   - Check TypeScript errors: ``npx tsc --noEmit``
   - Verify all dependencies are installed: ``npm install``
   - Clear node_modules and reinstall: ``rm -rf node_modules package-lock.json && npm install``

2. **API Connection Issues:**
   - Ensure Flask backend is running on port 5000
   - Check Vite proxy configuration in ``vite.config.ts``
   - Verify CORS is enabled in Flask app

3. **Authentication Problems:**
   - Check browser cookies and session storage
   - Verify API endpoints return proper status codes
   - Test authentication flow in browser dev tools

4. **Hot Reload Not Working:**
   - Restart Vite dev server: ``npm run dev``
   - Check file permissions and paths
   - Clear browser cache

**Debugging Tools:**

* Browser DevTools for inspecting network requests and React components
* React Developer Tools browser extension
* TypeScript compiler for type checking
* Flask debug toolbar for backend API issues

Frontend Testing (Future Enhancement)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When adding frontend tests, consider:

* **Unit Tests**: Jest and React Testing Library for component testing
* **Integration Tests**: Testing API integration and user workflows
* **E2E Tests**: Playwright or Cypress for full application testing

**Example test structure:**

.. code-block:: typescript

   // src/components/__tests__/SlideshowCard.test.tsx
   import { render, screen, fireEvent } from '@testing-library/react';
   import SlideshowCard from '../SlideshowCard';
   
   test('renders slideshow name', () => {
     const slideshow = { id: 1, name: 'Test Slideshow' };
     render(<SlideshowCard slideshow={slideshow} />);
     expect(screen.getByText('Test Slideshow')).toBeInTheDocument();
   });

Deployment Considerations
~~~~~~~~~~~~~~~~~~~~~~~~~

**Production Build:**

.. code-block:: bash

   cd frontend
   npm run build

This creates optimized assets in ``kiosk_show_replacement/static/dist/`` that Flask serves in production.

**Environment Variables:**

Create ``.env`` files for different environments:

.. code-block:: bash

   # frontend/.env.development
   VITE_API_BASE_URL=http://localhost:5000
   
   # frontend/.env.production
   VITE_API_BASE_URL=

**Build Optimization:**

* Vite automatically optimizes bundle size
* Tree shaking removes unused code
* Assets are fingerprinted for caching
* Source maps available for debugging

Contributing
------------

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Update documentation
7. Submit a pull request

Code Review Process
~~~~~~~~~~~~~~~~~~~

All contributions go through code review:

1. Automated checks (linting, testing, type checking)
2. Manual review by maintainers
3. Discussion and iteration
4. Approval and merge

Release Process
---------------

1. Update version in ``pyproject.toml``
2. Update ``CHANGELOG.md``
3. Create a Git tag
4. Build and publish to PyPI
5. Create GitHub release
