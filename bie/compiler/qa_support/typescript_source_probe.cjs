'use strict';
// QA-004: Parse only. Never import, transpile-and-execute, or evaluate generated code.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
try {
  const [requestPath, typescriptPath] = process.argv.slice(2);
  const ts = require(path.resolve(typescriptPath));
  const raw = fs.readFileSync(requestPath, 'utf8');
  if (Buffer.byteLength(raw) > 32 * 1024 * 1024) throw new Error('probe input budget exceeded');
  const request = JSON.parse(raw);
  if (!Array.isArray(request.files) || !request.files.length) throw new Error('source files required');
  const findings = [];
  const imports = [];
  for (const entry of request.files) {
    if (typeof entry.path !== 'string' || typeof entry.content !== 'string') throw new Error('invalid source entry');
    const sf = ts.createSourceFile(entry.path, entry.content, ts.ScriptTarget.Latest, true,
      /\.[jt]sx$/.test(entry.path) ? ts.ScriptKind.TSX : ts.ScriptKind.TS);
    const add = (code, node, message, severity = 'ERROR') => {
      const pos = Math.max(0, node ? node.getStart(sf) : 0);
      const loc = sf.getLineAndCharacterOfPosition(pos);
      findings.push({code, severity, path: entry.path, line: loc.line + 1,
                     column: loc.character + 1, message});
    };
    for (const diagnostic of sf.parseDiagnostics) {
      const loc = sf.getLineAndCharacterOfPosition(diagnostic.start || 0);
      findings.push({code: 'TS' + diagnostic.code, severity: 'ERROR', path: entry.path,
        line: loc.line + 1, column: loc.character + 1,
        message: ts.flattenDiagnosticMessageText(diagnostic.messageText, ' | ')});
    }
    const randomAliases = new Set(['random']);
    const resolveName = n => {
      if (ts.isIdentifier(n)) return n.text;
      if (ts.isPropertyAccessExpression(n)) return resolveName(n.expression) + '.' + n.name.text;
      if (ts.isElementAccessExpression(n) && n.argumentExpression && ts.isStringLiteral(n.argumentExpression))
        return resolveName(n.expression) + '.' + n.argumentExpression.text;
      if (ts.isParenthesizedExpression(n)) return resolveName(n.expression);
      return '';
    };
    // Imports are resolved from exact generated file paths by the Python adapter.
    function recordImport(spec, node, dynamic = false) {
      if (!spec || !ts.isStringLiteralLike(spec)) {
        add('QA_DYNAMIC_IMPORT_UNBOUNDED', node, 'Dynamic import/require target must be a static, governed module.');
        return;
      }
      imports.push({file: entry.path, specifier: spec.text, dynamic});
      if (/^(?:node:|fs$|fs\/|child_process$|net$|tls$|http$|https$|vm$|worker_threads$|dgram$)/.test(spec.text))
        add('QA_NODE_RUNTIME_IMPORT', node, 'Generated video code cannot import a Node host capability.');
      if (/^(?:https?:|data:|file:|\/)/.test(spec.text))
        add('QA_EXTERNAL_IMPORT', node, 'Remote/absolute executable import is not a governed dependency.');
    }
    function visit(n) {
      if (ts.isImportDeclaration(n) || ts.isExportDeclaration(n) && n.moduleSpecifier) {
        recordImport(n.moduleSpecifier, n);
        if (ts.isImportDeclaration(n) && n.moduleSpecifier.text === 'remotion') {
          const bindings = n.importClause && n.importClause.namedBindings;
          if (bindings && ts.isNamedImports(bindings)) {
            for (const spec of bindings.elements) {
              if ((spec.propertyName || spec.name).text === 'random') randomAliases.add(spec.name.text);
            }
          }
        }
      }
      if (ts.isImportEqualsDeclaration(n) && ts.isExternalModuleReference(n.moduleReference))
        recordImport(n.moduleReference.expression, n);
      if (ts.isCallExpression(n)) {
        const name = resolveName(n.expression);
        if (n.expression.kind === ts.SyntaxKind.ImportKeyword || name === 'require')
          recordImport(n.arguments[0], n, true);
        if (/^(?:globalThis\.|window\.)?(?:eval|Function)$/.test(name))
          add('QA_EXECUTABLE_EVAL', n, 'Dynamic code evaluation is forbidden.');
        if (/^(?:globalThis\.|window\.)?Math\.random$/.test(name) ||
            (randomAliases.has(name) && (!n.arguments.length || n.arguments[0].kind === ts.SyntaxKind.NullKeyword)))
          add('QA_UNSEEDED_RANDOM', n, 'Unseeded randomness makes repeat rendering nondeterministic.');
        if (/(?:^|\.)Date\.now$/.test(name) || /(?:^|\.)performance\.now$/.test(name))
          add('QA_WALL_CLOCK', n, 'Wall-clock state must not affect generated content.');
        if (/^(?:globalThis\.|window\.)?(?:setTimeout|setInterval|requestAnimationFrame)$/.test(name))
          add('QA_REALTIME_SCHEDULER', n, 'Use frame-driven animation instead of real-time schedulers.');
        if (/^(?:globalThis\.|window\.)?(?:fetch|WebSocket|EventSource)$/.test(name))
          add('QA_NETWORK_SIDE_EFFECT', n, 'Runtime network side effects require a separate governed asset stage.');
        if (name === 'crypto.randomUUID' || name === 'crypto.getRandomValues')
          add('QA_UNSEEDED_RANDOM', n, 'Cryptographic runtime randomness is nondeterministic.');
      }
      if (ts.isNewExpression(n)) {
        const name = resolveName(n.expression);
        if (name === 'Function' || name === 'globalThis.Function')
          add('QA_EXECUTABLE_EVAL', n, 'Function construction evaluates generated strings.');
        if ((name === 'Date' || name === 'globalThis.Date') && !(n.arguments && n.arguments.length))
          add('QA_WALL_CLOCK', n, 'new Date() reads wall-clock time.');
        if (['WebSocket','EventSource','XMLHttpRequest','Worker','SharedWorker'].includes(name))
          add('QA_NETWORK_SIDE_EFFECT', n, 'Generated component opens an uncontrolled execution/network channel.');
      }
      if (ts.isPropertyAccessExpression(n) || ts.isElementAccessExpression(n)) {
        const name = resolveName(n);
        if (/^(?:globalThis\.|window\.)?Math\.random$/.test(name))
          add('QA_UNSEEDED_RANDOM', n, 'A reference/alias to unseeded Math.random is nondeterministic.');
        if (/(?:^|\.)Date\.now$/.test(name) || /(?:^|\.)performance\.now$/.test(name))
          add('QA_WALL_CLOCK', n, 'A reference/alias to a wall-clock function is not an explicit input.');
        if (/^(?:globalThis\.)?process\.env(?:\.|$)/.test(name))
          add('QA_ENVIRONMENT_DEPENDENCY', n, 'Environment state must be an explicit compiler input.');
      }
      if (ts.isPropertyAssignment(n)) {
        const key = ts.isIdentifier(n.name) || ts.isStringLiteralLike(n.name) ? n.name.text : '';
        if (['animation','animationName','transition'].includes(key))
          add('QA_CSS_REALTIME_ANIMATION', n, 'CSS real-time animation/transition is not frame driven.');
      }
      if (ts.isJsxAttribute(n) && n.name.getText(sf) === 'dangerouslySetInnerHTML')
        add('QA_UNSAFE_HTML', n, 'Untrusted HTML cannot bypass text/JSX escaping.');
      ts.forEachChild(n, visit);
    }
    visit(sf);
    // Inspect actual comments, not strings that happen to mention @ts-ignore.
    const scanner = ts.createScanner(ts.ScriptTarget.Latest, false, ts.LanguageVariant.JSX, entry.content);
    for (let kind = scanner.scan(); kind !== ts.SyntaxKind.EndOfFileToken; kind = scanner.scan()) {
      if ([ts.SyntaxKind.SingleLineCommentTrivia, ts.SyntaxKind.MultiLineCommentTrivia].includes(kind) &&
          /@ts-(?:ignore|nocheck)/.test(scanner.getTokenText())) {
        const loc = sf.getLineAndCharacterOfPosition(scanner.getTokenPos());
        findings.push({code:'QA_TYPECHECK_SUPPRESSION',severity:'ERROR',path:entry.path,
          line:loc.line+1,column:loc.character+1,message:'Generated code cannot suppress type checking.'});
      }
    }
  }
  process.stdout.write(JSON.stringify({schema_version:'bie.typescript-source-probe.v1',
    typescript_version:ts.version, files_parsed:request.files.length, findings, imports,
    execution_kind:'REAL_TYPESCRIPT_AST_PARSER', full_typecheck:false,
    request_sha256:crypto.createHash('sha256').update(raw).digest('hex'), accepted:false}));
} catch (error) {
  process.stderr.write(String(error && error.stack || error));
  process.exitCode = 2;
}
