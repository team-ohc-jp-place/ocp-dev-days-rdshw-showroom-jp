import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { spawnSync } from 'node:child_process';
const require = createRequire(import.meta.url);
const yaml = require('js-yaml');
const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const cache = path.join(root, '.cache', 'localization');
fs.mkdirSync(cache, { recursive: true });
for (const lang of ['en', 'ja']) {
  const config = yaml.load(fs.readFileSync(path.join(root, 'localization', `playbook-${lang}.yml`), 'utf8'));
  for (const source of config.content.sources) source.url = path.resolve(root, source.url);
  for (const extension of config.antora.extensions) {
    if (extension.require.startsWith('./')) extension.require = path.resolve(root, extension.require);
  }
  config.output.dir = path.join(root, 'www', lang);
  if (config.ui.supplemental_files) config.ui.supplemental_files = path.join(root, 'ui-supplemental');
  const filename = path.join(cache, `playbook-${lang}.yml`);
  fs.writeFileSync(filename, yaml.dump(config));
  const result = spawnSync(process.execPath, [path.join(root, 'node_modules/@antora/cli/bin/antora'), '--cache-dir', path.join(root, '.cache/antora'), filename], { cwd: root, stdio: 'inherit' });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
