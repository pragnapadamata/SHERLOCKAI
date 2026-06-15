import ReactMarkdown, { type Components } from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import rehypeSanitize from 'rehype-sanitize';
import remarkGfm from 'remark-gfm';

import { cn } from '@/lib/cn';
import { spaceUnits } from '@/lib/format';

import { CiteChip } from './Cite';

// Some models emit section markers as enclosed/emoji numerals (1️⃣, ①, ❶, ➀). They look out
// of place in a report, so normalize them to a plain "N." that renders as a clean label.
function normalizeNumerals(text: string): string {
  return text
    // keycap emoji digits: 0️⃣..9️⃣ (digit + optional VS-16 + combining enclosing keycap)
    .replace(/([0-9])️?⃣/gu, '$1.')
    // circled ①..⑳, negative-circled ❶..❿, dingbat ➀..➉ and ➊..➓
    .replace(/[①-⑳]/gu, (c) => `${c.codePointAt(0)! - 0x2460 + 1}.`)
    .replace(/[❶-❿]/gu, (c) => `${c.codePointAt(0)! - 0x2776 + 1}.`)
    .replace(/[➀-➉]/gu, (c) => `${c.codePointAt(0)! - 0x2780 + 1}.`)
    .replace(/[➊-➓]/gu, (c) => `${c.codePointAt(0)! - 0x278A + 1}.`);
}

// The agent embeds specialist-provenance tags inline as 【diagnostic】 and [[diagnostic]] /
// [[FAULT:F3-GBX-002]]. Convert BOTH forms to link tokens so react-markdown renders them as
// subtle citation chips (the `a` override below), instead of showing literal brackets.
function preprocess(text: string): string {
  const toCite = (tag: string) => `[${tag.trim()}](#cite-${encodeURIComponent(tag.trim())})`;
  return normalizeNumerals(text)
    .replace(/【\s*([^】]+?)\s*】/g, (_match, role: string) => toCite(role))
    .replace(/\[\[\s*([^[\]]+?)\s*\]\]/g, (_match, tag: string) => toCite(tag));
}

const COMPONENTS: Components = {
  a({ node: _node, href, children, ...props }) {
    if (typeof href === 'string' && href.startsWith('#cite-')) {
      const label = Array.isArray(children) ? children.join('') : String(children ?? '');
      return <CiteChip label={label} />;
    }
    return (
      <a href={href} target="_blank" rel="noreferrer noopener" {...props}>
        {children}
      </a>
    );
  },
};

const REMARK_PLUGINS = [remarkGfm];
// rehype-raw renders inline HTML the LLM emits (e.g. <br> in table cells) as real markup;
// rehype-sanitize (GitHub schema) then strips anything unsafe. Order matters: raw, then sanitize.
const REHYPE_PLUGINS = [rehypeRaw, rehypeSanitize];

interface MarkdownViewProps {
  children: string | null | undefined;
  className?: string;
  compact?: boolean;
}

// Renders LLM-generated GitHub-flavored markdown as clean, enterprise-styled HTML.
// Styling lives in the `.mw-markdown` scope in index.css.
export function MarkdownView({ children, className, compact = false }: MarkdownViewProps) {
  return (
    <div className={cn('mw-markdown', compact && 'mw-markdown-compact', className)}>
      <ReactMarkdown remarkPlugins={REMARK_PLUGINS} rehypePlugins={REHYPE_PLUGINS} components={COMPONENTS}>
        {spaceUnits(preprocess(children ?? ''))}
      </ReactMarkdown>
    </div>
  );
}
