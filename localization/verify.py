#!/usr/bin/env python3
"""Compare the local English/Japanese source and complete generated HTML trees.

Run from the Japanese repository after npm run build:preview.
Uses Python's standard library; does not access external workshop services.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
import hashlib, json, re, subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT.parent / 'ocp-dev-days-rdshw-showroom'
JP = ROOT
REPORT = ROOT / 'localization' / 'verification.json'

@dataclass
class Node:
    tag: str
    attrs: dict = field(default_factory=dict)
    children: list = field(default_factory=list)
    def walk(self):
        yield self
        for c in self.children:
            if isinstance(c, Node): yield from c.walk()
    def text(self):
        return ''.join(c.text() if isinstance(c, Node) else c for c in self.children)
    def has_class(self, name):
        return name in self.attrs.get('class', '').split()

class Document(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.root = Node('root'); self.stack = [self.root]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        node=Node(tag,dict(attrs));self.stack[-1].children.append(node)
        if tag not in self.VOID: self.stack.append(node)
    def handle_startendtag(self,tag,attrs):
        self.stack[-1].children.append(Node(tag,dict(attrs)))
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:self.stack=self.stack[:i];break
    def handle_data(self,data):self.stack[-1].children.append(data)

def blocks(text):
    """Source/listing blocks and copyable sidebar payloads must remain exact."""
    result=[]; delimiter=None; current=[]; copypaste=False
    for line in text.splitlines():
        s=line.strip()
        if delimiter:
            if s==delimiter:
                result.append('\n'.join(current));delimiter=None;current=[]
            else:current.append(line)
        elif re.fullmatch(r'-{4,}|\.{4,}',s):delimiter=s
        elif s=='****' and copypaste:delimiter=s;copypaste=False
        elif s.startswith('['):copypaste=bool(re.search(r'\.(?:copypaste|datafetch)\b',s))
        elif s:copypaste=False
    return result

def references(text):
    return Counter(re.findall(r'(?:xref:|link:|include::|image::?)([^\s\[]+)',text))

def inline_codes(doc):
    article=next((n for n in doc.root.walk() if n.tag=='article' and n.has_class('doc')),doc.root)
    result=[]
    def visit(n, literal=False):
        literal=literal or n.tag in ('pre','script','style') or n.has_class('copypaste')
        if n.tag=='code' and not literal:result.append(n.text())
        for c in n.children:
            if isinstance(c,Node):visit(c,literal)
    visit(article)
    return Counter(result)

def broken_links(base, path, doc, docs):
    failures=set()
    for n in doc.root.walk():
        attr='src' if n.tag in ('img','script') else 'href' if n.tag in ('a','link') else None
        if not attr:continue
        value=n.attrs.get(attr,'')
        if not value or value=='#':continue
        u=urlsplit(value)
        if u.scheme or u.netloc:continue
        target=(base/unquote(u.path.lstrip('/')) if u.path.startswith('/') else path.parent/unquote(u.path)) if u.path else path
        target=target.resolve()
        if target.is_dir():target=target/'index.html'
        if not target.exists():failures.add((value,'missing file'));continue
        if u.fragment and target.suffix=='.html':
            other=docs.get(target)
            if other is None:other=Document(target.read_text());docs[target]=other
            ids={q.attrs.get('id') for q in other.root.walk()}
            ids.update(q.attrs.get('name') for q in other.root.walk() if q.tag=='a')
            if unquote(u.fragment) not in ids:failures.add((value,'missing fragment'))
    return failures

def main():
    errors=[]; source=[];html=[]; known=[]
    srcroot=EN/'content';dstroot=JP/'content'
    for p in sorted(srcroot.rglob('*.adoc')):
        if '/partials/' in str(p) or p.name=='nav.adoc':continue
        q=dstroot/p.relative_to(srcroot)
        if not q.exists():errors.append(f'Missing source: {q}');continue
        a=p.read_text();b=q.read_text()
        if blocks(a)!=blocks(b):errors.append(f'Changed literal/copy block: {p.relative_to(srcroot)}')
        if references(a)!=references(b):errors.append(f'Changed reference: {p.relative_to(srcroot)}')
        source.append(str(p.relative_to(srcroot)))
    enimgs={p.relative_to(srcroot) for p in srcroot.rglob('*') if p.is_file() and any(x in ('image','images') for x in p.parts)}
    for rel in enimgs:
        if not (dstroot/rel).exists() or hashlib.sha256((srcroot/rel).read_bytes()).digest()!=hashlib.sha256((dstroot/rel).read_bytes()).digest():errors.append(f'Image bytes differ: {rel}')
    for folder in ['attachments','examples']:
        for p in (srcroot/'modules/ROOT'/folder).rglob('*'):
            if p.is_file() and p.read_bytes()!=(dstroot/p.relative_to(srcroot)).read_bytes():errors.append(f'Changed payload: {p}')
    bases={lang:ROOT/'www'/lang for lang in ('en','ja')}
    for lang,base in bases.items():
        if not (base/'modules/index.html').exists():
            raise SystemExit(f'Missing generated site: {base}. Run npm run build:preview first.')
    docs={lang:{p.resolve():Document(p.read_text()) for p in base.rglob('*.html')} for lang,base in bases.items()}
    for p,d in sorted(docs['en'].items()):
        rel=p.relative_to(bases['en']);q=(bases['ja']/rel).resolve()
        if q not in docs['ja']:errors.append(f'Missing HTML: {rel}');continue
        j=docs['ja'][q]
        ea=next((n for n in d.root.walk() if n.tag=='article' and n.has_class('doc')),None)
        ja=next((n for n in j.root.walk() if n.tag=='article' and n.has_class('doc')),None)
        if not ea or not ja:continue
        be=broken_links(bases['en'],p,d,docs['en']);bj=broken_links(bases['ja'],q,j,docs['ja'])
        if bj-be:errors.append(f'New broken links: {rel}: {sorted(bj-be)}')
        if be:known.append({'page':str(rel),'links':[list(x) for x in sorted(be)]})
        ec=inline_codes(d);jc=inline_codes(j)
        if ec!=jc:html.append({'page':str(rel),'inline_code_removed':list((ec-jc).elements()),'inline_code_added':list((jc-ec).elements())})
        for tag in ('strong','em'):
            ne=sum(n.tag==tag for n in ea.walk());nj=sum(n.tag==tag for n in ja.walk())
            if ne!=nj:html.append({'page':str(rel),'tag':tag,'en':ne,'ja':nj})
        # Compare actual hyperlink destinations, keeping navigation and body links.
        for scope_en,scope_ja,scope in [(ea,ja,'article'),(d.root,j.root,'document')]:
            refs=lambda root:Counter(n.attrs['href'] for n in root.walk() if n.tag=='a' and 'href' in n.attrs)
            er=refs(scope_en);jr=refs(scope_ja)
            if er!=jr:html.append({'page':str(rel),'scope':scope,'href_removed':list((er-jr).elements()),'href_added':list((jr-er).elements())})
    reviewed=[]
    for item in html[:]:
        if item == {'page': 'modules/module-05/module-05-03-configure-mta-extension.html', 'inline_code_removed': ['quarkus-profile`', 'quarkus, `quarkus3+, `jakarta-ee`', ', `quarkus3+'], 'inline_code_added': ['quarkus-profile', 'quarkus', 'quarkus3+', 'jakarta-ee']}:
            reviewed.append({**item, 'reason': 'Corrected extra backticks already present in the English source; profile and technology values are unchanged.'})
            html.remove(item)
    for item in html: errors.append('Unreviewed HTML formatting/link difference: '+str(item))
    theme_files=list((ROOT/'.cache/antora/ui').glob('*.zip'))
    theme_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in theme_files}
    report={'reviewed_formatting_fixes':reviewed,'theme_sha256':theme_hashes,'source_commit':subprocess.check_output(['git','-C',str(EN),'rev-parse','HEAD'],text=True).strip(),'source_pages_checked':len(source),'images_checked':len(enimgs),'html_pages_checked':len([p for p in docs['en'] if '/modules/' in str(p) and '/_images/' not in str(p)]),'errors':errors,'formatting_and_link_differences_to_review':html,'upstream_broken_links':known}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v if not isinstance(v,list) else len(v) for k,v in report.items()},ensure_ascii=False,indent=2))
    return 1 if errors else 0

if __name__=='__main__':raise SystemExit(main())
