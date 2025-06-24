// Playwright configuration for debugging integration tests
module.exports = {
  // Use debug mode
  use: {
    // Global test settings
    headless: true,   // Run in headless mode (safer for CI/servers)
    slowMo: 50,       // Reduced slow down for faster tests
    video: 'retain-on-failure',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
    
    // Browser settings
    launchOptions: {
      args: [
        '--disable-dev-shm-usage',
        '--disable-extensions',
        '--disable-gpu',
        '--disable-background-timer-throttling',
        '--disable-backgrounding-occluded-windows',
        '--disable-renderer-backgrounding',
        '--no-sandbox',
        '--disable-web-security',
        '--disable-features=VizDisplayCompositor',
        '--disable-setuid-sandbox',
        '--disable-software-rasterizer',
        '--run-all-compositor-stages-before-draw',
        '--disable-background-media-suspend',
        '--disable-domain-reliability',
        '--disable-features=AudioServiceOutOfProcess',
        '--disable-ipc-flooding-protection'
      ]
    }
  },
  
  // Timeout settings
  timeout: 30000,
  expect: {
    timeout: 10000
  },
  
  // Global setup/teardown
  globalSetup: null,
  globalTeardown: null,
  
  // Test settings
  testDir: './tests/integration',
  workers: 1,  // Run tests serially for debugging
  retries: 0,  // No retries during debugging
  
  // Reporting
  reporter: [
    ['list'],
    ['html', { 
      outputFolder: 'playwright-report',
      open: 'never'  // Don't auto-open browser for reports
    }],
    ['json', { 
      outputFile: 'test-results/results.json' 
    }]
  ],
  
  // Browser projects
  projects: [
    {
      name: 'chromium',
      use: { 
        ...require('@playwright/test').devices['Desktop Chrome'],
        channel: 'chrome'  // Use system Chrome if available
      },
    },
  ],
  
  // Output directory
  outputDir: 'test-results/',
  
  // Full path configuration
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  
  // Web server (not used - we start our own servers)
  webServer: null
};
