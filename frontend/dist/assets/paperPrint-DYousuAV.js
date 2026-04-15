function r(e){return e.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}function z(e,t){return r(e?e.replace(/\{\{\s*paper_title\s*\}\}/gi,t):t)}function M(e,t){const m=e.paper||{},a=Number(m.widthMm)||210,l=Number(m.heightMm)||297,p=m.portrait!==!1?`${a}mm ${l}mm`:`${l}mm ${a}mm`,o=e.marginMm||{},d=Number(o.top)>=0?Number(o.top):15,b=Number(o.right)>=0?Number(o.right):15,u=Number(o.bottom)>=0?Number(o.bottom):15,f=Number(o.left)>=0?Number(o.left):15,n=e.header||{},g=n.show!==!1,h=Number(n.fontPt)>0?Number(n.fontPt):14,$=n.align||"center",N=n.titleTemplate,i=e.question||{},P=Number(i.fontPt)>0?Number(i.fontPt):11,w=Number(i.lineHeight)>0?Number(i.lineHeight):1.6,s=e.footer||{},v=s.show!==!1,x=Number(s.fontPt)>0?Number(s.fontPt):9,T=s.textTemplate||"",k=z(N,t.paperTitle),q=t.questionBlocks.map(c=>`<div class="q-block">${c.includes("<")?c:r(c)}</div>`).join(""),H=r(T.replace(/\{\{\s*page\s*\}\}/gi,"1").replace(/\{\{\s*pages\s*\}\}/gi,"1"));return`<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>${r(t.paperTitle)}</title>
  <style>
    @page { size: ${p}; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: ${d}mm ${b}mm ${u}mm ${f}mm;
      font-family: "Microsoft YaHei", "SimSun", sans-serif;
    }
    .doc-header { font-size: ${h}pt; text-align: ${$}; margin-bottom: 12px; }
    .doc-body { font-size: ${P}pt; line-height: ${w}; }
    .q-block { margin-bottom: 10px; page-break-inside: avoid; }
    .doc-footer { margin-top: 16px; font-size: ${x}pt; text-align: center; color: #666; }
  </style>
</head>
<body>
  ${g?`<div class="doc-header">${k}</div>`:""}
  <div class="doc-body">${q}</div>
  ${v?`<div class="doc-footer">${H}</div>`:""}
</body>
</html>`}function S(e){const t=window.open("","_blank");t&&(t.document.open(),t.document.write(e),t.document.close(),t.focus(),t.print())}export{M as b,S as o};
