#!/usr/bin/env python3
"""Conservative, offline Global Outlook dashboard. Standard library only.

Only directly checked structured views enter operational matrices; source host or access errors do not automatically exclude them.
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
FREQUENCIES = {'weekly', 'monthly', 'quarterly', 'strategic', 'unclassified', ''}

def rows(path):
    if not path.exists(): return []
    with path.open(encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))

def safe(s): return html.escape(str(s or ''), quote=True)
def valid_url(s):
    p = urlsplit(s or '')
    return p.scheme == 'https' and bool(p.netloc) and not p.username and not p.password

def validate_view(r):
    if not all((r.get(k) or '').strip() for k in ('asset_class','stance','reviewed_at_utc','evidence_quote')): return False
    if r['frequency'] not in FREQUENCIES or r['stance'] not in STANCES: return False
    try:
        raw_date = (r.get('publication_date') or '').strip()
        if len(raw_date) == 4 and raw_date.isdigit(): normalized_date = raw_date + '-01-01'
        elif len(raw_date) == 7 and raw_date[4] == '-': normalized_date = raw_date + '-01'
        else: normalized_date = raw_date
        d = dt.date.fromisoformat(normalized_date)
        reviewed = dt.datetime.fromisoformat(r['reviewed_at_utc'].replace('Z','+00:00'))
        if reviewed.tzinfo is None or d > reviewed.date(): return False
    except ValueError: return False
    prev = (r.get('previous_stance') or '').strip()
    return (not prev or prev in STANCES) and (not r.get('previous_document_url') or valid_url(r['previous_document_url']))

def render(root):
    candidates = {f: rows(root / f'outlook_{f}_candidates.csv') for f in ('weekly','monthly','quarterly','strategic','unclassified')}
    review_queue = rows(root / 'view_review_queue.csv')
    evidence = rows(root / 'document_evidence.csv')
    readable_evidence = [r for r in evidence if r.get('fetch_status') in ('html_read','pdf_read') and r.get('text_excerpt') and any(q.get('document_url') == r.get('document_url') for q in review_queue)]
    source_registry = rows(root / 'outlook_source_registry.csv')
    today_date = dt.datetime.now(dt.timezone.utc).date()
    from select_outlooks_v21 import cutoff
    start_date = cutoff(today_date)
    reassessed = rows(root / 'view_reassessment_latest.csv')
    stance_types = {(r.get('institution_name'), r.get('document_url'), r.get('asset_class')): r.get('position_type', 'n.d.') for r in reassessed}
    raw_views = rows(root / 'validated_views.csv')
    admissible = [r for r in raw_views if validate_view(r)]
    # No human-review gate. Only explicit completed ChatGPT document verification
    # is eligible for operational matrices; legacy AI summaries stay preliminary.
    # Evidence is attributed to AI verification, never independent human review.
    # Preserve all AI-reviewed entries as exploratory, regardless of source host.
    def ai_provisional(r):
        reviewer = (r.get('reviewer') or '').lower()
        return 'chatgpt' in reviewer or 'assistita da ia' in reviewer
    views = [r for r in admissible if (r.get('reviewer') or '').strip().lower() == 'chatgpt - verifica documentale completata']
    provisional = [r for r in admissible if r not in views]
    source_admitted = views
    invalid = len(raw_views) - len(admissible)
    today = dt.datetime.now(dt.timezone.utc)
    all_sources = rows(root / 'sources.csv')
    source_institutions = {r.get('institution_name','').strip() for r in all_sources if r.get('institution_name','').strip()}
    source_institutions.update(r.get('institution_name','').strip() for v in candidates.values() for r in v if r.get('institution_name','').strip())
    source_institutions.update(r.get('institution_name','').strip() for r in raw_views if r.get('institution_name','').strip())
    if not source_institutions:
        source_institutions = {r.get('institution_name','').strip() for v in candidates.values() for r in v if r.get('institution_name','').strip()}
    institutions = {r['institution_name'] for r in views}
    missing_view_institutions = sorted(source_institutions - institutions)
    coverage_percent = round(100 * len(institutions) / len(source_institutions), 1) if source_institutions else 0.0
    provisional_institutions = {r['institution_name'] for r in provisional}
    # Multiple outlooks for same institution/asset/frequency: most recent wins.
    latest = {}
    for r in views:
        key = (r['asset_class'],r['institution_name'])
        if key not in latest or (r['publication_date'],r['reviewed_at_utc']) > (latest[key]['publication_date'],latest[key]['reviewed_at_utc']): latest[key] = r
    by_asset = collections.defaultdict(list)
    for r in latest.values(): by_asset[(r['frequency'],r['asset_class'])].append(r)
    esc = safe
    style = '''body{margin:0;background:#f3f6fa;color:#14243a;font:15px system-ui,-apple-system,sans-serif}header{background:#0c2340;color:white;padding:30px max(20px,calc((100% - 1100px)/2))}main{max-width:1100px;margin:auto;padding:22px}h1{margin:0 0 7px}h2{margin-top:30px}p{line-height:1.5}.muted{color:#65758a}.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.kpi,.panel{background:white;border:1px solid #dce3ec;border-radius:12px;padding:18px}.kpi strong{display:block;font-size:28px;margin:5px 0}.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;background:white}th,td{border-bottom:1px solid #e5eaf0;padding:12px;text-align:left;vertical-align:top}th{background:#e9eef5}a{color:#0a568d;overflow-wrap:anywhere}.tag{border-radius:30px;padding:4px 10px;display:inline-block;font-size:12px;background:#e6eaf0}.pos{background:#daf4e5}.neu{background:#fff1c7}.neg{background:#ffe0df}.notice{border-left:4px solid #b57b00;padding:12px 16px;background:#fff8e6}details{margin:8px 0;background:white;padding:12px;border-radius:8px}footer{padding:28px;color:#65758a}'''
    out = ['<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Global Outlook — Ricerca istituzionale globale</title><style>'+style+'</style></head><body>', '<header><h1>Global Investment Outlook — Ricerca istituzionale globale</h1><div>Research Intelligence · Dashboard istituzionale</div><small>Generato '+esc(today.strftime('%Y-%m-%d %H:%M UTC'))+'</small></header><main>']
    out.append('<div class="notice"><b>Regola operativa:</b> la provenienza da un dominio ufficiale non certifica l’interpretazione. Le view assistite da IA sono mostrate separatamente e non entrano nel consensus. <b>Ammissione da fonte riconosciuta NON significa verifica della correttezza della view:</b> date, attribuzioni e parafrasi potrebbero richiedere controlli ulteriori. Flussi finanziari: n.d.</div>')
    kpis = [('Istituzioni censite',str(len(source_institutions)),'Da sources.csv'),('Gestori con view ammesse',str(len(institutions)),'Verifica documentale diretta completata'),('Copertura operativa del censimento',f'{100*len(institutions)/len(source_institutions):.1f}%' if source_institutions else 'n.d.','Non è la copertura del mercato globale'),('Flussi netti','n.d.','Nessuna serie omogenea verificata')]
    out.append('<p class="notice">Monitoraggio prioritario degli outlook recenti dal '+esc(start_date.isoformat())+' al '+esc(today_date.isoformat())+'. Sono incluse anche fonti mensili, trimestrali e strategiche; i documenti senza data rimangono candidati non validati.</p>')
    out.append('<h2>Executive dashboard</h2><section class="kpis">'+''.join('<div class="kpi"><span class="muted">'+esc(k)+'</span><strong>'+esc(v)+'</strong><small>'+esc(note)+'</small></div>' for k,v,note in kpis)+'</section>')
    # Human-readable, source-linked direct research is separate from production consensus.
    direct = rows(root / 'direct_weekly_matrix_2026-11-10.csv')
    direct = [r for r in direct if r.get('stance_type') == 'explicit' and valid_url(r.get('official_url', '')) and start_date.isoformat() <= r.get('weekly_publication_date', '') <= today_date.isoformat()]
    out.append('<h2>Ricerca diretta — posizioni esplicite documentate</h2><p class="muted">Analisi separata dal consensus automatico. La data del commento settimanale non equivale necessariamente alla data di modifica della posizione tattica. Le frecce sono n.d. senza un confronto storico omogeneo.</p>')
    if direct:
        out.append('<div class="scroll"><table><thead><tr><th>Gestore</th><th>Asset class</th><th>View</th><th>Variazione</th><th>Fonte ufficiale</th></tr></thead><tbody>')
        labels = {'overweight': ('Sovrappeso', 'pos'), 'neutral': ('Neutrale', 'neu'), 'underweight': ('Sottopeso', 'neg')}
        for r in sorted(direct, key=lambda x: (x['institution'], x['asset_or_theme'])):
            label, css = labels.get(r.get('stance'), ('n.d.', ''))
            out.append('<tr><td>'+esc(r['institution'])+'</td><td>'+esc(r['asset_or_theme'])+'</td><td><span class="tag '+css+'">'+esc(label)+'</span></td><td>n.d.</td><td><a rel="noopener noreferrer" href="'+esc(r['official_url'])+'">Apri fonte</a> · '+esc(r['weekly_publication_date'])+'</td></tr>')
        out.append('</tbody></table></div>')
    else:
        out.append('<div class="panel">Nessuna posizione esplicita disponibile nel periodo.</div>')
    out.append('<p class="muted">Le osservazioni tematiche non sono trasformate in sovrappesi o sottopesi. Questo registro di ricerca non aumenta il KPI delle view ammesse né contribuisce al consensus.</p>')
    # Documented cross-manager consensus. Equal weight per manager / asset / horizon.
    consensus_input = rows(root / 'institutional_consensus_views.csv')
    eligible = [r for r in consensus_input if r.get('stance') in STANCES and valid_url(r.get('official_url','')) and r.get('institution') and r.get('asset_class') and r.get('horizon')]
    consensus_latest = {}
    for r in eligible:
        key=(r['institution'],r['asset_class'],r['horizon'])
        if key not in consensus_latest or (r.get('publication_date') or '') > (consensus_latest[key].get('publication_date') or ''): consensus_latest[key]=r
    buckets=collections.defaultdict(list)
    for r in consensus_latest.values(): buckets[(r['asset_class'],r['horizon'])].append(r)
    out.append('<h2>Consensus istituzionale — campione verificato</h2><p class="muted">Media non ponderata delle posizioni documentate: positivo +1, neutrale 0, negativo -1. Ogni istituzione pesa una volta per asset class e orizzonte. Il campione attuale non rappresenta l’intera industria; le view non direzionali rimangono nel registro integrale sottostante.</p>')
    out.append('<div class="scroll"><table><thead><tr><th>Asset class</th><th>Orizzonte</th><th>Gestori</th><th>Positivi</th><th>Neutrali</th><th>Negativi</th><th>Consensus (-100/+100)</th></tr></thead><tbody>')
    if buckets:
        for (asset,horizon), rr in sorted(buckets.items()):
            n=len(rr); counts=collections.Counter(r['stance'] for r in rr)
            score=round(100*(counts['positive']-counts['negative'])/n)
            out.append('<tr><td>'+esc(asset)+'</td><td>'+esc(horizon)+'</td><td>'+str(n)+'</td><td>'+str(round(100*counts['positive']/n))+'%</td><td>'+str(round(100*counts['neutral']/n))+'%</td><td>'+str(round(100*counts['negative']/n))+'%</td><td>'+('+' if score>0 else '')+str(score)+'</td></tr>')
    else: out.append('<tr><td colspan="7">n.d. — nessuna posizione comparabile</td></tr>')
    out.append('</tbody></table></div>')
    out.append('<details><summary>Fonti individuali del consensus</summary><div class="scroll"><table><thead><tr><th>Gestore</th><th>Asset class</th><th>Orizzonte</th><th>View</th><th>Data</th><th>Fonte</th></tr></thead><tbody>')
    for r in sorted(consensus_latest.values(),key=lambda r:(r['institution'],r['asset_class'])):
        out.append('<tr><td>'+esc(r['institution'])+'</td><td>'+esc(r['asset_class'])+'</td><td>'+esc(r['horizon'])+'</td><td>'+esc(r['stance'])+'</td><td>'+esc(r.get('publication_date'))+'</td><td><a href="'+esc(r['official_url'])+'" rel="noopener noreferrer">Outlook</a></td></tr>')
    out.append('</tbody></table></div></details>')
    # Broader research register: accept qualitative, macro, tactical and strategic views.
    # Distinguish them from homogeneous allocation consensus; never invent weights.
    broad = [r for r in rows(root / 'expanded_official_outlooks.csv') if valid_url(r.get('official_url', ''))]
    out.append('<h2>Outlook istituzionali — tutte le tipologie di view</h2><p class="muted">Incluse analisi settimanali, mensili, trimestrali e strategiche, anche qualitative e macroeconomiche. La data originale e la frequenza sono visibili. Questo registro non richiede un sovrappeso esplicito e non altera il consensus quantitativo.</p>')
    if broad:
        out.append('<div class="scroll"><table><thead><tr><th>Istituzione</th><th>Data</th><th>Orizzonte</th><th>Area</th><th>View documentata</th><th>Fonte</th></tr></thead><tbody>')
        for r in sorted(broad, key=lambda x:(x.get('institution',''),x.get('asset_class',''))):
            out.append('<tr><td>'+esc(r.get('institution'))+'</td><td>'+esc(r.get('publication_date') or 'n.d.')+'</td><td>'+esc(r.get('frequency') or 'n.d.')+'</td><td>'+esc(r.get('asset_class'))+'</td><td>'+esc(r.get('view_summary'))+'</td><td><a rel="noopener noreferrer" href="'+esc(r['official_url'])+'">Documento</a></td></tr>')
        out.append('</tbody></table></div>')
    else:
        out.append('<div class="panel">Nessuna view documentata ancora disponibile.</div>')
    out.append('<h2>Posizionamenti preliminari senza verifica documentale completata</h2><div class="panel"><b>'+str(len(provisional))+' posizionamenti preliminari di '+str(len(provisional_institutions))+' gestori</b><p>Questi posizionamenti non sono ammessi automaticamente e non contribuiscono ai semafori né al consensus. Le descrizioni possono essere parafrasi e non citazioni testuali certificate. Controllare date, fonte e testo prima di utilizzare i dati.</p></div>')
    out.append('<h2>Copertura delle view strutturate</h2><div class="panel"><strong>'+str(len(institutions))+' / '+str(len(source_institutions))+' gestori ('+str(coverage_percent)+'%)</strong><p>La presenza nel registro fonti non equivale a una view analizzata. Le istituzioni seguenti sono censite ma non contribuiscono ancora alle matrici operative.</p>')
    if missing_view_institutions:
        out.append('<p>'+', '.join(esc(n) for n in missing_view_institutions)+'</p>')
    else:
        out.append('<p>Tutti i gestori censiti hanno almeno una view ammessa.</p>')
    out.append('</div>')
    out.append('<h2>Registro completo delle fonti istituzionali</h2><p class="muted">Ogni gestore censito compare qui anche senza view strutturate. Data di pubblicazione e data di riferimento del documento sono distinte; n.d. significa non verificata. Le date di pagina non equivalgono a una validazione della view.</p>')
    if source_registry:
        out.append('<div class="scroll"><table><thead><tr><th>Gestore</th><th>Documento ufficiale</th><th>Data pubblicazione</th><th>Dati riferiti al</th><th>Stato</th></tr></thead><tbody>')
        for s in sorted(source_registry, key=lambda r:r.get('institution_name','')):
            url = s.get('document_url','')
            link = '<a rel="noopener noreferrer" href="'+esc(url)+'">Apri documento</a>' if valid_url(url) else 'n.d.'
            out.append('<tr><td>'+esc(s.get('institution_name'))+'</td><td>'+link+'</td><td>'+esc(s.get('publication_date') or 'n.d.')+'</td><td>'+esc(s.get('as_of_date') or 'n.d.')+'</td><td>'+esc(s.get('verification_status'))+'</td></tr>')
        out.append('</tbody></table></div>')
    if provisional:
        out.append('<details><summary>Consulta le interpretazioni preliminari</summary><div class="scroll"><table><thead><tr><th>Gestore</th><th>Asset</th><th>Interpretazione IA</th><th>Fonte da verificare</th></tr></thead><tbody>')
        for r in provisional:
            url=r.get('document_url','')
            link='<a rel="noopener noreferrer" href="'+esc(url)+'">Apri fonte</a>' if valid_url(url) else 'n.d.'
            out.append('<tr><td>'+esc(r['institution_name'])+'</td><td>'+esc(r['asset_class'])+'</td><td>'+esc(r['stance'])+' — '+esc(r['evidence_quote'])+'</td><td>'+link+'</td></tr>')
        out.append('</tbody></table></div></details>')
    # Preliminary traffic lights are useful for exploration but never presented as verified.
    # A preliminary descriptive distribution is not an institutional consensus.
    prelim_latest = {}
    for r in provisional:
        k = (r['frequency'], r['asset_class'], r['institution_name'])
        if k not in prelim_latest or (r['publication_date'], r['reviewed_at_utc']) > (prelim_latest[k]['publication_date'], prelim_latest[k]['reviewed_at_utc']):
            prelim_latest[k] = r
    out.append('<h2>Matrice esplorativa — semafori NON verificati</h2><p class="notice">Le seguenti indicazioni sono interpretazioni preliminari, NON view verificate automaticamente né confermate mediante lettura completa della fonte. Le motivazioni disponibili sono parafrasi e non prove testuali controllate. Nessun consensus viene calcolato su questi dati.</p>')
    if prelim_latest:
        out.append('<div class="scroll"><table><thead><tr><th>Gestore</th><th>Asset class</th><th>Frequenza dichiarata</th><th>Semaforo preliminare</th><th>Fonte da controllare</th></tr></thead><tbody>')
        for r in sorted(prelim_latest.values(), key=lambda x: (x['institution_name'], x['asset_class'])):
            label, css = {'positive': ('Positivo', 'pos'), 'neutral': ('Neutrale', 'neu'), 'negative': ('Negativo', 'neg')}[r['stance']]
            out.append('<tr><td>'+esc(r['institution_name'])+'</td><td>'+esc(r['asset_class'])+'</td><td>'+esc(r['frequency'])+'</td><td><span class="tag '+css+'">'+label+' (preliminare)</span></td><td><a rel="noopener noreferrer" href="'+esc(r['document_url'])+'">Verifica fonte</a></td></tr>')
        out.append('</tbody></table></div>')
    else:
        out.append('<div class="panel">n.d. — Nessuna interpretazione preliminare disponibile.</div>')
    out.append('<h2>Distribuzione delle view riesaminate e matrici a semaforo</h2><p class="muted">Verde = positivo; giallo = neutrale; rosso = negativo. Il consensus richiede almeno 3 istituzioni indipendenti per asset e frequenza; con meno di 3 la distribuzione è mostrata, ma il segnale resta n.d. Le frecce compaiono soltanto quando è documentata anche una view precedente.</p>')
    for frequency in ('weekly','monthly','quarterly','strategic','unclassified'):
        out.append('<h3>'+{'weekly':'Settimanale','monthly':'Mensile','quarterly':'Trimestrale','strategic':'Strategico / annuale','unclassified':'Non classificato'}[frequency]+'</h3>')
        keys = sorted(k for k in by_asset if k[0]==frequency)
        if not keys: out.append('<div class="panel">n.d. — Nessuna view ammessa disponibile per questa frequenza.</div>'); continue
        out.append('<div class="scroll"><table><thead><tr><th>Asset class</th><th>Gestori</th><th>Positivi</th><th>Neutrali</th><th>Negativi</th><th>Consensus</th></tr></thead><tbody>')
        for _, asset in keys:
            vs = by_asset[(frequency,asset)]; counts=collections.Counter(r['stance'] for r in vs)
            score=sum(STANCES[r['stance']] for r in vs)/len(vs)
            cls, label = ('pos','Positivo') if score>0 else ('neg','Negativo') if score<0 else ('neu','Neutrale')
            if len(vs) < 3:
                cls, label = '', 'n.d. — campione insufficiente'
            out.append('<tr><td>'+esc(asset)+'</td><td>'+str(len(vs))+'</td><td>'+str(counts['positive'])+'</td><td>'+str(counts['neutral'])+'</td><td>'+str(counts['negative'])+'</td><td><span class="tag '+cls+'">'+label+'</span></td></tr>')
        out.append('</tbody></table></div>')
    out.append('<h2>View riesaminate con attribuzione documentale</h2>')
    if not views: out.append('<div class="panel">n.d. — Nessuna view ammessa. Nessun semaforo individuale viene inventato.</div>')
    else:
        out.append('<div class="scroll"><table><thead><tr><th>Gestore</th><th>Frequenza</th><th>Asset</th><th>Tipologia</th><th>View</th><th>Variazione</th><th>Fonte</th></tr></thead><tbody>')
        for r in sorted(views,key=lambda r:(r['institution_name'],r['frequency'],r['asset_class'])):
            previous = (r.get('previous_stance') or '').strip()
            arrow = '↑' if previous and STANCES[r['stance']]>STANCES[previous] else '↓' if previous and STANCES[r['stance']]<STANCES[previous] else '→' if previous else 'n.d.'
            out.append('<tr><td>'+esc(r['institution_name'])+'</td><td>'+esc(r['frequency'])+'</td><td>'+esc(r['asset_class'])+'</td><td>'+esc(stance_types.get((r['institution_name'],r['document_url'],r['asset_class']), 'n.d.'))+'</td><td><span class="tag '+{'positive':'pos','neutral':'neu','negative':'neg'}[r['stance']]+'">'+esc(r['stance'])+'</span></td><td>'+arrow+'</td><td><a rel="noopener noreferrer" href="'+esc(r['document_url'])+'">Fonte della view</a><br><small>'+esc(r['publication_date'])+' · '+esc(r['reviewer'])+'</small><br><small>'+esc(r['evidence_quote'])+'</small></td></tr>')
        out.append('</tbody></table></div>')
    out.append('<h2>Investment View Engine — documenti da analizzare</h2><div class="panel"><b>'+str(len(review_queue))+' documenti candidati</b><p>Il sistema prepara una scheda per ciascun documento candidato. Le view entrano nei semafori dopo verifica diretta della pertinenza, attribuzione, interpretazione e tracciabilità, senza filtri esclusivi di fonte ufficiale, accessibilità tecnica o revisione umana. I candidati privi di evidenze sufficienti restano separati.</p><p><code>view_review_queue.csv</code> contiene i collegamenti e i campi da completare; <code>validated_views.csv</code> è l’unica fonte per i semafori.</p></div>')
    out.append('<h2>Estratti documentali disponibili</h2><p class="muted">Questi estratti sono acquisiti automaticamente e NON rappresentano view validate. Aprire la fonte primaria per verificare data, contesto e posizionamento.</p>')
    out.append('<div class="panel"><b>'+str(len(readable_evidence))+' pagine HTML con estratti leggibili</b> su '+str(len(evidence))+' tentativi archiviati.</div>')
    if readable_evidence:
        out.append('<details><summary>Consulta gli estratti raccolti</summary><div class="scroll"><table><thead><tr><th>Gestore</th><th>Documento</th><th>Estratto (non validato)</th><th>Controllato</th></tr></thead><tbody>')
        for r in sorted(readable_evidence, key=lambda x: x.get('checked_at_utc', ''), reverse=True)[:40]:
            url = r.get('document_url', '')
            title = esc(r.get('page_title') or r.get('candidate_title') or 'Fonte')
            link = '<a rel="noopener noreferrer" href="'+esc(url)+'">'+title+'</a>' if valid_url(url) else title
            out.append('<tr><td>'+esc(r.get('institution_name'))+'</td><td>'+link+'</td><td>'+esc((r.get('text_excerpt') or '')[:500])+'</td><td>'+esc(r.get('checked_at_utc'))+'</td></tr>')
        out.append('</tbody></table></div></details>')
    out.append('<h2>Documenti candidati da verificare</h2><p class="muted">Le code seguenti non contribuiscono al consensus.</p>')
    for freq in ('weekly','monthly','quarterly','strategic','unclassified'):
        rs = candidates[freq]
        out.append('<details><summary><b>'+esc({'weekly':'Settimanali','monthly':'Mensili','quarterly':'Trimestrali','strategic':'Strategici / annuali','unclassified':'Non classificati'}[freq])+'</b> — '+str(len(rs))+' candidati</summary><div class="scroll"><table><thead><tr><th>Gestore</th><th>Titolo / collegamento</th><th>Data metadata</th><th>Stato</th></tr></thead><tbody>')
        for r in rs[:250]:
            url = r.get('final_url') or r.get('candidate_url') or ''
            title = esc((r.get('candidate_title') or 'Documento')[:180])
            link = '<a rel="noopener noreferrer" href="'+esc(url)+'">'+title+'</a>' if valid_url(url) else title
            out.append('<tr><td>'+esc(r.get('institution_name'))+'</td><td>'+link+'</td><td>'+esc(r.get('metadata_publication_date') or 'n.d.')+'</td><td>'+esc(r.get('selection_status'))+'</td></tr>')
        out.append('</tbody></table></div></details>')
    if invalid: out.append('<p class="notice">'+str(invalid)+' righe di view validate escluse per campi mancanti o formato errato.</p>')
    out.append('</main><footer>Global Outlook 3.1 · Dati di ricerca informativi, non raccomandazioni personalizzate.</footer></body></html>')
    (root/'global_outlook.html').write_text(''.join(out),encoding='utf-8')
    summary={'view_coverage_percent':coverage_percent,'institutions_without_views':missing_view_institutions,'registered_source_documents':len(source_registry),'sources_with_page_date':sum(1 for s in source_registry if s.get('publication_date') not in ('','n.d.')),'source_admitted_view_rows':len(source_admitted),'generated_at_utc':today.isoformat(),'institutions_in_sources':len(source_institutions),'institutions_with_validated_views':len(institutions),'validated_view_rows':len(views),'preliminary_traffic_light_rows':len(prelim_latest),'provisional_view_rows':len(provisional),'provisional_institutions':len(provisional_institutions),'rejected_view_rows':invalid,'candidate_counts':{k:len(v) for k,v in candidates.items()},'view_review_queue_rows':len(review_queue),'document_evidence_rows':len(evidence),'readable_evidence_rows':len(readable_evidence),'flows':'n.d.'}
    (root/'report_status.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('Dashboard generated:',summary)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--dir',default='.');args=p.parse_args();render(Path(args.dir))
