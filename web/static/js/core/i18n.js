/* core/i18n.js — UI-chrome translation only (EN/ES/RU).
   Job copy itself is shown exactly as the source returns it — never machine-faked. */

const I18N = {
  en: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Checking backend…',
    'state.init': 'Initializing…',
    'nav.home': 'Home', 'nav.jobs': 'Jobs', 'nav.discovery': 'Discovery',
    'nav.providers': 'Providers', 'nav.budget': 'Budget',
    'nav.history': 'History', 'nav.opportunities': 'Opportunities',
    'nav.applications': 'Applications', 'nav.debug': 'Debug', 'nav.why-three': 'Why Three',
    'nav.diagnostics': 'System',
    'jobs.reload': 'Browse saved jobs (free)', 'jobs.run': 'Run fresh discovery',
    'jobs.confirm': 'Run fresh discovery? This calls live provider APIs.',
    'common.unavailable': 'unavailable', 'common.apply': 'Open / Apply',
    'common.evidence': 'Show evidence', 'common.evidence_hide': 'Hide evidence',
    'common.track': 'Track this job',
    'landing.tag': 'Local opportunity intelligence — discover, resolve, and track jobs near you.',
    'landing.enter': 'Enter',
    'landing.safe': 'Discover local jobs. Powered by AI. Free to use.',
    'home.tag': 'Your local opportunity cockpit.',
    'filters.title': 'Filters',
    'disc.safe_title': 'Ready.', 'disc.idle': 'Idle — no providers active.',
    'disc.safe': 'Browsing saved batches is always free.',
  },
  es: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Comprobando el servidor…',
    'state.init': 'Inicializando…',
    'nav.home': 'Inicio', 'nav.jobs': 'Empleos', 'nav.discovery': 'Búsqueda',
    'nav.providers': 'Proveedores', 'nav.budget': 'Recursos',
    'nav.history': 'Historial', 'nav.opportunities': 'Oportunidades',
    'nav.applications': 'Solicitudes', 'nav.debug': 'Depuración', 'nav.why-three': 'Por qué tres',
    'nav.diagnostics': 'Sistema',
    'landing.enter': 'Entrar', 'landing.tag': 'Inteligencia local de oportunidades cerca de ti.',
    'landing.safe': 'Descubre empleos locales. Con inteligencia artificial.',
    'filters.title': 'Filtros',
    'jobs.reload': 'Ver empleos guardados (gratis)', 'jobs.run': 'Búsqueda en vivo',
    'jobs.confirm': '¿Iniciar búsqueda en vivo? Esto llama a las APIs de proveedores.',
    'common.unavailable': 'no disponible', 'common.apply': 'Abrir / Solicitar',
    'common.evidence': 'Ver evidencia', 'common.evidence_hide': 'Ocultar evidencia',
    'common.track': 'Seguir este empleo',
    'home.tag': 'Tu cockpit de oportunidades locales.',
    'disc.safe_title': 'Listo.', 'disc.idle': 'Inactivo.',
    'disc.safe': 'Ver lotes guardados es siempre gratis.',
  },
  ru: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Проверка сервера…',
    'state.init': 'Инициализация…',
    'nav.home': 'Главная', 'nav.jobs': 'Вакансии', 'nav.discovery': 'Поиск',
    'nav.providers': 'Источники', 'nav.budget': 'Ресурсы',
    'nav.history': 'История', 'nav.opportunities': 'Возможности',
    'nav.applications': 'Заявки', 'nav.debug': 'Отладка', 'nav.why-three': 'Почему три',
    'nav.diagnostics': 'Система',
    'landing.enter': 'Войти', 'landing.tag': 'Локальная аналитика вакансий рядом с вами.',
    'landing.safe': 'Находи вакансии рядом. С поддержкой ИИ.',
    'filters.title': 'Фильтры',
    'jobs.reload': 'Сохранённые вакансии (бесплатно)', 'jobs.run': 'Живой поиск',
    'jobs.confirm': 'Запустить живой поиск? Это обращается к API провайдеров.',
    'common.unavailable': 'недоступно', 'common.apply': 'Открыть / Откликнуться',
    'common.evidence': 'Показать данные', 'common.evidence_hide': 'Скрыть данные',
    'common.track': 'Отслеживать вакансию',
    'home.tag': 'Ваш локальный кокпит возможностей.',
    'disc.safe_title': 'Готов.', 'disc.idle': 'Простой.',
    'disc.safe': 'Просмотр сохранённых пакетов всегда бесплатен.',
  },
};

function t(key) {
  const lang = (AppState && AppState.lang) || 'en';
  return (I18N[lang] && I18N[lang][key]) || I18N.en[key] || key;
}

// Replace text of any [data-i18n] node with the active language
function applyI18n(root) {
  (root || document).querySelectorAll('[data-i18n]').forEach(function (el) {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
}

function setLang(lang) {
  if (!I18N[lang]) return;
  AppState.lang = lang;
  document.documentElement.lang = lang;
  applyI18n(document);
  if (typeof buildNav === 'function') buildNav();
  const cur = Views[AppState.activeView];
  if (cur) navigate(cur.id);  // re-render active view with new chrome
}
