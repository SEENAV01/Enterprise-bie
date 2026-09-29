'use strict';
// Trusted parser helper: never import, transpile-and-run, or evaluate candidate text.
const fs=require('node:fs');
const ts=require(process.argv[2]);
const raw=JSON.parse(fs.readFileSync(0,'utf8'));
const kind=raw.language==='TSX'?ts.ScriptKind.TSX:raw.language==='JAVASCRIPT'?ts.ScriptKind.JS:ts.ScriptKind.TS;
const source=ts.createSourceFile('candidate',raw.text,ts.ScriptTarget.Latest,true,kind);
const findings=[];const imports=new Set();let nodes=0;
function add(code,severity='BLOCKER',n){const line=n?source.getLineAndCharacterOfPosition(n.getStart(source)).line+1:0;const row={code,severity,line};if(!findings.some(x=>x.code===code&&x.severity===severity&&x.line===line)) findings.push(row);}
const dangerous=new Set(['eval','Function','require','process','global','globalThis','Deno','Bun','WebAssembly','fetch','XMLHttpRequest','WebSocket','EventSource','Worker','SharedWorker','localStorage','sessionStorage','indexedDB','__proto__','prototype','constructor','innerHTML','outerHTML','dangerouslySetInnerHTML','importScripts']);
function visit(n){
 nodes++; if(nodes>raw.max_nodes){add('SEC_AST_LIMIT');return;}
 if(ts.isImportDeclaration(n)||ts.isExportDeclaration(n)) {if(n.moduleSpecifier&&ts.isStringLiteral(n.moduleSpecifier))imports.add(n.moduleSpecifier.text);}
 if(ts.isImportEqualsDeclaration(n))add('SEC_DYNAMIC_MODULE');
 if(ts.isCallExpression(n)&&n.expression.kind===ts.SyntaxKind.ImportKeyword)add('SEC_DYNAMIC_IMPORT');
 if(ts.isIdentifier(n)&&dangerous.has(n.text))add('SEC_CAPABILITY_NAME','BLOCKER',n);
 if(ts.isElementAccessExpression(n)){
   if(ts.isStringLiteral(n.argumentExpression)&&dangerous.has(n.argumentExpression.text))add('SEC_CAPABILITY_ATTRIBUTE','BLOCKER',n);
   else add('SEC_COMPUTED_PROPERTY_REVIEW','REVIEW',n);
 }
 if(ts.isCallExpression(n)||ts.isNewExpression(n))add('SEC_CALL_REQUIRES_REVIEW','REVIEW',n);
 if(ts.isJsxAttribute(n)&&n.name&&n.name.getText(source)==='srcDoc')add('SEC_ACTIVE_MARKUP','BLOCKER',n);
 ts.forEachChild(n,visit);
}
function data(n){
 if(ts.isStringLiteral(n)||ts.isNumericLiteral(n)||[ts.SyntaxKind.TrueKeyword,ts.SyntaxKind.FalseKeyword,ts.SyntaxKind.NullKeyword].includes(n.kind))return true;
 if(ts.isPrefixUnaryExpression(n)&&[ts.SyntaxKind.MinusToken,ts.SyntaxKind.PlusToken].includes(n.operator)&&ts.isNumericLiteral(n.operand))return true;
 if(ts.isAsExpression(n)&&n.type.getText(source)==='const')return data(n.expression);
 if(ts.isArrayLiteralExpression(n))return n.elements.every(data);
 if(ts.isObjectLiteralExpression(n)){
  const names=new Set();return n.properties.every(p=>{
   if(!ts.isPropertyAssignment(p)||!p.name||!(ts.isIdentifier(p.name)||ts.isStringLiteral(p.name)||ts.isNumericLiteral(p.name)))return false;
   const key=p.name.text;if(names.has(key)||dangerous.has(key))return false;names.add(key);return data(p.initializer);
  });
 }
 return false;
}
if(source.parseDiagnostics.length)add('SEC_PARSE_ERROR');
visit(source);
if(raw.profile==='DATA'){
 const names=new Set();
 for(const s of source.statements){
  if(!ts.isVariableStatement(s)||!(s.declarationList.flags&ts.NodeFlags.Const)||!s.modifiers?.some(m=>m.kind===ts.SyntaxKind.ExportKeyword)) {add('SEC_DATA_PROFILE_VIOLATION','BLOCKER',s);continue;}
  for(const d of s.declarationList.declarations){if(!ts.isIdentifier(d.name)||names.has(d.name.text)||!d.initializer||!data(d.initializer))add('SEC_DATA_PROFILE_VIOLATION','BLOCKER',d);if(ts.isIdentifier(d.name))names.add(d.name.text);}
 }
 if(!source.statements.length)add('SEC_EMPTY_SOURCE');
}else add('SEC_GENERAL_CODE_REVIEW','REVIEW');
console.log(JSON.stringify({findings,imports:[...imports].sort(),nodes,parser_version:ts.version}));
