// @-mention support, frontend-only and text-based. A mention is stored inline in the
// existing free-text fields as the literal token `@[Full Name]` (e.g. `@[A. Bose]`) -- no
// schema or backend change. Parse with /@\[([^\]]+)\]/g. We build a fresh regex per call so
// the global `lastIndex` is never shared across callers.
const MENTION_PATTERN = '@\\[([^\\]]+)\\]';

export function mentionRegex(): RegExp {
  return new RegExp(MENTION_PATTERN, 'g');
}

/** True if the text contains at least one `@[Name]` token. */
export function hasMention(text: string | null | undefined): boolean {
  return !!text && mentionRegex().test(text);
}

/** The distinct names referenced by `@[Name]` tokens in the text, in order of appearance. */
export function mentionedNames(text: string | null | undefined): string[] {
  if (!text) return [];
  const re = mentionRegex();
  const names: string[] = [];
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) names.push(m[1].trim());
  return names;
}

/** True if the text `@[...]`-mentions the given display name (exact, distinct persona names). */
export function textMentionsName(text: string | null | undefined, name: string | null | undefined): boolean {
  if (!text || !name) return false;
  return mentionedNames(text).includes(name);
}
