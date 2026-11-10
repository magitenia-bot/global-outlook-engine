#!/usr/bin/env python3
"""Conservative, offline Global Outlook dashboard. Standard library only.

Only explicit human-reviewed rows in validated_views.csv contribute to consensus.
Candidate documents are displayed separately, never interpreted as investment views.
"""
import argparse
import collections
import csv
import datetime as dt
import html
import json
from pathlib import Path
from urllib.parse import urlsplit

VIEW_FIELDS = ['institution_name','document_url','publication_date','frequency','asset_class','stance','reviewed_at_utc','reviewer','evidence_quote','previous_stance','previous_document_url']
STANCES = {'positive': 1, 'neutral': 0, 'negative': -1}
FREQUENCIES = {'weekly', 'monthly'}

def rows(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def safe(s): return html.escape(str(s or ''), quote=True)
def valid_url(s):
    p = urlsplit(s or '')
    return p.scheme == 'https' and bool(p.netloc) and not p.username and not p.password

def validate_view(r):
    if not all((r.get(k) or '').strip() for k in ('institution_name','document_url','publication_date','frequency','asset_class','stance','reviewed_at_utc','reviewer','evidence_quote')): return False
    if r['frequency'] not in FREQUENCIES or r['stance'] not in STANCES or not valid_url(r['document_url']): return False
    try:
        d = dt.date.fromisoformat(r['publication_date']); reviewed = dt.datetime.fromisoformat(r['reviewed_at_utc'].replace('Z','+00:00'))
        if reviewed.tzinfo is None or d > reviewed.date(): return False
    except ValueError: return False
    prev = (r.get('previous_stance') or '').strip()
    return (not prev or prev in STANCES) and (not r.get('previous_document_url') or valid_url(r['previous_document_url']))

def render(root):
    candidates = {f: rows(root / f'outlook_{f}_candidates.csv') for f in ('weekly','monthly','unclassified')}
    review_queue = rows(root / 'view_review_queue.csv')
    raw_views = rows(root / 'validated_views.csv')
    views = [r for r in raw_views if validate_view(r)]
    invalid = len(raw_views) - len(views)
    today = dt.datetime.now(dt.timezone.utc)
    all_sources = rows(root / 'sources.csv')
    source_institutions = {r.get('institution_name','').strip() for r in all_sources if r.get('institution_name','').strip()}
    if not source_institutions:
        source_institutions = {r.get('institution_name','').strip() for v in candidates.values() for r in v if r.get('institution_name','').strip()}
    institutions = {r['institution_name'] for r in views}
    # Multiple outlooks for same institution/asset/frequency: most recent wins.
    latest = {}
    for r in views:
        key = (r['frequency'],r['asset_class'],r['institution_name'])
        if key not in latest or (r['publication_date'],r['reviewed_at_utc']) > (latest[key]['publication_date'],latest[key]['reviewed_at_utc']): latest[key] = r
    by_asset = collections.defaultdict(list)
    for r in latest.values(): by_asset[(r['frequency'],r['asset_class'])].append(r)
    esc = safe
    style = '''body{margin:0;background:#f3f6fa;color:#14243a;font:15px system-ui,-apple-system,sans-serif}header{background:#0c2340;color:white;padding:30px max(20px,calc((100% - 1100px)/2))}main{max-width:1100px;margin:auto;padding:22px}h1{margin:0 0 7px}h2{margin-top:30px}p{line-height:1.5}.muted{color:#65758a}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.kpi,.panel{background:white;border:1px solid #dce3ec;border-radius:12px;padding:18px}.kpi strong{display:block;font-size:28px;margin:5px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white}th,td{border-bottom:1px solid #e5eaf0;padding:12px;text-align:left;vertical-align:top}th{background:#e9eef5}a{color:#0a568d;overflow-wrap:anywhere}.tag{border-radius:30px;padding:4px 10px;display:inline-block;font-size:12px;background:#e6eaf0}.pos{background:#daf4e5}.neu{background:#fff1c7}.neg{background:#ffe0df}.notice{border-left:4px solid #b57b00;padding:12px 16px;background:#fff8e6}details{margin:8px 0;background:white;padding:12px;border-radius:8px}footer{padding:28px;color:#65758a}'''
    out = ['<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Global Outlook 3.1</title><style>'+style+'</style></head><body>', '<header><h1>Global Investment Outlook 3.1</h1><div>Research Intelligence · Dashboard istituzionale</div><small>Generato '+esc(today.strftime('%Y-%m-%d %H:%M UTC'))+'</small></header><main>']
    out.append('<div class="notice"><b>Regola di validazione:</b> i documenti individuati automaticamente sono candidati, non view certificate. I semafori sono calcolati esclusivamente dalle righe approvate in <code>validated_views.csv</code>. I flussi finanziari non sono disponibili da queste fonti: n.d.</div>')
    kpis = [('Istituzioni censite',str(len(source_institutions)),'Da sources.csv'),('Gestori con view validate',str(len(institutions)),'Con evidenza e revisore'),('Copertura del censimento',f'{100*len(institutions)/len(source_institutions):.1f}%' if source_institutions else 'n.d.','Non è la copertura del mercato globale'),('Flussi netti','n.d.','Nessuna serie omogenea verificata')]
    out.append('<h2>Executive dashboard</h2><section class="kpis">'+''.join('<div class="kpi"><span class="muted">'+esc(k)+'</span><strong>'+esc(v)+'</strong><small>'+esc(note)+'</small></div>' for k,v,note in kpis)+'</section>')
    out.append('<h2>Consensus e matrici a semaforo</h2><p class="muted">Verde = positivo; giallo = neutrale; rosso = negativo. Le frecce compaiono soltanto quando è documentata anche una view precedente.</p>')
    for frequency in ('weekly','monthly'):
        out.append('<h3>'+('Settimanale' if frequency=='weekly' else 'Mensile')+'</h3>')
        keys = sorted(k for k in by_asset if k[0]==frequency)
        if not keys: out.append('<div class="panel">n.d. — Nessuna view validata disponibile per questa frequenza.</div>'); continue
        out.append('<div class="scroll"><table><thead><tr><th>Asset class</th><th>Gestori</th><th>Positivi</th><th>Neutrali</th><th>Negativi</th><th>Consensus</th></tr></thead><tbody>')
        for _, asset in keys:
            vs = by_asset[(frequency,asset)]; counts=collections.Counter(r['stance'] for r in vs)
            score=sum(STANCES[r['stance']] for r in vs)/len(vs)
            cls, label = ('pos','Positivo') if score>0 else ('neg','Negativo') if score<0 else ('neu','Neutrale')
            out.append('<tr><td>'+esc(asset)+'</td><td>'+str(len(vs))+'</td><td>'+str(counts['positive'])+'</td><td>'+str(counts['neutral'])+'</td><td>'+str(counts['negative'])+'</td><td><span class="tag '+cls+'">'+label+'</span></td></tr>')
        out.append('</tbody></table></div>')
    out.append('<h2>View documentate per gestore</h2>')
    if not latest: out.append('<div class="panel">n.d. — Nessuna view approvata. Nessun semaforo individuale viene inventato.</div>')
    else:
        out.append('<div class="scroll"><table><thead><tr><th>Gestore</th><th>Frequenza</th><th>Asset</th><th>View</th><th>Variazione</th><th>Fonte</th></tr></thead><tbody>')
        for r in sorted(latest.values(),key=lambda r:(r['institution_name'],r['frequency'],r['asset_class'])):
            previous = (r.get('previous_stance') or '').strip()
            arrow = '↑' if previous and STANCES[r['stance']]>STANCES[previous] else '↓' if previous and STANCES[r['stance']]<STANCES[previous] else '→' if previous else 'n.d.'
            out.append('<tr><td>'+esc(r['institution_name'])+'</td><td>'+esc(r['frequency'])+'</td><td>'+esc(r['asset_class'])+'</td><td><span class="tag '+{'positive':'pos','neutral':'neu','negative':'neg'}[r['stance']]+'">'+esc(r['stance'])+'</span></td><td>'+arrow+'</td><td><a rel="noopener noreferrer" href="'+esc(r['document_url'])+'">Outlook ufficiale</a><br><small>'+esc(r['publication_date'])+' · '+esc(r['reviewer'])+'</small><br><small>'+esc(r['evidence_quote'])+'</small></td></tr>')
        out.append('</tbody></table></div>')
    out.append('<h2>Investment View Engine — coda di revisione</h2><div class="panel"><b>'+str(len(review_queue))+' documenti in coda</b><p>Il sistema prepara una scheda per ciascun documento candidato. La lettura integrale, la verifica della citazione e l’approvazione della view richiedono revisione: nessuna posizione viene assegnata automaticamente.</p><p><code>view_review_queue.csv</code> contiene i collegamenti e i campi da completare; <code>validated_views.csv</code> è l’unica fonte per i semafori.</p></div>')
    out.append('<h2>Documenti candidati da verificare</h2><p class="muted">Le code seguenti non contribuiscono al consensus.</p>')
    for freq in ('weekly','monthly','unclassified'):
        rs = candidates[freq]
        out.append('<details><summary><b>'+esc({'weekly':'Settimanali','monthly':'Mensili','unclassified':'Non classificati'}[freq])+'</b> — '+str(len(rs))+' candidati</summary><div class="scroll"><table><thead><tr><th>Gestore</th><th>Titolo / collegamento</th><th>Data metadata</th><th>Stato</th></tr></thead><tbody>')
        for r in rs[:250]:
            url = r.get('final_url') or r.get('candidate_url') or ''
            title = esc((r.get('candidate_title') or 'Documento')[:180])
            link = '<a rel="noopener noreferrer" href="'+esc(url)+'">'+title+'</a>' if valid_url(url) else title
            out.append('<tr><td>'+esc(r.get('institution_name'))+'</td><td>'+link+'</td><td>'+esc(r.get('metadata_publication_date') or 'n.d.')+'</td><td>'+esc(r.get('selection_status'))+'</td></tr>')
        out.append('</tbody></table></div></details>')
    if invalid: out.append('<p class="notice">'+str(invalid)+' righe di view validate escluse per campi mancanti o formato errato.</p>')
    out.append('</main><footer>Global Outlook 3.1 · Dati di ricerca informativi, non raccomandazioni personalizzate.</footer></body></html>')
    (root/'global_outlook.html').write_text(''.join(out),encoding='utf-8')
    summary={'generated_at_utc':today.isoformat(),'institutions_in_sources':len(source_institutions),'institutions_with_validated_views':len(institutions),'validated_view_rows':len(views),'rejected_view_rows':invalid,'candidate_counts':{k:len(v) for k,v in candidates.items()},'view_review_queue_rows':len(review_queue),'flows':'n.d.'}
    (root/'report_status.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Dashboard generated:',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dir',default='.');args=p.parse_args();render(Path(args.dir))
