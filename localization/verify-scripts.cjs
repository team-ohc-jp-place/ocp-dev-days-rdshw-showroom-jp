// Parse generated inline browser scripts without executing workshop commands.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.dirname(__dirname);
const walk = (dir) => fs.readdirSync(dir, {withFileTypes:true}).flatMap(e => e.isDirectory() ? walk(path.join(dir,e.name)) : [path.join(dir,e.name)]);
let parsed=0, modules=0;
const errors=[];
for (const filename of walk(path.join(root,'www/ja/modules')).filter(p=>p.endsWith('.html'))) {
  for (const match of fs.readFileSync(filename,'utf8').matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/gi)) {
    if (/\bsrc\s*=/.test(match[1]) || /\btype\s*=\s*["']application\/json/.test(match[1])) continue;
    if (/\btype\s*=\s*["']module/.test(match[1])) {modules++;continue;}
    try {new vm.Script(match[2]);parsed++;}
    catch (error) {errors.push({page:path.relative(root,filename),message:error.message});}
  }
}
const report={inlineScriptsParsed:parsed,externalModuleScriptsSkipped:modules,errors};
fs.writeFileSync(path.join(root,'localization/script-verification.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
if(errors.length) process.exitCode=1;
