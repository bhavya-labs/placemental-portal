const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

async function run() {
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const tmpDir = path.join(process.env.TEMP || '.', 'edge_faculty_' + Date.now());
  fs.mkdirSync(tmpDir, { recursive: true });

  const port = 9444;
  console.log(`Launching Edge on port ${port}...`);
  const edgeProc = spawn(edgePath, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${tmpDir}`,
    '--disable-gpu',
    '--no-first-run',
    '--window-size=1534,1200',
    'http://localhost:5173/login'
  ]);

  let version = null;
  for (let i = 0; i < 20; i++) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) {
        version = await res.json();
        break;
      }
    } catch (e) {
      await new Promise(r => setTimeout(r, 500));
    }
  }

  if (!version) {
    console.error('Failed to connect to Edge DevTools');
    process.exit(1);
  }

  console.log('Connected to Edge:', version.Browser);

  const pagesRes = await fetch(`http://127.0.0.1:${port}/json/list`);
  const pages = await pagesRes.json();
  const pageWsUrl = pages[0].webSocketDebuggerUrl;

  const ws = new WebSocket(pageWsUrl);
  let id = 1;
  const callbacks = new Map();

  function send(method, params = {}) {
    return new Promise((resolve, reject) => {
      const msgId = id++;
      callbacks.set(msgId, { resolve, reject });
      ws.send(JSON.stringify({ id: msgId, method, params }));
    });
  }

  const consoleLogs = [];
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.id && callbacks.has(data.id)) {
      const { resolve, reject } = callbacks.get(data.id);
      callbacks.delete(data.id);
      if (data.error) reject(data.error);
      else resolve(data.result);
    } else if (data.method === 'Runtime.consoleAPICalled') {
      const text = data.params.args.map(a => a.value || JSON.stringify(a)).join(' ');
      consoleLogs.push(`[${data.params.type}] ${text}`);
    } else if (data.method === 'Runtime.exceptionThrown') {
      consoleLogs.push(`[EXCEPTION] ${data.params.exceptionDetails.text} ${data.params.exceptionDetails.exception?.description || ''}`);
    }
  };

  await new Promise(r => ws.onopen = r);
  await send('Page.enable');
  await send('Runtime.enable');

  console.log('Waiting for login page to load...');
  await new Promise(r => setTimeout(r, 2000));

  console.log('Submitting login form as faculty.cse@platform.edu...');
  const submitResult = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const emailInput = document.querySelector('input[type="email"]') || document.querySelector('input[name="email"]') || document.querySelectorAll('input')[0];
        const passInput = document.querySelector('input[type="password"]') || document.querySelectorAll('input')[1];
        const submitBtn = document.querySelector('button[type="submit"]') || document.querySelector('form button');
        
        if (!emailInput || !passInput) {
          return { error: 'Inputs not found', inputs: document.querySelectorAll('input').length, html: document.body.innerHTML.slice(0, 500) };
        }
        
        // Native setter simulation for React controlled inputs
        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeInputValueSetter.call(emailInput, 'faculty.cse@platform.edu');
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));

        nativeInputValueSetter.call(passInput, 'password123');
        passInput.dispatchEvent(new Event('input', { bubbles: true }));
        passInput.dispatchEvent(new Event('change', { bubbles: true }));

        submitBtn.click();
        return { success: true };
      })()
    `,
    returnByValue: true
  });
  console.log('Form submission result:', submitResult.result.value);

  // Wait for login and navigation to faculty dashboard
  console.log('Waiting 5 seconds for dashboard navigation and chart rendering...');
  await new Promise(r => setTimeout(r, 5000));

  // Inspect current page state
  const pageState = await send('Runtime.evaluate', {
    expression: `
      (() => {
        const url = window.location.href;
        const text = document.body.innerText;
        const cards = Array.from(document.querySelectorAll('.gov-card')).map(c => c.innerText.replace(/\\n+/g, ' '));
        const svgs = Array.from(document.querySelectorAll('svg')).map(s => ({
          tag: s.tagName,
          width: s.clientWidth,
          height: s.clientHeight,
          className: s.getAttribute('class'),
          hasChildren: s.children.length
        }));
        const rechartsElements = {
          containers: document.querySelectorAll('.recharts-responsive-container').length,
          bars: document.querySelectorAll('.recharts-bar').length,
          lines: document.querySelectorAll('.recharts-line').length,
          pies: document.querySelectorAll('.recharts-pie').length,
          tooltips: document.querySelectorAll('.recharts-tooltip-wrapper').length,
          barRectangles: document.querySelectorAll('.recharts-bar-rectangle').length
        };
        const headings = Array.from(document.querySelectorAll('h1, h2, h3, h4')).map(h => h.innerText);
        return {
          url,
          headings,
          cardsCount: cards.length,
          cardsSample: cards.slice(0, 6),
          svgsCount: svgs.length,
          svgs: svgs.slice(0, 10),
          rechartsElements,
          hasOverallPlacement: text.includes('Overall Placement Percentage') || text.includes('3.7%'),
          hasHighestPackage: text.includes('Highest Package Offered') || text.includes('8.5 LPA'),
          hasBranchChart: text.includes('Branch-wise Placement %') || text.includes('Placement Rate'),
          hasTimelineChart: text.includes('Monthly Placement Timeline'),
          hasGenderChart: text.includes('Gender Placement Ratios'),
          hasFunnelChart: text.includes('Recruitment Pipeline Funnel')
        };
      })()
    `,
    returnByValue: true
  });

  console.log('\n======================================================');
  console.log('FACULTY DASHBOARD LIVE BROWSER INSPECTION');
  console.log('======================================================');
  console.log(JSON.stringify(pageState.result.value, null, 2));

  console.log('\n--- BROWSER CONSOLE LOGS ---');
  if (consoleLogs.length === 0) {
    console.log('ZERO console errors or warnings.');
  } else {
    console.log(consoleLogs.join('\n'));
  }

  // Save screenshot
  const screenshot = await send('Page.captureScreenshot', { format: 'png' });
  const outPath = 'd:/placement portal/scratch/faculty_dashboard_live_verified.png';
  fs.writeFileSync(outPath, Buffer.from(screenshot.data, 'base64'));
  console.log('\nScreenshot successfully saved to:', outPath);

  ws.close();
  try {
    process.kill(edgeProc.pid);
  } catch (e) {}
  process.exit(0);
}

run().catch(err => {
  console.error('Script failed:', err);
  process.exit(1);
});
