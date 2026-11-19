// Use this rule from the root of the repository being reviewed.
const { execFileSync } = require('node:child_process');
const path = require('node:path');

function changedLines(file, base) {
  const args = [
    'diff',
    '--no-ext-diff',
    '--no-textconv',
    '--no-renames',
    '-U0',
    base,
    '--',
    file,
  ];
  const diff = execFileSync('git', args, { encoding: 'utf8' });
  const ranges = Array.from(
    diff.matchAll(/^@@ -[\d,]+ \+(\d+)(?:,(\d+))? @@/gm),
    (hunk) => {
      const first = Number(hunk[1]);
      return [first, first + Number(hunk[2] ?? 1)];
    },
  );
  if (!ranges.length && !execFileSync('git', ['ls-files', '--', file]).length) {
    return () => true;
  }
  return (line) => ranges.some(([start, end]) => start <= line && line < end);
}

module.exports = {
  names: ['GD001', 'studio-prose-punctuation'],
  description: 'Use a period or comma in studio prose',
  tags: ['prose'],
  parser: 'micromark',
  function(params, onError) {
    const base = process.env.GD_PROSE_BASE;
    const file = path.relative(process.cwd(), path.resolve(params.name));
    const include = base ? changedLines(file, base) : () => true;
    function inspect(tokens) {
      for (const token of tokens) {
        if (
          /^(?:code|html|literalAutolink|autolink|resource|definition|characterReference|characterEscape)/.test(
            token.type,
          )
        )
          continue;
        if (token.type === 'data') {
          const line = token.startLine;
          if (!include(line + params.frontMatterLines.length)) continue;
          for (const match of token.text.matchAll(/[;·]/gu)) {
            onError({
              lineNumber: line,
              range: [token.startColumn + match.index, 1],
            });
          }
        } else {
          inspect(token.children);
        }
      }
    }
    inspect(params.parsers.micromark.tokens);
  },
};
