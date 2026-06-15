/** Display helpers. All tolerate null/undefined and return a hyphen placeholder. */

export function formatDateTime(iso?: string | null): string {
  if (!iso) return '-';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function formatDate(iso?: string | null): string {
  if (!iso) return '-';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: '2-digit' });
}

export function relativeTime(iso?: string | null): string {
  if (!iso) return '-';
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return iso;
  const diff = t - Date.now();
  const mins = Math.round(Math.abs(diff) / 60000);
  const rtf = new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' });
  const sign = Math.sign(diff) || -1;
  if (mins < 60) return rtf.format(sign * mins, 'minute');
  const hours = Math.round(mins / 60);
  if (hours < 24) return rtf.format(sign * hours, 'hour');
  return rtf.format(sign * Math.round(hours / 24), 'day');
}

export function formatNumber(n?: number | null, digits = 1): string {
  if (n === null || n === undefined || Number.isNaN(n)) return '-';
  return n.toLocaleString(undefined, { maximumFractionDigits: digits });
}

/** "acute_alarm" -> "Acute Alarm". */
export function titleCase(s?: string | null): string {
  if (!s) return '-';
  return s.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

/**
 * Put a single space between a value and its unit ("2.6mm/s" -> "2.6 mm/s"), around the
 * "≈" operator, and between a value and a duration word ("next≈2weeks" -> "next ≈ 2 weeks").
 * Bolded values in the LLM prose otherwise render glued; non-bold baselines are already
 * spaced. Scoped to the markdown render path only.
 */
export function spaceUnits(text: string): string {
  return text
    .replace(/(\d)\s*(mm\/s|mm s⁻¹|dB|ppm|°C|kW|Hz)\b/g, '$1 $2')
    .replace(/\s*≈\s*/g, ' ≈ ')
    .replace(/(\d)\s*(weeks?|days?|hours?)\b/g, '$1 $2')
    .replace(/  +/g, ' ');
}

/**
 * Sanitize a server-truncated markdown snippet (e.g. an alert's 500-char analysis
 * preview) so it never renders dangling markdown. A mid-token cut can leave an
 * emphasis marker open -- which would otherwise surface as a literal "**" -- and a
 * heading or list item sliced mid-sentence. We balance any stray emphasis/code marker
 * and trim the incomplete trailing block back to the last block that ends cleanly,
 * marking the elision with an ellipsis. Complete text passes through unchanged.
 */
export function cleanTruncatedMarkdown(raw?: string | null): string {
  if (!raw) return '';
  const original = raw.replace(/\s+$/, '');
  let text = original;

  // Close a mid-token cut: if an emphasis/code marker has an odd count, drop the
  // dangling run from the last (unmatched) marker to the end.
  for (const marker of ['**', '`', '*']) {
    if ((text.split(marker).length - 1) % 2 === 1) {
      text = text.slice(0, text.lastIndexOf(marker)).replace(/\s+$/, '');
    }
  }

  // Trim a trailing block the cut left incomplete (a dangling heading/rule or a half
  // sentence) back to the last block that ends cleanly -- sentence punctuation, a
  // citation chip, or a closing bracket/quote.
  const endsClean = /[.!?。\]】)"']\s*$/;
  while (text && !endsClean.test(text) && text.includes('\n')) {
    text = text.slice(0, text.lastIndexOf('\n')).replace(/\s+$/, '');
  }

  return text && text.length < original.length ? `${text} …` : text;
}
