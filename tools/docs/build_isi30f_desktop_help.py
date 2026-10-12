"""Rebuild the owner-requested desktop edition from the accepted Help baseline.

Historical assets remain available as evidence; only contextual desktop figures
are referenced by active Help. Replacement sources are exact reviewed captures.
"""
from pathlib import Path
import hashlib
import json
import subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'automation/contracts/ISI-30F-DESKTOP-DOCUMENTATION.json'


def build():
    contract = json.loads(CONTRACT.read_text())
    data = json.loads(subprocess.check_output(
        ['git', 'show', contract['baseline'] + ':docs/help/ISI-ILLUSTRATED-MANUAL.json'],
        cwd=ROOT, text=True,
    ))
    screens = ROOT / 'docs/help/screens'
    for name, item in data['assets'].items():
        item['width'], item['height'] = Image.open(screens / name).size
        item['view'] = 'DESKTOP' if item['width'] >= 1200 else 'MOBILE'
    for name, item in contract['assets'].items():
        source = ROOT / item['source']
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['source_sha256']
        image = Image.open(source)
        assert list(image.size) == contract['viewport']
        image.convert('RGB').save(screens / name, quality=94)
        assert hashlib.sha256((screens / name).read_bytes()).hexdigest() == item['sha256']
        data['assets'][name] = {k: item[k] for k in ('caption','kind','captured','sha256','view','width','height')}
    for code, chapter in data['chapters'].items():
        chapter['screens'] = contract['chapters'][code]
        groups = chapter.get('screen_sections', {'4': chapter['screens'].copy()})
        groups = {key: [name for name in names if data['assets'][name]['view'] == 'DESKTOP'] for key,names in groups.items()}
        for name,item in contract['assets'].items():
            if item['chapter'] == code:
                group = groups.setdefault(item['section'], [])
                if name not in group:
                    group.append(name)
        chapter['screen_sections'] = {key: names for key,names in groups.items() if names}
        for section in chapter['sections']:
            if 'mobil' in section[0].lower():
                section[:] = ['Desktop prikaz i tastaturna navigacija',
                    'SIMPA i ORDO koriste se na desktop/laptop uređajima. Bočni meni omogućava izbor funkcije. Tab i Shift+Tab pomeraju fokus; Enter i Space aktiviraju odgovarajuću kontrolu. Za grafikon je dostupan tabelarni pregled izvornog rezultata.']
            else:
                section[1] = section[1].replace('Na telefonu otvorite bočni meni','Otvorite bočni meni').replace('mobile/keyboard','tastaturu').replace('telefonu','desktop uređaju')
    for topic in data['topics'].values():
        topic['screens'] = [name for name in topic['screens'] if data['assets'][name]['view'] == 'DESKTOP']
        if not topic['screens'] and topic.get('related_chapters'):
            topic['screens'] = data['chapters'][topic['related_chapters'][0]]['screens'][:2]
    data['topics']['SIMPA-H01']['screens'] = ['ISI-30F-desktop-simpa-profile-context.jpg']
    data['topics']['SIMPA-H02']['screens'] = ['ISI-30F-desktop-simpa-profile-form.jpg']
    old = 'ISI-30A-desktop-simpa.jpg'
    replacement = 'ISI-30F-desktop-simpa-profile-context.jpg'
    data['assets'][old]['view'] = 'ARCHIVED_SUPERSEDED_DESKTOP'
    for entry in [*data['topics'].values(), *data['chapters'].values()]:
        entry['screens'] = list(dict.fromkeys(replacement if n == old else n for n in entry['screens']))
        if 'screen_sections' in entry:
            entry['screen_sections'] = {k: list(dict.fromkeys(replacement if n == old else n for n in names))
                for k, names in entry['screen_sections'].items()}
    data['assets']['screenshots-simpa-profile.jpg']['view'] = 'ARCHIVED_CROPPED_DESKTOP'
    data['presentation'] = dict(authenticated_view='DESKTOP', minimum_capture_width=1200,
        new_capture_viewport=[1280,900], browser_zoom_percent=100, image_max_display_width=960,
        public_landing_mobile=True, legacy_mobile_assets='RETAINED_HISTORY_NOT_REFERENCED')
    (ROOT / 'docs/help/ISI-ILLUSTRATED-MANUAL.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    build()
