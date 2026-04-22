import { useState, useCallback } from 'react';

type Locale = 'en' | 'es';

const translations: Record<Locale, Record<string, string>> = {
  en: {
    'dashboard.title': 'Fleet Overview',
    'tasks.title': 'Tasks',
    'agents.title': 'Agents',
    'approvals.title': 'Approvals',
    'events.title': 'Events',
    'settings.title': 'Settings',
    'providers.title': 'Provider Configuration',
    'onboarding.title': 'Welcome to FleetOps',
    'login.title': 'Sign In',
    'create.task': 'Create Task',
    'create.agent': 'Create Agent',
    'search.placeholder': 'Search...',
    'save.changes': 'Save Changes',
    'cancel': 'Cancel',
    'delete': 'Delete',
    'edit': 'Edit',
    'active': 'Active',
    'inactive': 'Inactive',
    'pending': 'Pending',
    'completed': 'Completed',
    'failed': 'Failed',
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
    'critical': 'Critical',
    'welcome': 'Welcome',
    'logout': 'Log Out',
    'notifications': 'Notifications',
    'language': 'Language',
    'dark_mode': 'Dark Mode',
    'loading': 'Loading...',
    'error.retry': 'Try Again',
    'no.data': 'No data available',
  },
  es: {
    'dashboard.title': 'Vista General',
    'tasks.title': 'Tareas',
    'agents.title': 'Agentes',
    'approvals.title': 'Aprobaciones',
    'events.title': 'Eventos',
    'settings.title': 'Configuración',
    'providers.title': 'Configuración de Proveedores',
    'onboarding.title': 'Bienvenido a FleetOps',
    'login.title': 'Iniciar Sesión',
    'create.task': 'Crear Tarea',
    'create.agent': 'Crear Agente',
    'search.placeholder': 'Buscar...',
    'save.changes': 'Guardar Cambios',
    'cancel': 'Cancelar',
    'delete': 'Eliminar',
    'edit': 'Editar',
    'active': 'Activo',
    'inactive': 'Inactivo',
    'pending': 'Pendiente',
    'completed': 'Completado',
    'failed': 'Fallido',
    'low': 'Bajo',
    'medium': 'Medio',
    'high': 'Alto',
    'critical': 'Crítico',
    'welcome': 'Bienvenido',
    'logout': 'Cerrar Sesión',
    'notifications': 'Notificaciones',
    'language': 'Idioma',
    'dark_mode': 'Modo Oscuro',
    'loading': 'Cargando...',
    'error.retry': 'Intentar de Nuevo',
    'no.data': 'No hay datos disponibles',
  },
};

function getStoredLocale(): Locale {
  const stored = localStorage.getItem('fleetops_language');
  if (stored === 'es') return 'es';
  return 'en';
}

export function useI18n() {
  const [locale, setLocaleState] = useState<Locale>(getStoredLocale());

  const setLocale = useCallback((newLocale: Locale) => {
    setLocaleState(newLocale);
    localStorage.setItem('fleetops_language', newLocale);
  }, []);

  const t = useCallback(
    (key: string, fallback?: string): string => {
      const translation = translations[locale]?.[key];
      if (translation) return translation;
      if (fallback) return fallback;
      return key;
    },
    [locale]
  );

  return { locale, setLocale, t };
}
