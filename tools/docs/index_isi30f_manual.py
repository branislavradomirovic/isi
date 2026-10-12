"""Derive/check deterministic printed index pages from the rendered Word outline.
Run with the bundled document runtime; no product runtime dependency is added.
"""
from pathlib import Path
import argparse
import json
import re
import hashlib
import zipfile
from lxml import etree
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
FOLDER = ROOT / 'automation/evidence/ISI-30F/desktop-docs'


def normalize(text):
    return re.sub(r'\s+', ' ', text).strip()


def inspect(render_folder):
    author = json.loads((FOLDER/'manual-authoring.json').read_text())
    pdf = render_folder/'ISI_prirucnik_desktop.pdf'
    reader = PdfReader(pdf)
    outline=[]
    def walk(items,depth=0):
        for item in items:
            if isinstance(item,list):
                walk(item,depth+1)
            elif depth<=1 and item['/Title']!='Sadržaj i indeks':
                outline.append((normalize(item['/Title']),reader.get_destination_page_number(item)+1))
    walk(reader.outline)
    entries=author['navigation']
    assert len(outline)==len(entries),(len(outline),len(entries))
    pages={}
    for entry,(title,page) in zip(entries,outline):
        assert normalize(entry['title'])==title,(entry['title'],title)
        pages[entry['anchor']]=page
    docx=FOLDER/author['filename']
    with zipfile.ZipFile(docx) as archive:
        tree=etree.fromstring(archive.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    bookmarks=tree.xpath('//w:bookmarkStart/@w:name',namespaces=ns)
    links=tree.xpath('//w:hyperlink/@w:anchor',namespaces=ns)
    assert len(set(bookmarks))==len(bookmarks)
    assert set(links)<=set(bookmarks) and len(links)==2*len(entries)
    return pages,dict(page_count=len(reader.pages),index_entries=len(entries),
        internal_links=len(links),docx_sha256=hashlib.sha256(docx.read_bytes()).hexdigest(),
        pdf_sha256=hashlib.sha256(pdf.read_bytes()).hexdigest())


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--check',action='store_true')
    parser.add_argument('--render-dir',type=Path,default=FOLDER/'render-final')
    args=parser.parse_args()
    pages,receipt=inspect(args.render_dir)
    path=FOLDER/'index-pages.json'
    if args.check:
        assert json.loads(path.read_text())==pages,'Printed index changed; rebuild and render again.'
        receipt['status']='PASS'
        (FOLDER/'index-check.json').write_text(json.dumps(receipt,indent=2)+'\n')
    else:
        path.write_text(json.dumps(pages,indent=2)+'\n')
    print(json.dumps(receipt))
