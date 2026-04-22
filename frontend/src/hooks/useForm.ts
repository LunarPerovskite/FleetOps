import { useState, useCallback } from 'react';
import { toast } from './useToast';

interface ValidationRule {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  email?: boolean;
  pattern?: RegExp;
  custom?: (value: any) => string | null;
}

type ValidationSchema = Record<string, ValidationRule>;

interface FormState<T> {
  values: T;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}

export function useForm<T extends Record<string, any>>(
  initialValues: T,
  validationSchema: ValidationSchema,
  onSubmit: (values: T) => Promise<void>
) {
  const [state, setState] = useState<FormState<T>>({
    values: initialValues,
    errors: {},
    touched: {},
    isSubmitting: false,
    isValid: false,
  });

  const validateField = useCallback((name: string, value: any): string => {
    const rule = validationSchema[name];
    if (!rule) return '';

    if (rule.required && (!value || (typeof value === 'string' && value.trim() === ''))) {
      return 'This field is required';
    }

    if (rule.minLength && typeof value === 'string' && value.length < rule.minLength) {
      return `Minimum ${rule.minLength} characters`;
    }

    if (rule.maxLength && typeof value === 'string' && value.length > rule.maxLength) {
      return `Maximum ${rule.maxLength} characters`;
    }

    if (rule.email && typeof value === 'string' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
      return 'Invalid email address';
    }

    if (rule.pattern && typeof value === 'string' && !rule.pattern.test(value)) {
      return 'Invalid format';
    }

    if (rule.custom) {
      const customError = rule.custom(value);
      if (customError) return customError;
    }

    return '';
  }, [validationSchema]);

  const validateAll = useCallback((): Record<string, string> => {
    const errors: Record<string, string> = {};
    Object.keys(validationSchema).forEach((key) => {
      const error = validateField(key, state.values[key]);
      if (error) errors[key] = error;
    });
    return errors;
  }, [state.values, validationSchema, validateField]);

  const handleChange = useCallback((name: string, value: any) => {
    setState((prev) => {
      const newValues = { ...prev.values, [name]: value };
      const error = validateField(name, value);
      const newErrors = { ...prev.errors, [name]: error };
      if (!error) delete newErrors[name];

      const allErrors = Object.keys(validationSchema).reduce((acc, key) => {
        const err = key === name ? error : validateField(key, newValues[key]);
        if (err) acc[key] = err;
        return acc;
      }, {} as Record<string, string>);

      return {
        ...prev,
        values: newValues,
        errors: newErrors,
        touched: { ...prev.touched, [name]: true },
        isValid: Object.keys(allErrors).length === 0,
      };
    });
  }, [validateField, validationSchema]);

  const handleBlur = useCallback((name: string) => {
    setState((prev) => ({
      ...prev,
      touched: { ...prev.touched, [name]: true },
    }));
  }, []);

  const handleSubmit = useCallback(async (e?: React.FormEvent) => {
    if (e) e.preventDefault();

    const errors = validateAll();
    
    if (Object.keys(errors).length > 0) {
      setState((prev) => ({
        ...prev,
        errors,
        touched: Object.keys(validationSchema).reduce((acc, key) => {
          acc[key] = true;
          return acc;
        }, {} as Record<string, boolean>),
        isValid: false,
      }));
      toast.error('Please fix the errors before submitting');
      return;
    }

    setState((prev) => ({ ...prev, isSubmitting: true }));

    try {
      await onSubmit(state.values);
      toast.success('Submitted successfully');
      // Reset form
      setState((prev) => ({
        ...prev,
        values: initialValues,
        errors: {},
        touched: {},
        isSubmitting: false,
        isValid: false,
      }));
    } catch (err: any) {
      setState((prev) => ({ ...prev, isSubmitting: false }));
      toast.error(err.message || 'Submission failed');
    }
  }, [state.values, validateAll, onSubmit, initialValues, validationSchema]);

  const getFieldProps = useCallback((name: string) => ({
    value: state.values[name] || '',
    onChange: (e: any) => handleChange(name, e.target?.value ?? e),
    onBlur: () => handleBlur(name),
    error: state.touched[name] ? state.errors[name] : undefined,
  }), [state, handleChange, handleBlur]);

  return {
    ...state,
    handleChange,
    handleBlur,
    handleSubmit,
    getFieldProps,
  };
}
