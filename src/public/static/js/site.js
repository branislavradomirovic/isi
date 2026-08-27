(() => {
  const toggle = document.querySelector('[data-nav-toggle]');
  const nav = document.querySelector('[data-primary-nav]');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = toggle.getAttribute('aria-expanded') === 'true';
      toggle.setAttribute('aria-expanded', String(!open));
      nav.dataset.open = String(!open);
    });
  }

  const controls = document.querySelector('[data-catalog-controls]');
  const list = document.querySelector('[data-catalog-list]');
  if (!controls || !list) return;

  const input = controls.querySelector('[data-catalog-search]');
  const chips = [...controls.querySelectorAll('[data-catalog-filter]')];
  const items = [...list.querySelectorAll('[data-catalog-item]')];
  const groupContainers = [...list.querySelectorAll('.institution-document-group')];
  const empty = list.querySelector('[data-catalog-empty]');
  let activeFilter = 'all';

  const normalize = (value) => (value || '')
    .toLocaleLowerCase('sr-Latn')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');

  const apply = () => {
    const query = normalize(input ? input.value : '');
    let visibleCount = 0;

    items.forEach((item) => {
      const search = normalize(item.dataset.search || item.textContent || '');
      const itemGroup = item.dataset.catalogGroup || item.closest('[data-catalog-group]')?.dataset.catalogGroup || '';
      const matchesQuery = !query || search.includes(query);
      const matchesFilter = activeFilter === 'all' || itemGroup === activeFilter;
      const visible = matchesQuery && matchesFilter;
      item.hidden = !visible;
      if (visible) visibleCount += 1;
    });

    groupContainers.forEach((group) => {
      const groupVisible = [...group.querySelectorAll('[data-catalog-item]')].some((item) => !item.hidden);
      group.hidden = !groupVisible;
    });

    if (empty) empty.hidden = visibleCount !== 0;
  };

  if (input) input.addEventListener('input', apply);
  chips.forEach((chip) => {
    chip.addEventListener('click', () => {
      activeFilter = chip.dataset.catalogFilter || 'all';
      chips.forEach((candidate) => candidate.classList.toggle('is-active', candidate === chip));
      apply();
    });
  });

  apply();
})();
