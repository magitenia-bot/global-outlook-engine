# GLOBAL OUTLOOK — GitHub source database + ChatGPT research/report

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


## Global Macro Cycle Intelligence 1.0

Nuovo modulo macroeconomico separato all'interno di questo stesso repository: [documentazione](macro_cycle/README.md), [dashboard HTML con curve dei rendimenti](macro_cycle/dashboard_macro_cycle.html), [catalogo indicatori](macro_cycle/indicator_catalog.csv), [archivio delle curve](macro_cycle/data/yield_curves.csv). Il workflow `.github/workflows/macro-cycle-collect.yml` acquisisce solo dati grezzi senza modificare il report Global Outlook, le view o gli score; ChatGPT gestisce le interpretazioni e la dashboard. Stato: prima release con curve USA e Giappone del 9–10 novembre 2026; fasi macro non ancora stimate.
