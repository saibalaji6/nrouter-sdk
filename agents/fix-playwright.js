const fs = require('fs');
const path = require('path');

const agents = ['image-prompt-generator', 'video-prompt-generator', 'social-media-content-generator'];

agents.forEach(a => {
  const agentDir = path.join(__dirname, a);
  const globalSetup = path.join(agentDir, 'e2e', 'global-setup.ts');
  if (fs.existsSync(globalSetup)) {
    fs.unlinkSync(globalSetup);
  }

  const pwConfigPath = path.join(agentDir, 'playwright.config.ts');
  let pwConfig = fs.readFileSync(pwConfigPath, 'utf8');
  pwConfig = pwConfig.replace(/globalSetup: '.\/e2e\/global-setup.ts',/g, '');
  fs.writeFileSync(pwConfigPath, pwConfig);
});
