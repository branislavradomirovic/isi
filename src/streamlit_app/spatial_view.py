"""Bounded spatial read model and tile-free accessible SVG component."""

from __future__ import annotations
import hashlib
import json
import math
from src.platform.spatial.contracts import validate_geometry, GeometryError

MAX_FEATURES = 25
MAX_MAP_BYTES = 1_000_000
MAX_MAP_COORDINATES = 50_000
COLORS = {"Point": [153, 86, 15, 200], "Polygon": [26, 95, 139, 100], "MultiPolygon": [26, 95, 139, 100]}


def coordinates(value):
    if len(value) == 2 and all(isinstance(x, (int, float)) for x in value):
        yield value
    else:
        for child in value:
            yield from coordinates(child)


def collection(details):
    if len(details) > MAX_FEATURES:
        raise GeometryError("map_feature_limit")
    features, ids, total_bytes, total_coordinates = [], set(), 0, 0
    for item in details:
        row, geometry = item["metadata"], item["geometry"]
        if row["state"] != "VALIDATED" or row["id"] in ids:
            raise GeometryError("map_unvalidated_or_duplicate")
        ids.add(row["id"])
        total_bytes += len(validate_geometry(geometry))
        total_coordinates += sum(1 for _ in coordinates(geometry["coordinates"]))
        if total_bytes > MAX_MAP_BYTES or total_coordinates > MAX_MAP_COORDINATES:
            raise GeometryError("map_payload_limit")
        label = str(row["domain_binding"]["key"])[:160] + " · " + str(row["version"])[:120]
        features.append(
            {
                "type": "Feature",
                "id": row["id"],
                "geometry": geometry,
                "properties": {"id": row["id"], "label": label, "color": COLORS[geometry["type"]]},
            }
        )
    return {"type": "FeatureCollection", "features": features}


def selection_id(indices, ids):
    if not isinstance(indices, list) or len(indices) != 1:
        return None
    index = indices[0]
    return ids[index] if isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(ids) else None


def map_key(scope, at_date, details):
    # Scope/date/revisions and geometry fingerprints prevent stale selection reuse.
    identity = [
        scope,
        str(at_date),
        [(x["metadata"]["id"], x["metadata"]["fingerprint"], x["metadata"]["revision"]) for x in details],
    ]
    return "gis-" + hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()


def build_map(data, selected=None):
    points = [p for feature in data["features"] for p in coordinates(feature["geometry"]["coordinates"])]
    if not points or any(abs(p[1]) >= 90 for p in points):
        raise GeometryError("map_projection_unavailable_use_table")

    def mercator(point):
        return math.radians(point[0]), math.log(math.tan(math.pi / 4 + math.radians(point[1]) / 2))

    projected = [mercator(p) for p in points]
    lo_x, hi_x = min(p[0] for p in projected), max(p[0] for p in projected)
    lo_y, hi_y = min(p[1] for p in projected), max(p[1] for p in projected)
    span_x, span_y = max(hi_x - lo_x, 0.0001), max(hi_y - lo_y, 0.0001)
    scale = min(720 / span_x, 320 / span_y)
    mid_x, mid_y = (lo_x + hi_x) / 2, (lo_y + hi_y) / 2

    def xy(point):
        x, y = mercator(point)
        return [round(400 + (x - mid_x) * scale, 4), round(200 - (y - mid_y) * scale, 4)]

    result = []
    for feature in data["features"]:
        geometry = feature["geometry"]
        item = {
            "id": feature["id"],
            "label": feature["properties"]["label"],
            "selected": feature["id"] == selected,
            "point": geometry["type"] == "Point",
        }
        if item["point"]:
            item["position"] = xy(geometry["coordinates"])
        else:
            parts = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            paths = []
            for polygon in parts:
                path = []
                for ring in polygon:
                    pts = [xy(p) for p in ring]
                    path.append("M" + " L".join(f"{x},{y}" for x, y in pts) + " Z")
                paths.append(" ".join(path))
            item["paths"] = paths
        result.append(item)
    return {"features": result, "projection": "WGS84_RENDER_MERCATOR", "source_geometry_unchanged": True}


MAP_HTML = '<div class="isi-vector-map"></div>'
MAP_CSS = """
.isi-vector-map {width:100%; font-family:inherit; color:inherit;}
.controls {display:flex; flex-wrap:wrap; gap:6px; margin-bottom:8px;}
button {font:inherit; border:1px solid #46677b; border-radius:5px; background:#f4f8fa; color:#173e65; padding:5px 10px;}
svg {width:100%; height:360px; background:#f3f7fa; border:1px solid #9aabb8; touch-action:none;}
[role=button]:focus {outline:none; stroke:#b3256b; stroke-width:4;}
"""
MAP_JS = r"""
export default function({parentElement, data, setTriggerValue}) {
    const root = parentElement.querySelector('.isi-vector-map');
    const old = root.querySelector('svg');
    const saved = old && root.dataset.key === data.dataset ? old.getAttribute('viewBox') : '0 0 800 400';
    root.replaceChildren(); root.dataset.key = data.dataset;
    const controls = document.createElement('div'); controls.className='controls'; root.appendChild(controls);
    const ns='http://www.w3.org/2000/svg';
    const svg=document.createElementNS(ns,'svg'); svg.setAttribute('viewBox',saved);
    svg.setAttribute('role','group'); svg.setAttribute('aria-label','GIS karta potvrđenih geometrija');
    function adjust(action) {
        let [x,y,w,h]=svg.getAttribute('viewBox').split(' ').map(Number);
        if(action==='reset'){ x=0; y=0; w=800; h=400; }
        else if(action==='in' && w>25){ x+=w/8; y+=h/8; w*=.75; h*=.75; }
        else if(action==='out' && w<6400){ x-=w/6; y-=h/6; w*=4/3; h*=4/3; }
        else if(action==='left') x-=w/5;
        else if(action==='right') x+=w/5;
        else if(action==='up') y-=h/5;
        else if(action==='down') y+=h/5;
        svg.setAttribute('viewBox',[x,y,w,h].join(' '));
    }
    for(const [label, action] of [['Uvećaj','in'],['Umanji','out'],['Levo','left'],['Desno','right'],['Gore','up'],['Dole','down'],['Vrati prikaz','reset']]) {
        const b=document.createElement('button'); b.type='button'; b.textContent=label; b.setAttribute('aria-label',label+' kartu');
        b.onclick=()=>adjust(action); controls.appendChild(b);
    }
    for(const item of data.features) {
        const group=document.createElementNS(ns,'g');
        group.setAttribute('role','button'); group.setAttribute('tabindex','0');
        group.setAttribute('aria-label','Izaberi '+item.label); group.setAttribute('aria-pressed',String(item.selected));
        const title=document.createElementNS(ns,'title'); title.textContent=item.label; group.appendChild(title);
        group.setAttribute('fill',item.point?'#99560f':'#a3c5d9');
        group.setAttribute('stroke',item.selected?'#992d5f':'#1a415f');
        group.setAttribute('stroke-width',item.selected?'4':'2');
        if(item.point) {
            const hit=document.createElementNS(ns,'circle'); hit.setAttribute('cx',String(item.position[0]));
            hit.setAttribute('cy',String(item.position[1])); hit.setAttribute('r','8');
            hit.setAttribute('fill','transparent'); hit.setAttribute('stroke','transparent');
            hit.setAttribute('stroke-width','24'); hit.setAttribute('vector-effect','non-scaling-stroke');
            group.appendChild(hit);
            const c=document.createElementNS(ns,'circle'); c.setAttribute('cx',String(item.position[0]));
            c.setAttribute('cy',String(item.position[1])); c.setAttribute('r','8'); c.setAttribute('vector-effect','non-scaling-stroke'); group.appendChild(c);
        } else {
            for(const value of item.paths) {
                const path=document.createElementNS(ns,'path'); path.setAttribute('d',value);
                path.setAttribute('fill-rule','evenodd'); group.appendChild(path);
            }
        }
        group.onclick=()=>setTriggerValue('picked',item.id);
        group.onkeydown=(event)=>{ if(event.key==='Enter'||event.key===' '){event.preventDefault();setTriggerValue('picked',item.id);} };
        svg.appendChild(group);
    }
    let drag=null;
    svg.onpointerdown=(e)=>{if(e.target.closest('[role=button]'))return;
        drag=[e.clientX,e.clientY,svg.getAttribute('viewBox').split(' ').map(Number)];svg.setPointerCapture(e.pointerId);};
    svg.onpointermove=(e)=>{if(!drag)return;const rect=svg.getBoundingClientRect();const [sx,sy,[x,y,w,h]]=drag;
        const ratio=Math.min(rect.width/w,rect.height/h);
        svg.setAttribute('viewBox',[x-(e.clientX-sx)/ratio,y-(e.clientY-sy)/ratio,w,h].join(' '));};
    svg.onpointerup=()=>{drag=null;}; svg.onpointercancel=()=>{drag=null;};
    root.appendChild(svg);
}
"""


def map_component():
    # Only trusted static code is registered. Scope/geometry travel as data, never HTML/JS.
    import streamlit as st

    return _registered_component(st.components.v2.component)


from functools import lru_cache  # noqa: E402


@lru_cache(maxsize=1)
def _registered_component(register):
    return register("isi_spatial_vector_v1", html=MAP_HTML, css=MAP_CSS, js=MAP_JS)
