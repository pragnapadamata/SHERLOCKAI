import type { ReactNode } from 'react';

// The agent embeds provenance/citation tags inline in two forms:
//   - role tags:  【diagnostic】 (lenticular) and [[diagnostic]] (double-bracket)
//   - id tags:    [[FAULT:F3-GBX-002]], [[FR-2024-002]], [[SOMEID]]
// Both must render as small, clean chips -- never as raw 【...】 or [[...]] text.

// Matches a single 【...】 or [[...]] tag. Group 1 = lenticular content, group 2 = bracket content.
const CITE_TAG = /【\s*([^】]+?)\s*】|\[\[\s*([^[\]]+?)\s*\]\]/g;

// The single, canonical citation chip. Every citation form -- inline numbered refs
// (【1】), inline label refs ([[FAULT:…]] / [[diagnostic]]), and numbered source badges
// -- renders through THIS component, so a reader can't tell two answers used different
// schemes: identical padding, radius, font size, muted background, and inline placement.
export function CiteChip({ label, title }: { label: string; title?: string }) {
  return (
    <span
      title={title}
      className="mx-0.5 inline-flex items-center rounded-sm border border-brand-100 bg-brand-50 px-1 py-px align-middle text-[10px] font-medium uppercase leading-none tracking-wide text-brand-600"
    >
      {label.replace(/[_:]/g, ' ').trim()}
    </span>
  );
}

// Render a plain string with any inline 【...】 / [[...]] tags turned into chips and the rest
// left as text. Used where the content is NOT markdown (e.g. the Sources list labels).
export function renderCitations(text: string | null | undefined): ReactNode {
  if (!text) return text ?? null;
  const parts: ReactNode[] = [];
  let last = 0;
  let key = 0;
  let m: RegExpExecArray | null;
  CITE_TAG.lastIndex = 0;
  while ((m = CITE_TAG.exec(text)) !== null) {
    if (m.index > last) parts.push(text.slice(last, m.index));
    parts.push(<CiteChip key={key++} label={(m[1] ?? m[2] ?? '').trim()} />);
    last = m.index + m[0].length;
  }
  if (parts.length === 0) return text;
  if (last < text.length) parts.push(text.slice(last));
  return parts;
}
