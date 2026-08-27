(() => {
  document.querySelectorAll('[data-catalog-controls]').forEach((controls) => {
    const section = controls.closest('section') || document;
    const list = section.nextElementSibling?.querySelector?.('[data-catalog-list]') || document.querySelector('[data-catalog-list]');
    if (!list) return;
    const input = controls.querySelector('[data-catalog-search]');
    const chips = [...controls.querySelectorAll('[data-catalog-filter]')];
    const items = [...list.querySelectorAll('[data-catalog-item]')];
    const groups = [...list.querySelectorAll('[data-catalog-group]')].filter((node) => !node.matches('[data-catalog-item]'));
    const empty = list.querySelector('[data-catalog-empty]');
    let active = 'all';
    const norm = (v) => (v || '').toLocaleLowerCase('sr-Latn').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const apply = () => {
      const query = norm(input?.value);
      let visible = 0;
      items.forEach((item) => {
        const haystack = norm(item.dataset.search || item.textContent);
        const group = item.dataset.catalogGroup || item.closest('[data-catalog-group]')?.dataset.catalogGroup || '';
        const show = (!query || haystack.includes(query)) && (active === 'all' || group === active);
        item.hidden = !show;
        if (show) visible += 1;
      });
      groups.forEach((group) => {
        group.hidden = ![...group.querySelectorAll('[data-catalog-item]')].some((item) => !item.hidden);
      });
      if (empty) empty.hidden = visible !== 0;
    };
    input?.addEventListener('input', apply);
    chips.forEach((chip) => chip.addEventListener('click', () => {
      active = chip.dataset.catalogFilter || 'all';
      chips.forEach((candidate) => candidate.classList.toggle('is-active', candidate === chip));
      apply();
    }));
    apply();
  });
})();
