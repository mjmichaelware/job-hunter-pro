/* core/i18n.js — UI-chrome translation only (EN/ES/RU).
   Job copy itself is shown exactly as the source returns it — never machine-faked. */

const I18N = {
  en: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Checking backend…',
    'state.init': 'Initializing…',
    'nav.jobs': 'Jobs', 'nav.providers': 'Providers', 'nav.budget': 'Budget',
    'nav.history': 'History', 'nav.opportunities': 'Opportunities',
    'nav.applications': 'Applications', 'nav.debug': 'Debug', 'nav.why-three': 'Why Three',
    'jobs.reload': 'Reload saved (free)', 'jobs.run': 'Run fresh discovery (spends quota)',
    'jobs.confirm': 'Run fresh discovery? This may spend SerpAPI / provider quota.',
    'common.unavailable': 'unavailable', 'common.apply': 'Open / Apply',
    'common.evidence': 'Show evidence', 'common.evidence_hide': 'Hide evidence',
    'common.track': 'Track this job',
  },
  es: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Comprobando el servidor…',
    'state.init': 'Inicializando…',
    'nav.jobs': 'Empleos', 'nav.providers': 'Proveedores', 'nav.budget': 'Presupuesto',
    'nav.history': 'Historial', 'nav.opportunities': 'Oportunidades',
    'nav.applications': 'Solicitudes', 'nav.debug': 'Diagnóstico', 'nav.why-three': 'Por qué tres',
    'jobs.reload': 'Recargar guardados (gratis)', 'jobs.run': 'Buscar en vivo (consume cuota)',
    'jobs.confirm': '¿Buscar en vivo? Esto puede consumir cuota de SerpAPI / proveedor.',
    'common.unavailable': 'no disponible', 'common.apply': 'Abrir / Solicitar',
    'common.evidence': 'Ver evidencia', 'common.evidence_hide': 'Ocultar evidencia',
    'common.track': 'Seguir este empleo',
  },
  ru: {
    'app.title': 'Job Hunter Pro',
    'health.checking': 'Проверка сервера…',
    'state.init': 'Инициализация…',
    'nav.jobs': 'Вакансии', 'nav.providers': 'Источники', 'nav.budget': 'Бюджет',
    'nav.history': 'История', 'nav.opportunities': 'Возможности',
    'nav.applications': 'Заявки', 'nav.debug': 'Отладка', 'nav.why-three': 'Почему три',
    'jobs.reload': 'Обновить сохранённые (бесплатно)', 'jobs.run': 'Живой поиск (расход квоты)',
    'jobs.confirm': 'Запустить живой поиск? Это может израсходовать квоту SerpAPI / источника.',
    'common.unavailable': 'недоступно', 'common.apply': 'Открыть / Откликнуться',
    'common.evidence': 'Показать данные', 'common.evidence_hide': 'Скрыть данные',
    'common.track': 'Отслеживать вакансию',
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
