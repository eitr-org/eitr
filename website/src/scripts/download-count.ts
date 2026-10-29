import { message } from './messages';
async function showDownloadCount() {
  const label = document.querySelector<HTMLElement>('[data-download-count]');
  if (!label) return;
  try {
    const response = await fetch('https://download.eitr.info/stats.json', {
      credentials: 'omit',
      referrerPolicy: 'no-referrer',
    });
    if (!response.ok) return;
    const { total } = await response.json();
    if (!Number.isSafeInteger(total) || total <= 0) return;
    label.textContent = message('downloaded', {count: total.toLocaleString(document.documentElement.lang)});
    label.hidden = false;
  } catch {
    // The download link remains available when statistics are unavailable.
  }
}

if (document.readyState === 'complete') void showDownloadCount();
else window.addEventListener('load', () => { void showDownloadCount(); }, { once: true });
