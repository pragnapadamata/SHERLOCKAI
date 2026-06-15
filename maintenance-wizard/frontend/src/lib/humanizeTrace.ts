import { CHANNEL_SHORT, channelShort } from '@/lib/channels';

// A Python-style list of single-quoted items, e.g. ['vibration_rms_mm_s', 'oil_fe_ppm'].
const QUOTED_LIST = /\[\s*'(?:[^']*)'(?:\s*,\s*'[^']*')*\s*\]/g;
// Pulls each 'item' out of a matched list.
const QUOTED_ITEM = /'([^']*)'/g;

/**
 * Clean raw agent-trace internals at the display layer (also fixes existing cached
 * traces -- no re-capture):
 *
 *   (a) Reformat any Python-style list of single-quoted items into a human comma-separated
 *       phrase, mapping each item through the channel humanizer (channel codes become human
 *       names; ordinary words like 'gear'/'iron' pass through unchanged).
 *         ['vibration_rms_mm_s', 'oil_fe_ppm'] -> "overall vibration, iron particles in oil"
 *   (b) Replace any remaining standalone raw channel code anywhere in the text with its
 *       human name, word-boundary-safe so asset codes (HSM-F3-GBX) and fault codes
 *       (F3-GBX-002) -- which use hyphens, not the channels' underscores -- are untouched.
 *
 * Fault codes, asset codes, and numbers are left as-is. We use the SHORT channel labels
 * (no unit, lowercase) because the unit-bearing labels contain commas that would read as
 * extra list items in a comma-joined phrase.
 */
export function humanizeTrace(text: string): string {
  if (!text) return text;

  // (a) Bracketed single-quoted lists -> human comma-separated phrase.
  let out = text.replace(QUOTED_LIST, (list) => {
    const items: string[] = [];
    QUOTED_ITEM.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = QUOTED_ITEM.exec(list)) !== null) items.push(channelShort(m[1]));
    return items.join(', ');
  });

  // (b) Any remaining standalone raw channel code -> human name. Keys come from the
  //     channels map so this stays in sync with channelShort.
  for (const code of Object.keys(CHANNEL_SHORT)) {
    out = out.replace(new RegExp(`\\b${code}\\b`, 'g'), channelShort(code));
  }
  return out;
}
