import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { generateImagePrompt } from '../dist/agent.js';

const apiKey = process.env.NROUTER_API_KEY;
const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 4174;

const server = http.createServer(async (req, res) => {
  const host = req.headers.host || '127.0.0.1';
  const parsedUrl = new URL(req.url || '/', `http://${host}`);
  const { pathname } = parsedUrl;

  if (req.method === 'GET' && pathname === '/healthz') {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('ok');
    return;
  }

  if (req.method === 'GET' && pathname === '/') {
    const indexPath = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'index.html');
    const html = await fs.promises.readFile(indexPath, 'utf-8');
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(html);
    return;
  }

  if (req.method === 'POST' && pathname === '/api/generate') {
    let rawBody = '';
    req.on('data', chunk => rawBody += chunk);
    req.on('end', async () => {
      try {
        const body = JSON.parse(rawBody);
        const result = await generateImagePrompt({
          apiKey,
          query: body.query,
          ...{}
        });
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ result }));
      } catch (err) {
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }
  res.writeHead(404);
  res.end();
});

const host = process.env.HOST || '127.0.0.1';
server.listen(port, host, () => {
  console.log(`Demo server listening on http://${host}:${port}`);
});