import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

/**
 * Error severity levels for different types of errors.
 */
export type ErrorSeverity = 'error' | 'warning' | 'info';

/**
 * Error object structure for the error context.
 */
export interface AppError {
  id: string;
  message: string;
  severity: ErrorSeverity;
  timestamp: Date;
  code?: string;
  details?: Record<string, unknown>;
  dismissible?: boolean;
  autoHide?: boolean;
  autoHideDelay?: number;
}

/**
 * Error context type definition.
 */
interface ErrorContextType {
  errors: AppError[];
  addError: (error: Omit<AppError, 'id' | 'timestamp'>) => string;
  removeError: (id: string) => void;
  clearErrors: () => void;
  hasErrors: boolean;
  lastError: AppError | null;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

/**
 * Generate a unique error ID.
 */
const generateErrorId = (): string => {
  return `error-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
};

/**
 * Error provider component that manages global error state.
 */
interface ErrorProviderProps {
  children: ReactNode;
  maxErrors?: number;
}

export const ErrorProvider: React.FC<ErrorProviderProps> = ({
  children,
  maxErrors = 10,
}) => {
  const [errors, setErrors] = useState<AppError[]>([]);

  const removeError = useCallback((id: string): void => {
    setErrors((prev) => prev.filter((error) => error.id !== id));
  }, []);

  const addError = useCallback(
    (error: Omit<AppError, 'id' | 'timestamp'>): string => {
      const id = generateErrorId();
      const newError: AppError = {
        ...error,
        id,
        timestamp: new Date(),
        dismissible: error.dismissible ?? true,
        autoHide: error.autoHide ?? error.severity !== 'error',
        autoHideDelay: error.autoHideDelay ?? 5000,
      };

      setErrors((prev) => {
        // Limit the number of errors stored
        const updatedErrors = [newError, ...prev].slice(0, maxErrors);
        return updatedErrors;
      });

      // Auto-hide if configured
      if (newError.autoHide && newError.autoHideDelay) {
        setTimeout(() => {
          removeError(id);
        }, newError.autoHideDelay);
      }

      return id;
    },
    [maxErrors, removeError]
  );

  const clearErrors = useCallback((): void => {
    setErrors([]);
  }, []);

  const hasErrors = errors.length > 0;
  const lastError = errors.length > 0 ? errors[0] : null;

  return (
    <ErrorContext.Provider
      value={{
        errors,
        addError,
        removeError,
        clearErrors,
        hasErrors,
        lastError,
      }}
    >
      {children}
    </ErrorContext.Provider>
  );
};

/**
 * Hook to access the error context.
 */
export const useErrors = (): ErrorContextType => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error('useErrors must be used within an ErrorProvider');
  }
  return context;
};

/**
 * Convenience hook for adding errors with common patterns.
 */
export const useErrorHandler = () => {
  const { addError } = useErrors();

  const handleApiError = useCallback(
    (message: string, details?: Record<string, unknown>): string => {
      return addError({
        message,
        severity: 'error',
        code: 'API_ERROR',
        details,
        autoHide: false,
      });
    },
    [addError]
  );

  const handleNetworkError = useCallback(
    (message = 'Network error. Please check your connection.'): string => {
      return addError({
        message,
        severity: 'error',
        code: 'NETWORK_ERROR',
        autoHide: false,
      });
    },
    [addError]
  );

  const handleValidationError = useCallback(
    (message: string, details?: Record<string, unknown>): string => {
      return addError({
        message,
        severity: 'warning',
        code: 'VALIDATION_ERROR',
        details,
        autoHide: true,
        autoHideDelay: 8000,
      });
    },
    [addError]
  );

  const handleSuccess = useCallback(
    (message: string): string => {
      return addError({
        message,
        severity: 'info',
        autoHide: true,
        autoHideDelay: 3000,
      });
    },
    [addError]
  );

  const handleWarning = useCallback(
    (message: string): string => {
      return addError({
        message,
        severity: 'warning',
        autoHide: true,
        autoHideDelay: 5000,
      });
    },
    [addError]
  );

  return {
    handleApiError,
    handleNetworkError,
    handleValidationError,
    handleSuccess,
    handleWarning,
  };
};

export default ErrorContext;
