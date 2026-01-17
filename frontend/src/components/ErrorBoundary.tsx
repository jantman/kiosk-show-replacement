import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary component that catches JavaScript errors in child components.
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary fallback={<ErrorFallback />}>
 *   <MyComponent />
 * </ErrorBoundary>
 * ```
 */
class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<State> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo });

    // Log error for debugging
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // Call optional error handler
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default error UI
      return (
        <div className="container py-5">
          <div className="alert alert-danger" role="alert">
            <h4 className="alert-heading">Something went wrong</h4>
            <p>
              An unexpected error occurred. Please try refreshing the page or
              contact support if the problem persists.
            </p>
            <hr />
            <div className="d-flex gap-2">
              <button
                className="btn btn-outline-danger"
                onClick={this.handleRetry}
              >
                Try Again
              </button>
              <button
                className="btn btn-outline-secondary"
                onClick={() => window.location.reload()}
              >
                Refresh Page
              </button>
            </div>
            {this.props.showDetails && this.state.error && (
              <div className="mt-3">
                <details>
                  <summary className="text-muted">Technical Details</summary>
                  <pre className="mt-2 p-3 bg-light rounded text-wrap">
                    <code>
                      {this.state.error.toString()}
                      {this.state.errorInfo?.componentStack}
                    </code>
                  </pre>
                </details>
              </div>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Page-level error boundary with navigation options.
 */
interface PageErrorBoundaryProps {
  children: ReactNode;
  pageName?: string;
}

interface PageErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class PageErrorBoundary extends Component<PageErrorBoundaryProps, PageErrorBoundaryState> {
  public state: PageErrorBoundaryState = {
    hasError: false,
    error: null,
  };

  public static getDerivedStateFromError(error: Error): Partial<PageErrorBoundaryState> {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(`Error in ${this.props.pageName || 'page'}:`, error, errorInfo);
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false, error: null });
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="container py-5">
          <div className="text-center">
            <h2 className="text-danger mb-3">
              {this.props.pageName ? `Error Loading ${this.props.pageName}` : 'Page Error'}
            </h2>
            <p className="text-muted mb-4">
              We encountered an error while loading this page.
              This might be a temporary issue.
            </p>
            <div className="d-flex justify-content-center gap-3">
              <button
                className="btn btn-primary"
                onClick={this.handleRetry}
              >
                Try Again
              </button>
              <button
                className="btn btn-outline-secondary"
                onClick={() => window.history.back()}
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Component-level error boundary for non-critical UI sections.
 */
interface ComponentErrorBoundaryProps {
  children: ReactNode;
  componentName?: string;
  fallbackMessage?: string;
}

interface ComponentErrorBoundaryState {
  hasError: boolean;
}

export class ComponentErrorBoundary extends Component<ComponentErrorBoundaryProps, ComponentErrorBoundaryState> {
  public state: ComponentErrorBoundaryState = {
    hasError: false,
  };

  public static getDerivedStateFromError(): Partial<ComponentErrorBoundaryState> {
    return { hasError: true };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error(`Error in ${this.props.componentName || 'component'}:`, error, errorInfo);
  }

  private handleRetry = (): void => {
    this.setState({ hasError: false });
  };

  public render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="alert alert-warning d-flex align-items-center justify-content-between" role="alert">
          <span>
            {this.props.fallbackMessage || 'This section could not be loaded.'}
          </span>
          <button
            className="btn btn-sm btn-outline-warning"
            onClick={this.handleRetry}
          >
            Retry
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
