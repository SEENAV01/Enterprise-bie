tree => {
 const svgNS='http://www.w3.org/2000/svg',mathNS='http://www.w3.org/1998/Math/MathML';
 const attrs={className:'class',strokeWidth:'stroke-width',strokeDasharray:'stroke-dasharray',strokeDashoffset:'stroke-dashoffset',textAnchor:'text-anchor',dominantBaseline:'dominant-baseline',fillOpacity:'fill-opacity',fontSize:'font-size',fillRule:'fill-rule',clipPath:'clip-path',strokeLinejoin:'stroke-linejoin',strokeLinecap:'stroke-linecap'};
 const unitless=new Set(['opacity','scale','flex','flexGrow','flexShrink','order','zIndex','fontWeight','lineHeight']);
 function node(n,ns=null){
  if(n===null||n===undefined||n===false)return document.createTextNode('');
  if(typeof n==='string'||typeof n==='number')return document.createTextNode(String(n));
  ns=n.tag==='svg'?svgNS:n.tag==='math'?mathNS:ns;
  const e=ns?document.createElementNS(ns,n.tag):document.createElement(n.tag);
  for(const [k,v] of Object.entries(n.props||{})){
   if(['key','children'].includes(k)||v===null||v===undefined)continue;
   if(k==='style'){for(const [sk,sv] of Object.entries(v))e.style[sk]=(typeof sv==='number'&&!unitless.has(sk))?sv+'px':String(sv);}
   else e.setAttribute(attrs[k]||k,String(v));
  }
  for(const c of n.children||[])e.append(node(c,ns));return e;
 }
 document.getElementById('root').replaceChildren(node(tree));
}
