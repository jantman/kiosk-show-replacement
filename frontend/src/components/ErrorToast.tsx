import React from 'react';
import { useErrors, AppError } from '../contexts/ErrorContext';

/**
 * Get Bootstrap alert class based on error severity.
 */
const getAlertClass = (severity: AppError['severity']): string => {
  switch (severity) {
    case 'error':
      return 'alert-danger';
    case 'warning':
      return 'alert-warning';
    case 'info':
      return 'alert-success';
    default:
      return 'alert-secondary';
  }
};

/**
 * Get icon based on error severity.
 */
const getIcon = (severity: AppError['severity']): string => {
  switch (severity) {
    case 'error':
      return 'bi-exclamation-triangle-fill';
    case 'warning':
      return 'bi-exclamation-circle-fill';
    case 'info':
      return 'bi-check-circle-fill';
    default:
      return 'bi-info-circle-fill';
  }
};

/**
 * Single error toast item.
 */
interface ErrorToastItemProps {
  error: AppError;
  onDismiss: (id: string) => void;
}

const ErrorToastItem: React.FC<ErrorToastItemProps> = ({ error, onDismiss }) => {
  return (
    <div
      className={`alert ${getAlertClass(error.severity)} alert-dismissible fade show d-flex align-items-start`}
      role="alert"
    >
      <i className={`bi ${getIcon(error.severity)} me-2 flex-shrink-0`}></i>
      <div className="flex-grow-1">
        <div>{error.message}</div>
        {error.code && (
          <small className="text-muted">Code: {error.code}</small>
        )}
      </div>
      {error.dismissible && (
        <button
          type="button"
          className="btn-close"
          aria-label="Close"
          onClick={() => onDismiss(error.id)}
        />
      )}
    </div>
  );
};

/**
 * Container for error toasts.
 * Displays errors from the ErrorContext as toast notifications.
 */
interface ErrorToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center';
  maxVisible?: number;
}

export const ErrorToastContainer: React.FC<ErrorToastContainerProps> = ({
  position = 'top-right',
  maxVisible = 5,
}) => {
  const { errors, removeError } = useErrors();

  // Get position styles
  const getPositionStyles = (): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'fixed',
      zIndex: 9999,
      maxWidth: '400px',
      width: '100%',
    };

    switch (position) {
      case 'top-right':
        return { ...base, top: '1rem', right: '1rem' };
      case 'top-left':
        return { ...base, top: '1rem', left: '1rem' };
      case 'bottom-right':
        return { ...base, bottom: '1rem', right: '1rem' };
      case 'bottom-left':
        return { ...base, bottom: '1rem', left: '1rem' };
      case 'top-center':
        return { ...base, top: '1rem', left: '50%', transform: 'translateX(-50%)' };
      default:
        return { ...base, top: '1rem', right: '1rem' };
    }
  };

  // Limit visible errors
  const visibleErrors = errors.slice(0, maxVisible);

  if (visibleErrors.length === 0) {
    return null;
  }

  return (
    <div style={getPositionStyles()}>
      {visibleErrors.map((error) => (
        <ErrorToastItem
          key={error.id}
          error={error}
          onDismiss={removeError}
        />
      ))}
      {errors.length > maxVisible && (
        <div className="text-muted text-center small">
          +{errors.length - maxVisible} more notifications
        </div>
      )}
    </div>
  );
};

/**
 * Inline error display for forms and specific sections.
 */
interface InlineErrorProps {
  message: string;
  onDismiss?: () => void;
  className?: string;
}

export const InlineError: React.FC<InlineErrorProps> = ({
  message,
  onDismiss,
  className = '',
}) => {
  return (
    <div className={`alert alert-danger d-flex align-items-center ${className}`} role="alert">
      <i className="bi bi-exclamation-triangle-fill me-2"></i>
      <div className="flex-grow-1">{message}</div>
      {onDismiss && (
        <button
          type="button"
          className="btn-close"
          aria-label="Close"
          onClick={onDismiss}
        />
      )}
    </div>
  );
};

/**
 * Loading error state component for data fetching errors.
 */
interface LoadingErrorProps {
  message?: string;
  onRetry?: () => void;
}

export const LoadingError: React.FC<LoadingErrorProps> = ({
  message = 'Failed to load data',
  onRetry,
}) => {
  return (
    <div className="text-center py-4">
      <div className="text-danger mb-3">
        <i className="bi bi-exclamation-circle fs-1"></i>
      </div>
      <p className="text-muted mb-3">{message}</p>
      {onRetry && (
        <button className="btn btn-outline-primary" onClick={onRetry}>
          <i className="bi bi-arrow-clockwise me-2"></i>
          Try Again
        </button>
      )}
    </div>
  );
};

/**
 * Empty state component when no data is available.
 */
interface EmptyStateProps {
  message?: string;
  icon?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  message = 'No data available',
  icon = 'bi-inbox',
  action,
}) => {
  return (
    <div className="text-center py-5">
      <div className="text-muted mb-3">
        <i className={`bi ${icon} fs-1`}></i>
      </div>
      <p className="text-muted mb-3">{message}</p>
      {action && (
        <button className="btn btn-primary" onClick={action.onClick}>
          {action.label}
        </button>
      )}
    </div>
  );
};

export default ErrorToastContainer;
