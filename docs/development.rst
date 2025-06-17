Development
===========

Setting up tAvailable Commands
~~~~~~~~~~~~~~~~~~

**Important**: First activate your Poetry environment in any new terminal session:

.. code-block:: bash

   eval $(poetry env activate)

Then run the development commands:ment Environment
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

**Important**: First activate your Poetry environment in any new shell:

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

Located in ``tests/integration/``, these test the interaction between components and complete user workflows using Flask's test client.

**What Integration Tests Cover:**

* **Component Integration**: How different parts of your system work together (API + Database, Routes + Templates, Display + Models)
* **Complete User Workflows**: Full user journeys from start to finish, simulating real user interactions
* **Cross-system Validation**: Changes verified across multiple interfaces (Web UI + API + Database)
* **Business Logic**: End-to-end business workflows and user experience flows

**Key Characteristics:**

* Use Flask's test client to simulate HTTP requests
* Test multiple components working together in realistic scenarios
* Verify both technical correctness and user experience
* Include multi-step workflows (create → edit → view → delete)
* Test different content types and user scenarios

**Examples:**

* Complete slideshow creation workflow (homepage → create → add slides → preview → verify)
* User management workflows (registration → login → content management)
* Display management (registration → assignment → playback → monitoring)
* API integration with database persistence and template rendering

.. code-block:: bash

   nox -s test-integration

End-to-End Tests (Future)
~~~~~~~~~~~~~~~~~~~~~~~~~

End-to-end tests will use Flask's live test server with real HTTP requests and browser automation.

**Planned E2E Test Features:**

* **Live Server Testing**: Tests run against a real Flask server instance
* **Browser Automation**: Use Selenium, Playwright, or Cypress for actual browser testing
* **Real User Interactions**: Click buttons, fill forms, navigate pages like a real user
* **Cross-browser Testing**: Verify functionality across different browsers
* **Performance Testing**: Real-world performance and load testing
* **Visual Regression**: Screenshot comparisons for UI consistency

**When E2E Tests Will Be Added:**

* After core functionality is stable
* When browser-specific features need testing
* For complex JavaScript interactions
* To verify complete system behavior under real conditions

.. code-block:: bash

   # Future command - not yet implemented
   nox -s test-e2e

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
