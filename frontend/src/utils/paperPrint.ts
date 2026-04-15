/**
 * 试卷打印插件：根据模板 layout_json 与题目内容生成可打印 HTML，并唤起浏览器打印。
 */

function escHtml(s: string) {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export type PaperPrintPayload = {
  paperTitle: string;
  /** 每道题目已格式化的 HTML 或纯文本（纯文本会转义） */
  questionBlocks: string[];
};

/** 将 layout 中的占位符替换为试卷标题（供预览） */
export function applyTitleTemplate(tpl: string | undefined, paperTitle: string) {
  if (!tpl) return escHtml(paperTitle);
  return escHtml(tpl.replace(/\{\{\s*paper_title\s*\}\}/gi, paperTitle));
}

/**
 * 构建完整打印文档 HTML（含 @page 尺寸与页边距）。
 * 供后期「试卷详情」等页面调用：resolve模板后传入 layout与题目列表即可。
 */
export function buildPaperPrintHtml(layout: Record<string, unknown>, payload: PaperPrintPayload): string {
  const paper = (layout.paper || {}) as Record<string, unknown>;
  const w = Number(paper.widthMm) || 210;
  const h = Number(paper.heightMm) || 297;
  const portrait = paper.portrait !== false;
  const sizeCss = portrait ? `${w}mm ${h}mm` : `${h}mm ${w}mm`;
  const m = (layout.marginMm || {}) as Record<string, number>;
  const mt = Number(m.top) >= 0 ? Number(m.top) : 15;
  const mr = Number(m.right) >= 0 ? Number(m.right) : 15;
  const mb = Number(m.bottom) >= 0 ? Number(m.bottom) : 15;
  const ml = Number(m.left) >= 0 ? Number(m.left) : 15;
  const header = (layout.header || {}) as Record<string, unknown>;
  const headerShow = header.show !== false;
  const headerFont = Number(header.fontPt) > 0 ? Number(header.fontPt) : 14;
  const headerAlign = (header.align as string) || "center";
  const titleTpl = header.titleTemplate as string | undefined;
  const qConf = (layout.question || {}) as Record<string, unknown>;
  const qFont = Number(qConf.fontPt) > 0 ? Number(qConf.fontPt) : 11;
  const qLh = Number(qConf.lineHeight) > 0 ? Number(qConf.lineHeight) : 1.6;
  const footer = (layout.footer || {}) as Record<string, unknown>;
  const footerShow = footer.show !== false;
  const footerFont = Number(footer.fontPt) > 0 ? Number(footer.fontPt) : 9;
  const footerTpl = (footer.textTemplate as string) || "";

  const titleHtml = applyTitleTemplate(titleTpl, payload.paperTitle);
  const blocksHtml = payload.questionBlocks
    .map((b) => {
      const chunk = b.includes("<") ? b : escHtml(b);
      return `<div class="q-block">${chunk}</div>`;
    })
    .join("");

  const footerHtml = escHtml(footerTpl.replace(/\{\{\s*page\s*\}\}/gi, "1").replace(/\{\{\s*pages\s*\}\}/gi, "1"));

  return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <title>${escHtml(payload.paperTitle)}</title>
  <style>
    @page { size: ${sizeCss}; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      padding: ${mt}mm ${mr}mm ${mb}mm ${ml}mm;
      font-family: "Microsoft YaHei", "SimSun", sans-serif;
    }
    .doc-header { font-size: ${headerFont}pt; text-align: ${headerAlign}; margin-bottom: 12px; }
    .doc-body { font-size: ${qFont}pt; line-height: ${qLh}; }
    .q-block { margin-bottom: 10px; page-break-inside: avoid; }
    .doc-footer { margin-top: 16px; font-size: ${footerFont}pt; text-align: center; color: #666; }
  </style>
</head>
<body>
  ${headerShow ? `<div class="doc-header">${titleHtml}</div>` : ""}
  <div class="doc-body">${blocksHtml}</div>
  ${footerShow ? `<div class="doc-footer">${footerHtml}</div>` : ""}
</body>
</html>`;
}

/** 打开新窗口并执行打印（浏览器打印对话框） */
export function openPaperPrint(html: string) {
  const w = window.open("", "_blank");
  if (!w) return;
  w.document.open();
  w.document.write(html);
  w.document.close();
  w.focus();
  w.print();
}
