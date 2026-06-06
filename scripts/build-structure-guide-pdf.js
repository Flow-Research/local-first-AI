const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");
const inputPath = path.join(root, "docs", "project-structure-guide.md");
const outputPath = path.join(root, "docs", "project-structure-guide.pdf");

const markdown = fs.readFileSync(inputPath, "utf8");

function plainTextFromMarkdown(md) {
  return md
    .replace(/```[\s\S]*?```/g, block => block.replace(/```/g, ""))
    .replace(/\|---[\s\S]*?\n/g, "")
    .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/^#+\s*/gm, "")
    .replace(/^\|\s*/gm, "")
    .replace(/\s*\|\s*/g, " | ")
    .replace(/^\s*-\s+/gm, "- ")
    .replace(/\r/g, "");
}

function wrapLine(line, maxChars) {
  if (line.trim() === "") return [""];
  const words = line.split(/\s+/);
  const lines = [];
  let current = "";
  for (const word of words) {
    if ((current + " " + word).trim().length > maxChars) {
      if (current) lines.push(current);
      current = word;
    } else {
      current = (current + " " + word).trim();
    }
  }
  if (current) lines.push(current);
  return lines;
}

const text = plainTextFromMarkdown(markdown);
const sourceLines = text.split("\n");
const wrapped = [];
for (const line of sourceLines) {
  const isTitle = line.trim().length > 0 && !line.startsWith(" ") && !line.startsWith("- ") && line.length < 70;
  const max = isTitle ? 72 : 88;
  for (const wrappedLine of wrapLine(line, max)) {
    wrapped.push(wrappedLine);
  }
}

const pages = [];
let page = [];
for (const line of wrapped) {
  if (page.length >= 46) {
    pages.push(page);
    page = [];
  }
  page.push(line);
}
if (page.length) pages.push(page);

function escPdf(str) {
  return str
    .replace(/\\/g, "\\\\")
    .replace(/\(/g, "\\(")
    .replace(/\)/g, "\\)");
}

const objects = [];
function addObject(content) {
  objects.push(content);
  return objects.length;
}

const fontId = addObject("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>");
const pageIds = [];

for (let i = 0; i < pages.length; i++) {
  const lines = pages[i];
  let stream = "BT\n/F1 10 Tf\n50 742 Td\n14 TL\n";
  if (i === 0) {
    stream += "/F1 16 Tf\n(Local-First AI Context Assistant: Project Structure Guide) Tj\n/F1 10 Tf\n0 -28 Td\n";
  }
  for (const line of lines) {
    const safe = escPdf(line);
    stream += `(${safe}) Tj\nT*\n`;
  }
  stream += "ET\n";
  const contentId = addObject(`<< /Length ${Buffer.byteLength(stream, "utf8")} >>\nstream\n${stream}endstream`);
  const pageId = addObject(`<< /Type /Page /Parent PAGES_REF 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 ${fontId} 0 R >> >> /Contents ${contentId} 0 R >>`);
  pageIds.push(pageId);
}

const pagesId = addObject(`<< /Type /Pages /Kids [${pageIds.map(id => `${id} 0 R`).join(" ")}] /Count ${pageIds.length} >>`);
const catalogId = addObject(`<< /Type /Catalog /Pages ${pagesId} 0 R >>`);

for (let i = 0; i < objects.length; i++) {
  objects[i] = objects[i].replace(/PAGES_REF/g, String(pagesId));
}

let pdf = "%PDF-1.4\n";
const offsets = [0];
for (let i = 0; i < objects.length; i++) {
  offsets.push(Buffer.byteLength(pdf, "utf8"));
  pdf += `${i + 1} 0 obj\n${objects[i]}\nendobj\n`;
}
const xrefOffset = Buffer.byteLength(pdf, "utf8");
pdf += `xref\n0 ${objects.length + 1}\n`;
pdf += "0000000000 65535 f \n";
for (let i = 1; i < offsets.length; i++) {
  pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
}
pdf += `trailer\n<< /Size ${objects.length + 1} /Root ${catalogId} 0 R >>\nstartxref\n${xrefOffset}\n%%EOF\n`;

fs.writeFileSync(outputPath, pdf, "binary");
console.log(outputPath);
