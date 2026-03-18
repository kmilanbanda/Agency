document.addEventListener('keydown', (e) => {
  console.log('Key pressed anywhere:', e.key, 'Target:', e.target.tagName);

  if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

  const entries = document.querySelectorAll('.entry-item'); 
  if (entries.length === 0) return;

  let current = document.activeElement.closest('.entry-item') || entries[0];
  let index = Array.from(entries).indexOf(current);

  switch (e.key.toLowerCase()) {
  case 'j': // next entry
  case 'arrowdown':
    e.preventDefault();
    index = Math.min(index + 1, entries.length - 1);
    entries[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
    entries[index].focus();
    break;

  case 'k': // previous entry
  case 'arrowup':
    e.preventDefault();
    index = Math.max(index - 1, 0);
    entries[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
    entries[index].focus();
    break;

  case 'h': // home
    if (e.key === 'g' && e.repeat) return;
    window.location.href = window.HOME_URL;
    break;

  case 's': // focus search
    e.preventDefault();
    document.querySelector('input[name="q"]')?.focus();
    break;

  case 'r': // refresh 
    e.preventDefault();
    location.reload();
    break;
  }
});
