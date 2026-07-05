import fs from 'fs';
import path from 'path';
import https from 'https';
import { PDFDocument, rgb } from 'pdf-lib';
import fontkit from '@pdf-lib/fontkit';

// ------------------------------------------------------------------
// Font Downloader (cached locally in e:/Report-Engine/fonts/)
// ------------------------------------------------------------------
async function downloadFontIfNeeded(url, destPath) {
  if (fs.existsSync(destPath)) {
    return fs.readFileSync(destPath);
  }
  fs.mkdirSync(path.dirname(destPath), { recursive: true });
  console.log(`Downloading font from: ${url}`);
  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode === 302 || response.statusCode === 301) {
        // Follow redirect
        downloadFontIfNeeded(response.headers.location, destPath).then(resolve).catch(reject);
        return;
      }
      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download font: status code ${response.statusCode}`));
        return;
      }
      const data = [];
      response.on('data', (chunk) => data.push(chunk));
      response.on('end', () => {
        const buffer = Buffer.concat(data);
        fs.writeFileSync(destPath, buffer);
        console.log(`Saved font to: ${destPath}`);
        resolve(buffer);
      });
    }).on('error', (err) => {
      console.error(`Error downloading font: ${err.message}`);
      reject(err);
    });
  });
}

// ------------------------------------------------------------------
// Text wrapping logic
// ------------------------------------------------------------------
function wrapText(text, maxWidth, fontSize, font) {
  const words = text.split(/\s+/);
  const lines = [];
  let currentLine = '';

  for (let word of words) {
    const testLine = currentLine ? `${currentLine} ${word}` : word;
    const width = font.widthOfTextAtSize(testLine, fontSize);
    if (width > maxWidth) {
      lines.push(currentLine);
      currentLine = word;
    } else {
      currentLine = testLine;
    }
  }
  if (currentLine) {
    lines.push(currentLine);
  }
  return lines;
}

function stripEmojis(text) {
  if (!text) return "";
  return text.replace(/[\u{1F300}-\u{1F9FF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{1F000}-\u{1FFFF}]/gu, '');
}

function getWrappedLines(text, maxWidth, fontSize, font) {
  const paragraphs = text.split(/\n+/);
  const allLines = [];
  for (let i = 0; i < paragraphs.length; i++) {
    const p = paragraphs[i].trim();
    if (!p) continue;
    const pLines = wrapText(p, maxWidth, fontSize, font);
    allLines.push(...pLines);
    if (i < paragraphs.length - 1) {
      allLines.push(''); // spacing line between paragraphs
    }
  }
  return allLines;
}

// ------------------------------------------------------------------
// Table Drawing Helper
// ------------------------------------------------------------------
function drawTable(page, x, y, colWidths, defaultRowHeight, rows, bodyFont, boldFont) {
  const textPadding = 8;
  const roseGold = rgb(0.79, 0.59, 0.48); // #C9967B
  const textDark = rgb(0.17, 0.1, 0.07); // #2C1A11
  
  let currentY = y;
  
  for (let r = 0; r < rows.length; r++) {
    const row = rows[r];
    const isHeader = r === 0;
    
    // 1. Pre-calculate wrapped lines for each cell to determine the row height
    const cellLinesList = [];
    let maxLines = 1;
    
    for (let c = 0; c < row.length; c++) {
      const cellText = row[c] || '';
      const colWidth = colWidths[c];
      const maxTextWidth = colWidth - (textPadding * 2);
      
      // Clean up text: replace slash or hyphen with space-included versions to allow natural wrapping
      let cleanedText = cellText;
      if (!isHeader) {
        cleanedText = cellText
          .replace(/\//g, ' / ')
          .replace(/-/g, ' - ');
      }
      
      const cellLines = wrapText(cleanedText, maxTextWidth, 9.5, isHeader ? boldFont : bodyFont);
      cellLinesList.push(cellLines);
      if (cellLines.length > maxLines) {
        maxLines = cellLines.length;
      }
    }
    
    // Row height is dynamic: at least defaultRowHeight, but grows with lines
    const rowHeight = Math.max(defaultRowHeight, maxLines * 12 + 10);
    
    // 2. Draw the row cells
    let currentX = x;
    for (let c = 0; c < row.length; c++) {
      const cellLines = cellLinesList[c];
      const colWidth = colWidths[c];
      
      // Draw cell border
      page.drawRectangle({
        x: currentX,
        y: currentY - rowHeight,
        width: colWidth,
        height: rowHeight,
        borderColor: roseGold,
        borderWidth: 1,
        color: isHeader ? rgb(0.98, 0.96, 0.93) : undefined
      });
      
      // Draw cell text centered vertically
      const lineGap = 11;
      const textY = currentY - rowHeight / 2 + (cellLines.length - 1) * lineGap / 2 - 4;
      
      for (let i = 0; i < cellLines.length; i++) {
        page.drawText(cellLines[i], {
          x: currentX + textPadding,
          y: textY - (i * lineGap),
          size: 9.5,
          font: isHeader ? boldFont : bodyFont,
          color: textDark
        });
      }
      
      currentX += colWidth;
    }
    currentY -= rowHeight;
  }
  return currentY;
}

// ------------------------------------------------------------------
// Main Compiler function
// ------------------------------------------------------------------
async function main() {
  const args = {};
  for (let i = 2; i < process.argv.length; i += 2) {
    const key = process.argv[i].replace('--', '');
    const val = process.argv[i + 1];
    args[key] = val;
  }

  if (!args.data || !args.template || !args.output) {
    console.error("Usage: node compile_report.js --data <data.json> --template <template.pdf> --output <output.pdf>");
    process.exit(1);
  }

  console.log(`Loading data from: ${args.data}`);
  const data = JSON.parse(fs.readFileSync(args.data, 'utf-8'));

  console.log(`Loading PDF template from: ${args.template}`);
  const templateBytes = fs.readFileSync(args.template);
  const pdfDoc = await PDFDocument.load(templateBytes);
  
  // Register fontkit
  pdfDoc.registerFontkit(fontkit);

  // ------------------------------------------------------------------
  // Embed Fonts (Local System Fonts with Online Fallbacks)
  // ------------------------------------------------------------------
  console.log("Loading and embedding fonts...");

  let bodyFontBytes, boldFontBytes, headerFontBytes, headerBoldFontBytes;

  // 1. Try loading local Windows system fonts first (instant & offline)
  const localHeaderPath = 'C:/Windows/Fonts/georgia.ttf';
  const localHeaderBoldPath = 'C:/Windows/Fonts/georgiab.ttf';
  const localBodyPath = 'C:/Windows/Fonts/georgia.ttf';
  const localBodyBoldPath = 'C:/Windows/Fonts/georgiab.ttf';

  if (
    fs.existsSync(localHeaderPath) &&
    fs.existsSync(localHeaderBoldPath) &&
    fs.existsSync(localBodyPath) &&
    fs.existsSync(localBodyBoldPath)
  ) {
    console.log("Using local Windows system fonts (Georgia)...");
    headerFontBytes = fs.readFileSync(localHeaderPath);
    headerBoldFontBytes = fs.readFileSync(localHeaderBoldPath);
    bodyFontBytes = fs.readFileSync(localBodyPath);
    boldFontBytes = fs.readFileSync(localBodyBoldPath);
  } else {
    // 2. Fall back to downloading portable Google Fonts from raw GitHub (used on Linux/servers)
    console.log("Local system fonts not found. Downloading fallbacks from Google Fonts...");
    const headerRegUrl = 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Regular.ttf';
    const headerBoldUrl = 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf';
    const bodyRegUrl = 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Regular.ttf';
    const bodyBoldUrl = 'https://github.com/google/fonts/raw/main/ofl/cormorantgaramond/static/CormorantGaramond-Bold.ttf';

    const fontsDir = path.resolve('fonts');
    
    headerFontBytes = await downloadFontIfNeeded(headerRegUrl, path.join(fontsDir, 'CormorantGaramond-Regular.ttf'));
    headerBoldFontBytes = await downloadFontIfNeeded(headerBoldUrl, path.join(fontsDir, 'CormorantGaramond-Bold.ttf'));
    bodyFontBytes = await downloadFontIfNeeded(bodyRegUrl, path.join(fontsDir, 'CormorantGaramond-Regular.ttf'));
    boldFontBytes = await downloadFontIfNeeded(bodyBoldUrl, path.join(fontsDir, 'CormorantGaramond-Bold.ttf'));
  }

  const bodyFont = await pdfDoc.embedFont(bodyFontBytes);
  const boldFont = await pdfDoc.embedFont(boldFontBytes);
  const headerFont = await pdfDoc.embedFont(headerFontBytes);
  const headerBoldFont = await pdfDoc.embedFont(headerBoldFontBytes);

  const pages = pdfDoc.getPages();
  const pageCount = pages.length;
  console.log(`PDF Template has ${pageCount} pages.`);

  const fontSize = 12.0;
  const lineSpacing = fontSize * 1.85;
  const textColorDark = rgb(0.17, 0.1, 0.07); // #2C1A11

  // Keep track of overflow text for pages dynamically
  const overflowLines = {};

  for (let pageIdx = 0; pageIdx < pageCount; pageIdx++) {
    const page = pages[pageIdx];
    let rect = data.layout[pageIdx];
    if (rect) {
      rect = {
        x_left: 70,
        x_right: 525,
        y_top: rect.y_top,
        y_bottom: rect.y_bottom
      };
    }
    


    // Draw charts/tables if they belong on this page index
    
    // Page 2 (index 1): User Details Table
    if (pageIdx === 1) {
      if (rect) {
        console.log(`Page ${pageIdx + 1}: Drawing User Details Table...`);
        const rows = [
          ["Birth Profile Field", "Personal Astrological Details"],
          ["Full Name", data.client_name || ""],
          ["Gender", data.client_gender || ""],
          ["Date of Birth", data.client_dob || ""],
          ["Time of Birth", data.client_tob || ""],
          ["Place of Birth", data.client_pob || ""],
          ["Lagna (Ascendant Sign)", data.lagna_sign || ""],
          ["Moon Sign", data.moon_sign || ""]
        ];
        const colWidths = [160, 295];
        const rowHeight = 26;
        const totalTableHeight = rowHeight * rows.length;
        const yStart = rect.y_bottom + (rect.y_top - rect.y_bottom - totalTableHeight) / 2 + totalTableHeight;
        
        drawTable(page, rect.x_left, yStart, colWidths, rowHeight, rows, bodyFont, boldFont);
      }
      continue;
    }
    
    // Page 6 (index 5): D1 Chart & 2 lines explaining it
    if (pageIdx === 5) {
      if (rect && data.d1_png && fs.existsSync(data.d1_png)) {
        console.log(`Page ${pageIdx + 1}: Drawing D1 Chart...`);
        const pngBytes = fs.readFileSync(data.d1_png);
        const image = await pdfDoc.embedPng(pngBytes);
        
        const chartSize = 250;
        const xChart = rect.x_left + (rect.x_right - rect.x_left - chartSize) / 2;
        const yChart = rect.y_top - chartSize - 10;
        
        page.drawImage(image, {
          x: xChart,
          y: yChart,
          width: chartSize,
          height: chartSize
        });
        
        // Draw 2 lines explaining D1 Chart
        const explanation = stripEmojis(data.sections[5] || "This is your D1 Birth Chart, the blueprint of your soul's current life journey. It shows planetary positions at the precise moment of your birth.");
        const wrappedExp = getWrappedLines(explanation, rect.x_right - rect.x_left, fontSize, bodyFont);
        
        let expY = yChart - 20;
        for (const line of wrappedExp) {
          if (line !== '') {
            page.drawText(line, {
              x: rect.x_left,
              y: expY,
              size: fontSize,
              font: bodyFont,
              color: textColorDark
            });
          }
          expY -= lineSpacing;
        }
      }
      continue;
    }
    
    // Page 11 (index 10): D9 & D30 Charts (no text)
    if (pageIdx === 10) {
      if (rect) {
        console.log(`Page ${pageIdx + 1}: Drawing D9 and D30 Charts...`);
        const chartSize = 200;
        const spacing = (rect.x_right - rect.x_left - (chartSize * 2)) / 3;
        
        const yChart = rect.y_bottom + (rect.y_top - rect.y_bottom - chartSize) / 2 + 10;
        
        if (data.d9_png && fs.existsSync(data.d9_png)) {
          const d9Bytes = fs.readFileSync(data.d9_png);
          const d9Image = await pdfDoc.embedPng(d9Bytes);
          const xD9 = rect.x_left + spacing;
          
          page.drawImage(d9Image, {
            x: xD9,
            y: yChart,
            width: chartSize,
            height: chartSize
          });
          
          page.drawText("D9 NAVAMSA CHART", {
            x: xD9 + (chartSize - headerBoldFont.widthOfTextAtSize("D9 NAVAMSA CHART", 12)) / 2,
            y: yChart - 20,
            size: 12,
            font: headerBoldFont,
            color: textColorDark
          });
        }
        
        if (data.d30_png && fs.existsSync(data.d30_png)) {
          const d30Bytes = fs.readFileSync(data.d30_png);
          const d30Image = await pdfDoc.embedPng(d30Bytes);
          const xD30 = rect.x_left + spacing * 2 + chartSize;
          
          page.drawImage(d30Image, {
            x: xD30,
            y: yChart,
            width: chartSize,
            height: chartSize
          });
          
          page.drawText("D30 TRIMSAMSHA CHART", {
            x: xD30 + (chartSize - headerBoldFont.widthOfTextAtSize("D30 TRIMSAMSHA CHART", 12)) / 2,
            y: yChart - 20,
            size: 12,
            font: headerBoldFont,
            color: textColorDark
          });
        }
      }
      continue;
    }
    
    // Page 22 (index 21): 3-Year Love Timeline (Table + Text explanation below)
    if (pageIdx === 21) {
      if (rect) {
        console.log(`Page ${pageIdx + 1}: Drawing 3-Year Timeline Table...`);
        const rows = [
          ["Vimshottari Period", "Timeline Windows", "Romantic Potential & Themes"]
        ];
        if (data.dasha_timeline && data.dasha_timeline.length > 0) {
          for (const item of data.dasha_timeline) {
            rows.push(item);
          }
        } else {
          rows.push(["Jupiter - Saturn", "Current - Dec 2026", "Subtle, steady emotional growth and marriage gateway."]);
          rows.push(["Jupiter - Mercury", "Dec 2026 - Mar 2029", "Exciting communicative windows, active socialization."]);
        }
        
        const colWidths = [125, 135, 195];
        const rowHeight = 24;
        const tableY = rect.y_top - 10;
        const finalTableY = drawTable(page, rect.x_left, tableY, colWidths, rowHeight, rows, bodyFont, boldFont);
        
        // Draw explanatory text below table
        const textBelow = stripEmojis(data.sections[21] || "");
        if (textBelow) {
          const wrapped = getWrappedLines(textBelow, rect.x_right - rect.x_left, fontSize, bodyFont);
          let txtY = finalTableY - 25;
          for (const line of wrapped) {
            if (line !== '') {
              page.drawText(line, {
                x: rect.x_left,
                y: txtY,
                size: fontSize,
                font: bodyFont,
                color: textColorDark
              });
            }
            txtY -= lineSpacing;
          }
        }
      }
      continue;
    }
    
    // Page 23 (index 22): Prayantar Dasha Timing (Table + Text explanation below)
    if (pageIdx === 22) {
      if (rect) {
        console.log(`Page ${pageIdx + 1}: Drawing Prayantar Dasha Table...`);
        const rows = [
          ["Sub-Sub Cycle", "Exact Date Window", "Intensity & Opportunity Key"]
        ];
        if (data.prayantar_dasha && data.prayantar_dasha.length > 0) {
          for (const item of data.prayantar_dasha) {
            rows.push(item);
          }
        } else {
          rows.push(["Jupiter-Saturn-Merc", "Jul 2026 - Sep 2026", "High. Ideal window for proposals or serious talks."]);
          rows.push(["Jupiter-Saturn-Ketu", "Sep 2026 - Nov 2026", "Moderate. Lessons in patient detachment."]);
          rows.push(["Jupiter-Saturn-Venus", "Nov 2026 - Mar 2027", "Very High. Harmonious celestial support for union."]);
        }
        
        const colWidths = [125, 135, 195];
        const rowHeight = 24;
        const tableY = rect.y_top - 10;
        const finalTableY = drawTable(page, rect.x_left, tableY, colWidths, rowHeight, rows, bodyFont, boldFont);
        
        // Draw explanatory text below table
        const textBelow = stripEmojis(data.sections[22] || "");
        if (textBelow) {
          const wrapped = getWrappedLines(textBelow, rect.x_right - rect.x_left, fontSize, bodyFont);
          let txtY = finalTableY - 25;
          for (const line of wrapped) {
            if (line !== '') {
              page.drawText(line, {
                x: rect.x_left,
                y: txtY,
                size: fontSize,
                font: bodyFont,
                color: textColorDark
              });
            }
            txtY -= lineSpacing;
          }
        }
      }
      continue;
    }
    
    // Page 20 (index 19): Risk matrix table?
    // Let's draw a table if it is Page 20 (Compatibility Matrix)
    if (pageIdx === 19) {
      if (rect) {
        console.log(`Page ${pageIdx + 1}: Drawing Compatibility/Risk Matrix...`);
        const rows = [
          ["Astrological Influence", "Subconscious Shadows & Friction Points", "Empowered Remedies & Actions"]
        ];
        if (data.risk_matrix && data.risk_matrix.length > 0) {
          for (const item of data.risk_matrix) {
            rows.push(item);
          }
        } else {
          rows.push(["General friction", "Minor friction points in communication.", "Commit to open dialogue."]);
        }
        
        const colWidths = [125, 165, 165];
        const rowHeight = 24;
        const tableY = rect.y_top - 10;
        const finalTableY = drawTable(page, rect.x_left, tableY, colWidths, rowHeight, rows, bodyFont, boldFont);
        
        // Draw explanatory text below table
        const textBelow = stripEmojis(data.sections[19] || "");
        if (textBelow) {
          const wrapped = getWrappedLines(textBelow, rect.x_right - rect.x_left, fontSize, bodyFont);
          let txtY = finalTableY - 25;
          for (const line of wrapped) {
            if (line !== '') {
              page.drawText(line, {
                x: rect.x_left,
                y: txtY,
                size: fontSize,
                font: bodyFont,
                color: textColorDark
              });
            }
            txtY -= lineSpacing;
          }
        }
      }
      continue;
    }
    
    // Regular text pages
    if (!rect) {
      continue;
    }
    
    let linesToDraw = [];
    if (overflowLines[pageIdx]) {
      linesToDraw.push(...overflowLines[pageIdx]);
    }
    
    const pageText = stripEmojis(data.sections[pageIdx] || '');
    if (pageText) {
      const wrapped = getWrappedLines(pageText, rect.x_right - rect.x_left, fontSize, bodyFont);
      linesToDraw.push(...wrapped);
    }
    
    if (linesToDraw.length === 0) {
      continue;
    }
    
    console.log(`Page ${pageIdx + 1}: Writing ${linesToDraw.length} lines of text...`);
    let currentY = rect.y_top - fontSize;
    
    for (let i = 0; i < linesToDraw.length; i++) {
      const line = linesToDraw[i];
      
      // Page overflow check
      if (currentY < rect.y_bottom) {
        console.log(`Page ${pageIdx + 1} overflowed! Moving remaining lines to next page.`);
        const remainder = linesToDraw.slice(i);
        const nextPageIndex = pageIdx + 1;
        if (!overflowLines[nextPageIndex]) {
          overflowLines[nextPageIndex] = [];
        }
        overflowLines[nextPageIndex].push(...remainder);
        break;
      }
      
      if (line !== '') {
        page.drawText(line, {
          x: rect.x_left,
          y: currentY,
          size: fontSize,
          font: bodyFont,
          color: textColorDark
        });
      }
      currentY -= lineSpacing;
    }
  }

  console.log(`Saving compiled PDF to: ${args.output}`);
  const pdfBytes = await pdfDoc.save();
  fs.writeFileSync(args.output, pdfBytes);
  console.log("Success: Report successfully compiled!");
}

main().catch((err) => {
  console.error("Fatal compiler error:", err);
  process.exit(1);
});
