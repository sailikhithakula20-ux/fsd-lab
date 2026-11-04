const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

// Locate Python executable (.venv in current, parent, grandparent, or system python)
const venvCandidates = [
  path.join(__dirname, '.venv', 'Scripts', 'python.exe'),
  path.join(__dirname, '..', '.venv', 'Scripts', 'python.exe'),
  path.join(__dirname, '..', '..', '.venv', 'Scripts', 'python.exe')
];
const venvPython = venvCandidates.find(p => fs.existsSync(p));
const pythonCmd = venvPython || 'python';

// Locate app.py
const candidatePaths = [
  path.join(__dirname, 'app.py'),
  path.join(__dirname, 'preventive-health-portal.zip', 'preventive-health-portal', 'app.py'),
  path.join(__dirname, 'preventive-health-portal', 'app.py')
];

const appPath = candidatePaths.find(p => fs.existsSync(p));

if (!appPath) {
  console.error('Error: Could not find app.py in the project directory.');
  process.exit(1);
}

const appDir = path.dirname(appPath);

console.log(`> Starting Preventive Health Portal on http://127.0.0.1:5000`);
console.log(`> Working directory: ${appDir}`);
console.log(`> Using Python: ${pythonCmd}`);

const child = spawn(pythonCmd, ['app.py'], {
  cwd: appDir,
  stdio: 'inherit',
  shell: false,
  env: {
    ...process.env,
    FLASK_DEBUG: '1'
  }
});

child.on('exit', (code) => {
  process.exit(code !== null ? code : 0);
});
