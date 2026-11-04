// Runs every website test script at once, a few at a time, instead of one after another.
// They only read the same built site (the preview server), so they do not affect each other.
// EITR_TEST_JOBS sets how many run together (default 4: the browser tests are timing-sensitive).
import { spawn } from 'node:child_process';
import { readFileSync } from 'node:fs';

const all = Object.keys(JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8')).scripts)
  .filter(name => name.startsWith('test:'));
// Accessibility measures colours right after hover animations; on a busy machine it can
// catch a colour mid-fade, so it runs alone after the others.
const alone = ['test:a11y'];
const scripts = all.filter(name => !alone.includes(name));
const jobs = Math.max(1, Number(process.env.EITR_TEST_JOBS) || 4);
const failed = [];
let next = 0;

function run(name) {
  return new Promise(resolve => {
    const started = Date.now();
    const child = spawn('npm', ['run', '--silent', name], { stdio: ['ignore', 'pipe', 'pipe'] });
    let output = '';
    child.stdout.on('data', chunk => { output += chunk; });
    child.stderr.on('data', chunk => { output += chunk; });
    child.on('close', code => {
      const seconds = ((Date.now() - started) / 1000).toFixed(0);
      if (code === 0) console.log(`  PASS  ${name} (${seconds}s)`);
      else {
        failed.push(name);
        console.log(`  FAIL  ${name} (${seconds}s)\n${output.trimEnd().split('\n').map(line => `        ${line}`).join('\n')}`);
      }
      resolve();
    });
  });
}

async function worker() {
  while (next < scripts.length) await run(scripts[next++]);
}

await Promise.all(Array.from({ length: Math.min(jobs, scripts.length) }, worker));
for (const name of alone.filter(name => all.includes(name))) await run(name);
if (failed.length) {
  console.log(`Failed: ${failed.join(', ')}`);
  process.exit(1);
}
console.log(`All ${all.length} test scripts passed.`);
