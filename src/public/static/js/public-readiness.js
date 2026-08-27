(() => {
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-primary-nav]');

  if (toggle && nav) {
    const closeNav = ({ restoreFocus = false } = {}) => {
      toggle.setAttribute('aria-expanded', 'false');
      nav.dataset.open = 'false';
      toggle.setAttribute('aria-label', document.documentElement.lang === 'en' ? 'Open navigation' : 'Otvori navigaciju');
      if (restoreFocus) toggle.focus();
    };

    const syncLabel = () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      const english = document.documentElement.lang === 'en';
      toggle.setAttribute('aria-label', open
        ? (english ? 'Close navigation' : 'Zatvori navigaciju')
        : (english ? 'Open navigation' : 'Otvori navigaciju'));
    };

    toggle.addEventListener('click', () => window.requestAnimationFrame(syncLabel));

    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') {
        closeNav({ restoreFocus: true });
      }
    });

    nav.addEventListener('click', (event) => {
      if (event.target.closest('a') && window.matchMedia('(max-width: 980px)').matches) {
        closeNav();
      }
    });

    window.matchMedia('(min-width: 981px)').addEventListener?.('change', (event) => {
      if (event.matches) closeNav();
    });
  }

  document.querySelectorAll('a[target="_blank"]').forEach((link) => {
    const rel = new Set((link.getAttribute('rel') || '').split(/\s+/).filter(Boolean));
    rel.add('noopener');
    rel.add('noreferrer');
    link.setAttribute('rel', [...rel].join(' '));
  });
})();
