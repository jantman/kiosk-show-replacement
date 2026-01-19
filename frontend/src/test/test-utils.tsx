import React, { ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { SSEProvider } from '../hooks/useSSE';

interface TestProvidersProps {
  children: ReactNode;
}

// eslint-disable-next-line react-refresh/only-export-components
const TestProviders: React.FC<TestProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <SSEProvider>
        {children}
      </SSEProvider>
    </BrowserRouter>
  );
};

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  wrapper?: React.ComponentType<{ children: ReactNode }>;
}

const customRender = (ui: React.ReactElement, options?: CustomRenderOptions) => {
  return render(ui, { wrapper: TestProviders, ...options });
};

// Re-export everything
// eslint-disable-next-line react-refresh/only-export-components
export * from '@testing-library/react';

// Override render method
export { customRender as render };

// Export helper for components that need just router
export const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

// Export helper for components that need all providers
export const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <TestProviders>
      {component}
    </TestProviders>
  );
};
