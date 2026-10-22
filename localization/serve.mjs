// Different ports give English and Japanese independent workshop progress storage.
import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const children=[];
for(const [lang,port] of [['ja',8080],['en',8081]]) {
  const child=spawn('python3',['-m','http.server',String(port),'--bind','127.0.0.1','--directory',path.join(root,'www')],{stdio:'inherit'});
  children.push(child);
  child.on('error',error=>{console.error(error.message);for(const other of children)other.kill();process.exitCode=1;});
  child.on('exit',code=>{if(code){for(const other of children)other.kill();process.exitCode=code;}});
  console.log(`${lang}: http://127.0.0.1:${port}/${lang}/modules/index.html`);
}
for(const signal of ['SIGINT','SIGTERM'])process.on(signal,()=>{for(const child of children)child.kill(signal);});
