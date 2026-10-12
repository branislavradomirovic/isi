"""Read-only independent analyzer for the bounded desktop documentation revision."""
from pathlib import Path
import hashlib
import ast
import json
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
BASELINE = '29fd3be3ac879c641505458a6c3f0e3495e36cbc'
FILES = [
    'TECHNICAL_DOCUMENTATION.md','automation/STATUS.md','automation/tasks.json',
    'automation/specs/ISI-30F-FINAL-ACCEPTANCE-DEPLOYMENT.md',
    'automation/contracts/ISI-30F-DESKTOP-DOCUMENTATION.json',
    'docs/roadmap/ISI-AUTONOMOUS-INDUSTRIALIZATION-MASTER-PLAN.md',
    'docs/help/ISI-ILLUSTRATED-MANUAL.json','docs/help/ISI-HELP-COVERAGE-MATRIX.md',
    'docs/help/ISI-SHARED-USER-GUIDE.md','docs/help/ISI-WORKFLOW-SHELL-GUIDE.md','docs/help/ISI-30F-DESKTOP-MANUAL-ARTIFACT.json','docs/help/templates/ISI-MANUAL-TEMPLATE.docx',
    'src/streamlit_app/help_manual.py','src/streamlit_app/shared_help_workspace.py','src/streamlit_app/simpa_workspace.py','src/streamlit_app/ordo_workspace.py',
    'src/streamlit_app/simpa_help_workspace.py','src/streamlit_app/ordo_help_workspace.py',
    'tests/test_isi_10_contract.py','tests/test_isi_30e_illustrated_workflows.py',
    'tests/test_isi_30f_current_domain_copy.py','tests/test_isi_30f_desktop_help.py',
    'tools/docs/build_isi30f_desktop_help.py','tools/docs/build_isi30f_desktop_manual.py','tools/docs/index_isi30f_manual.py',
    'tools/qa/run_isi30f_desktop.py','tools/qa/analyze_isi30f_desktop.py',
]


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()


def manifest():
    assert git('branch','--show-current') == 'main'
    assert git('rev-parse','HEAD') == BASELINE == git('rev-parse','origin/main')
    assert not git('diff','--cached','--name-only') and not git('stash','list')
    assert git('worktree','list','--porcelain').count('worktree ') == 1
    contract=json.loads((ROOT/'automation/contracts/ISI-30F-DESKTOP-DOCUMENTATION.json').read_text())
    assert contract['baseline']==BASELINE
    assets=['docs/help/screens/'+name for name in contract['assets']]
    files=sorted(FILES+assets)
    actual=set(git('diff','--name-only').splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    assert actual==set(files), {'unexpected':sorted(actual-set(files)),'missing':sorted(set(files)-actual)}
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    fingerprint=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()
    return dict(baseline=BASELINE,files=hashes,fingerprint=fingerprint)


def verify_copy_only_runtime():
    class CopyMask(ast.NodeTransformer):
        def visit_Call(self, node):
            self.generic_visit(node)
            if (isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "st" and node.func.attr in {"markdown","caption","info","write"}
                    and node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str)):
                node.args[0].value = "<REVIEWED_UI_COPY>"
            return node
    for product in ("simpa", "ordo"):
        name = f"src/streamlit_app/{product}_workspace.py"
        baseline = git("show", BASELINE + ":" + name)
        current = (ROOT/name).read_text()
        before = ast.dump(CopyMask().visit(ast.parse(baseline)),include_attributes=False)
        after = ast.dump(CopyMask().visit(ast.parse(current)),include_attributes=False)
        assert before == after, "Domain runtime changes exceed approved UI copy surface"


def analyze():
    current=manifest()
    verify_copy_only_runtime()
    folder=ROOT/'automation/evidence/ISI-30F/desktop-docs'
    acceptance=json.loads((folder/'acceptance.json').read_text())
    assert acceptance['candidate']==current and acceptance['status']=='LOCAL_GATES_PASS'
    for gate in acceptance['gates']:
        assert gate['returncode']==0
        assert hashlib.sha256((folder/gate['log']).read_bytes()).hexdigest()==gate['sha256']
    for name,digest in acceptance['xml_sha256'].items():
        path=folder/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
        suites=ET.parse(path).getroot().findall('testsuite')
        assert suites and all(int(x.attrib['failures'])==0 and int(x.attrib['errors'])==0 for x in suites)
    data=json.loads((ROOT/'docs/help/ISI-ILLUSTRATED-MANUAL.json').read_text())
    for entry in [*data['topics'].values(),*data['chapters'].values()]:
        assert entry['screens']
        for name in entry['screens']:
            item=data['assets'][name]
            assert item['view']=='DESKTOP' and item['width']>=1200 and 'mobile' not in name.lower()
            assert hashlib.sha256((ROOT/'docs/help/screens'/name).read_bytes()).hexdigest()==item['sha256']
    artifact=json.loads((ROOT/'docs/help/ISI-30F-DESKTOP-MANUAL-ARTIFACT.json').read_text())
    review=json.loads((folder/'word-layout-review.json').read_text())
    assert review['status']=='PASS' and review['docx_sha256']==artifact['sha256']
    assert len(review['pages'])==artifact['page_count'] and artifact['index_page_numbers']
    assert hashlib.sha256((folder/artifact['filename']).read_bytes()).hexdigest()==artifact['sha256']
    return dict(status='REVIEW_VERIFIED',candidate=current,runtime_copy_ast_verified=True,ci_verified=False,server_verified=False)


if __name__=='__main__':
    print(json.dumps(analyze(),indent=2))
