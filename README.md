# GLOBAL OUTLOOK — GitHub source database + ChatGPT research/report

> **Snapshot aggiornato Global Outlook 1.0 (11/11/2026).** Il report HTML autonomo di ChatGPT ha una base curata di **219 view / 62 gestori / 84 documenti** in [research_curated/chatgpt_direct_views_219_2026-11-11.csv](research_curated/chatgpt_direct_views_219_2026-11-11.csv), descritta in [research_curated/README.md](research_curated/README.md). Il registro legacy `validated_views.csv` rimane separato (129 view / 43 gestori), non è il conteggio del report HTML e **non va sommato** alla base curata. Il monitor automatizzato registra candidati, scansioni parziali ed errori d'accesso, ma non attribuisce view. Il report HTML diretto viene interpretato e creato da ChatGPT, non dal motore GitHub. L'automazione delle 07:00 è stata aggiornata per leggere prima la base curata.

**Architettura operativa (11 novembre 2026):** GitHub conserva il database persistente delle 100 istituzioni censite, i collegamenti e gli eventi di acquisizione. Le interpretazioni delle view, gli aggiornamenti delle matrici e la realizzazione dell'HTML sono compiti **esclusivi di ChatGPT**, mediante l'automazione giornaliera dedicata.

## Ciclo quotidiano

1. **06:00 Europe/Rome — GitHub Actions `monitor.yml`:** acquisizione delle pagine di tutte le frequenze, rilevamento cambi, scoperta di documenti, salvataggio in `sources.csv`, `acquisition_events.csv`, `document_candidates.csv`, `discovery_checks.csv` e `research_snapshot.json`. Le condizioni di accesso HTTP possono impedire singole letture; non costituiscono un filtro di validazione finanziaria. L'orario effettivo dipende dal servizio GitHub Actions.
2. **07:00 Europe/Rome — automazione ChatGPT** "Global Outlook — analisi ChatGPT e report HTML", ID `6af0be4926fc81918dc8ce5d4b4350b2`: legge repository e fonti verificabili, interpreta i documenti, integra lo storico e crea/aggiorna direttamente la dashboard `global_outlook.html` e i KPI `report_status.json` mediante il connettore GitHub. La riuscita richiede che il connettore sia disponibile durante l'esecuzione.
3. I due processi sono **separati per evitare sovrascritture**. `monitor.yml` NON lancia `build_report.py` e NON modifica `validated_views.csv`, `view_reassessment_latest.csv`, `expanded_official_outlooks.csv`, `global_outlook.html` o `report_status.json`.

## Regole metodologiche

- **Censimento ≠ view analizzata.** Una fonte scoperta non implica un giudizio finanziario. I documenti candidati mantengono lo stato non verificato.
- La lettura e l'interpretazione dei documenti spettano a ChatGPT: attribuzione, data originale, asset class, direzione, mandati, classificazione qualitativa/tattica e link.
- Le annotazioni `ChatGPT - verifica documentale completata` devono essere apposte solo dopo aver letto contenuti realmente verificabili. Non significano revisione umana o certificazione da un ente esterno.
- Per ogni gestore/asset/orizzonte mantieni le osservazioni precedenti; le frecce storiche sono lecite solo quando esiste un documento precedente distinto e comparabile, oppure evidenza esplicita di una modifica.
- Distingui **sovrappesi/neutralità/sottopesi effettivi** da **opinioni qualitative**, scenari, outlook settoriali o posizioni di singoli fondi. Evita un consensus non omogeneo. Raggruppa i giudizi per asset class, orizzonte e mandato; usa almeno tre gestori indipendenti per eventuali letture di consensus e dichiara il campione.
- Nella dashboard italiana presentare KPI del censimento e sua copertura (numeratore e denominatore), matrici a semaforo e cambi documentati, fonti individuali, view per Asia, settori e alternativi. Flussi del periodo soltanto se confrontabili e verificabili, altrimenti `n.d.`.
- Nessuna revisione umana obbligatoria; nessun filtro bloccante per dominio ufficiale o accessibilità tecnica. Pertinenza, attribuzione, interpretazione e tracciabilità restano obbligatorie.
- Errori della rete o indisponibilità del connettore NON devono eliminare view storiche né produrre view fittizie. L'ultimo HTML valido resta archiviato; fallimenti dichiarati espressamente.

## File principali

| File | Proprietario | Significato |
| --- | --- | --- |
| `sources.csv` | GitHub Actions + ricerca ChatGPT | Registro persistente fonti e istituzioni |
| `acquisition_events.csv` | GitHub Actions | Storico delle modifiche e degli accessi |
| `document_candidates.csv` | GitHub Actions | Candidati documentali storicizzati, non validati |
| `discovery_checks.csv` | GitHub Actions | Storico dei controlli effettuati |
| `research_snapshot.json` | GitHub Actions | Coda compatta da sottoporre all'analisi ChatGPT |
| `validated_views.csv` | ChatGPT | Posizioni verificate per l'analisi |
| `view_reassessment_latest.csv` | ChatGPT | Tipologia e qualità delle posizioni |
| `expanded_official_outlooks.csv` | ChatGPT | Sintesi delle ricerche interpretate |
| `global_outlook.html` | ChatGPT | Dashboard HTML interattiva e matrici |
| `report_status.json` | ChatGPT | Metadati, copertura e KPI dell'HTML |

## Operatività e limiti

Il workflow si può eseguire manualmente nella sezione GitHub **Actions**. Dopo una modifica del codice o delle fonti è prevista anche un'esecuzione da push. I commit nel repository conservano lo storico; gli artifact GitHub Actions sono temporanei (configurazione: 30 giorni).

Il repository è attualmente **pubblico**; non caricare dati personali o ricerca proprietaria senza prima modificarne le impostazioni di visibilità.

`build_report.py` rimane un vecchio renderer/test locale, **non usato nella produzione giornaliera**: eseguirlo manualmente può sostituire il report creato da ChatGPT. Invio email e sincronizzazione con il Report Center esterno **non fanno parte di questo workflow** e vanno verificati separatamente.

Nessun sistema automatizzato di lettura può garantire la disponibilità di ogni sito. L'esecuzione ChatGPT resta soggetta alle autorizzazioni del connettore e alla riuscita del servizio di automazione.

## Contratto obbligatorio del report (13 novembre 2026)

**Per ogni run ChatGPT Global Outlook, prima di comporre o pubblicare l'HTML, leggere e rispettare [research_curated/README.md](research_curated/README.md), sezione «Requisiti di pubblicazione obbligatori».** La pubblicazione e la dicitura «report completo» richiedono che siano effettivamente presenti almeno: (1) data media delle view dell'**intero periodo** e metodo di calcolo; (2) **variazioni di posizione dichiarate** e variazioni di stance comparabili negli **ultimi 21 giorni**, distinguendo i due concetti; (3) matrici macro/micro delle due sezioni; (4) confronti verso il report precedente, fonti e limiti documentali. Ripristini e snapshot non sostituiscono questa verifica.

## Layout canonico del checkpoint GO-20261112-2246

- **Sorgente grafica ESATTA e immutabile:** repository `magitenia-bot/trading-system-professional`, branch `report-center-publisher`, commit `27a29f184b08052836492d9ef7cbb6d3923d7a71`, file `publisher/reports/cap-945cc9f493ec52f5000655c4f8ba6d4f45264af476559e9e.html`, blob Git SHA `73d8d0a1b558a8fd14b0d5e0ce903fa82d520142`. È il formato verde/blu esistente alle 22:46 Europe/Rome del 12/11/2026, non un mock-up.
- **Preservare CSS, struttura e interazioni dell'HTML originario.** Le ancore centrali sono `focus-21d`, `confronto-recenti`, `variazioni-posizioni-21g`, `confronto-globale`, `quadro`, `global-publication-average`, `macro`, `micro`, `settori`, `registro`, `sintesi-fonti`, `metodo`.
- L'edizione 13/11/2026, nel **layout ripristinato**, è stata pubblicata come `publisher/reports/cap-7c7eb5b4f1168310ab0dba9fef2f7689cf54d061be8b48ef.html` (commit `69ed032cc3b30ead4ab03ece42e49c91772b1072`); conserva le 219 view, 62 gestori, 84 URL, con 86 view/18 gestori/30 documenti nella finestra recente; 5 variazioni fonte-dichiarate e data media dello storico.
- Aggiornare i dati significa cambiare le osservazioni, i KPI e le finestre temporali mantenendo identica l'impostazione visuale; **non riprogettare** la dashboard a ogni esecuzione. Lasciare l'originale del checkpoint immutato e usare una nuova edizione per ogni rilascio.
- Non considerare completo un report se mancano la data media delle view nell'intero periodo, le variazioni nella sezione recenti, le matrici e le schede fonti. Le modifiche alla struttura non vanno inferite dai soli CSV.
