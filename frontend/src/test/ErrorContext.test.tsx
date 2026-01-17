import { render, screen, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ErrorProvider, useErrors, useErrorHandler } from '../contexts/ErrorContext';

// Test component that uses the error context
const TestConsumer: React.FC = () => {
  const { errors, addError, removeError, clearErrors, hasErrors, lastError } = useErrors();

  return (
    <div>
      <div data-testid="error-count">{errors.length}</div>
      <div data-testid="has-errors">{hasErrors.toString()}</div>
      <div data-testid="last-error">{lastError?.message || 'none'}</div>
      <button
        data-testid="add-error"
        onClick={() => addError({ message: 'Test error', severity: 'error' })}
      >
        Add Error
      </button>
      <button
        data-testid="add-warning"
        onClick={() => addError({ message: 'Test warning', severity: 'warning', autoHide: false })}
      >
        Add Warning
      </button>
      <button data-testid="clear-errors" onClick={clearErrors}>
        Clear Errors
      </button>
      {errors.map((error) => (
        <div key={error.id} data-testid={`error-${error.id}`}>
          <span>{error.message}</span>
          <button onClick={() => removeError(error.id)}>Remove</button>
        </div>
      ))}
    </div>
  );
};

// Test component that uses error handler hook
const TestErrorHandler: React.FC = () => {
  const { handleApiError, handleNetworkError, handleValidationError, handleSuccess, handleWarning } =
    useErrorHandler();
  const { errors } = useErrors();

  return (
    <div>
      <div data-testid="error-count">{errors.length}</div>
      <button data-testid="api-error" onClick={() => handleApiError('API failed')}>
        API Error
      </button>
      <button data-testid="network-error" onClick={() => handleNetworkError()}>
        Network Error
      </button>
      <button
        data-testid="validation-error"
        onClick={() => handleValidationError('Invalid input')}
      >
        Validation Error
      </button>
      <button data-testid="success" onClick={() => handleSuccess('Operation successful')}>
        Success
      </button>
      <button data-testid="warning" onClick={() => handleWarning('Warning message')}>
        Warning
      </button>
      {errors.map((error) => (
        <div key={error.id} data-testid={`error-${error.severity}`}>
          {error.message}
        </div>
      ))}
    </div>
  );
};

describe('ErrorProvider', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('provides error context to children', () => {
    render(
      <ErrorProvider>
        <TestConsumer />
      </ErrorProvider>
    );

    expect(screen.getByTestId('error-count')).toHaveTextContent('0');
    expect(screen.getByTestId('has-errors')).toHaveTextContent('false');
  });

  it('adds errors correctly', () => {
    render(
      <ErrorProvider>
        <TestConsumer />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('add-error').click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('1');
    expect(screen.getByTestId('has-errors')).toHaveTextContent('true');
    expect(screen.getByTestId('last-error')).toHaveTextContent('Test error');
  });

  it('removes errors correctly', async () => {
    render(
      <ErrorProvider>
        <TestConsumer />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('add-warning').click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('1');

    // Find and click the remove button
    const removeButton = screen.getByText('Remove');
    act(() => {
      removeButton.click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('0');
  });

  it('clears all errors', () => {
    render(
      <ErrorProvider>
        <TestConsumer />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('add-error').click();
      screen.getByTestId('add-warning').click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('2');

    act(() => {
      screen.getByTestId('clear-errors').click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('0');
  });

  it('respects maxErrors limit', () => {
    render(
      <ErrorProvider maxErrors={2}>
        <TestConsumer />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('add-error').click();
      screen.getByTestId('add-error').click();
      screen.getByTestId('add-error').click();
    });

    // Should only have 2 errors due to maxErrors limit
    expect(screen.getByTestId('error-count')).toHaveTextContent('2');
  });

  it('auto-hides errors with autoHide enabled', async () => {
    render(
      <ErrorProvider>
        <TestConsumer />
      </ErrorProvider>
    );

    // Add a warning (auto-hide enabled by default for non-errors)
    act(() => {
      screen.getByTestId('add-error').click();
    });

    expect(screen.getByTestId('error-count')).toHaveTextContent('1');

    // Fast-forward past the auto-hide delay
    act(() => {
      vi.advanceTimersByTime(6000);
    });

    // Error should not auto-hide (severity: 'error' defaults to autoHide: false)
    expect(screen.getByTestId('error-count')).toHaveTextContent('1');
  });
});

describe('useErrorHandler', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('throws error when used outside ErrorProvider', () => {
    // Suppress console.error for this test
    const originalError = console.error;
    console.error = vi.fn();

    expect(() => {
      render(<TestErrorHandler />);
    }).toThrow('useErrors must be used within an ErrorProvider');

    console.error = originalError;
  });

  it('handles API errors', () => {
    render(
      <ErrorProvider>
        <TestErrorHandler />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('api-error').click();
    });

    expect(screen.getByTestId('error-error')).toHaveTextContent('API failed');
  });

  it('handles network errors with default message', () => {
    render(
      <ErrorProvider>
        <TestErrorHandler />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('network-error').click();
    });

    expect(screen.getByTestId('error-error')).toHaveTextContent(
      'Network error. Please check your connection.'
    );
  });

  it('handles validation errors', () => {
    render(
      <ErrorProvider>
        <TestErrorHandler />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('validation-error').click();
    });

    expect(screen.getByTestId('error-warning')).toHaveTextContent('Invalid input');
  });

  it('handles success messages', () => {
    render(
      <ErrorProvider>
        <TestErrorHandler />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('success').click();
    });

    expect(screen.getByTestId('error-info')).toHaveTextContent('Operation successful');
  });

  it('handles warning messages', () => {
    render(
      <ErrorProvider>
        <TestErrorHandler />
      </ErrorProvider>
    );

    act(() => {
      screen.getByTestId('warning').click();
    });

    expect(screen.getByTestId('error-warning')).toHaveTextContent('Warning message');
  });
});
