# Archivio Global Outlook diretto (ChatGPT)

Il file [chatgpt_direct_views_219_2026-11-11.csv](./chatgpt_direct_views_219_2026-11-11.csv) conserva le **219 view** del report HTML autonomo dell'11 novembre 2026: **62 gestori**, **84 URL originali**. Non sovrascrive il registro legacy `validated_views.csv` (129 view).

**Attenzione:** una parte delle view è qualitativa, condizionale, relativa a singoli fondi o priva di un estratto documentale completo. La presenza nel database non equivale a riverifica delle fonti né a consenso investibile. Le date mese/anno e anno sono meno precise.

**Flusso operativo:** GitHub Actions individua e archivia i candidati (senza attribuire view); ChatGPT interpreta documenti ufficiali, confronta i dati con lo storico e costruisce direttamente il report HTML (non in questo repository). Non si importa automaticamente un candidato come view validata. Il report HTML esistente non si aggiorna da solo: occorre rigenerare una nuova versione dal database sincronizzato nell'esecuzione ChatGPT.

Il file `manifest.json` descrive conteggi e limiti. Conservare i precedenti file storici immutati.

## Requisiti di pubblicazione obbligatori — consolidati 13 novembre 2026

Questi requisiti sono **vincolanti per ogni report Global Outlook**, incluse rigenerazioni, ripristini da snapshot, automazioni, test e pubblicazioni manuali. L'assenza di uno di essi rende il report incompleto; non pubblicarlo come "completo". Il file archivio `current_views.csv` contiene le osservazioni, ma **non sostituisce** questo contratto di presentazione/analisi.

### Sezione 01 — Ultimi 21 giorni (verde)
1. KPI numero di view, gestori, documenti, delta nuovi gestori e nuove view rispetto al precedente report, distinguendo per scorrimento temporale e nuovi documenti.
2. Matrici macro asset class e micro asset class, con semafori positivi, neutrali e negativi; evidenziare N, copertura e omogeneità.
3. **Variazioni di view e di posizione**: tabella visibile con gestore, asset/settore, data fonte, orientamento e freccia salita/discesa/invariato **solo se documentata**, link a fonte e tipo di evidenza.
4. Distinguere **(a)** aumento/diminuzione di esposizione esplicitamente dichiarato nella singola pubblicazione, da **(b)** cambio effettivo di stance rispetto a un precedente documento datato, omogeneo per mandato/orizzonte. Il tipo (a) va mostrato e qualificato, anche quando non esiste un documento precedente completo. Il tipo (b) non va inventato.
5. Le view che escono dalla finestra mobile per data non sono cambi di posizionamento. Riportare separatamente entrate/uscite della finestra ed entrate/uscite nel database.

### Sezione 02 — Intero periodo (blu)
1. KPI view, gestori, fonti distinte, nuovi gestori e nuove view rispetto al report precedente; flussi netti e copertura solo se con perimetro e denominatore verificabili, altrimenti n.d.
2. **Data media delle view di tutto il periodo** immediatamente visibile tra i KPI, con anzianità media in giorni riferita alla data del report e numerosità del campione.
3. Per le date giorno usare la data esatta; per date mese/anno o solo anno **non fingere precisione**. Riportare la media su date complete e, se si stima la media totale, imputare convenzionalmente giorno 15 per il solo mese e 1 luglio per il solo anno, descrivendo chiaramente il metodo. La media è ponderata per view: un gestore con più view pesa più volte. Non confonderla con una media per gestore o con la data dell'ultima rilevazione.
4. Matrici a semaforo per le 30 dimensioni istituzionali (geografie, stile, duration, credito, valute, materie prime, alternativi), sintesi macro/micro asset class e focus sui settori azionari; consenso GICS n.d. se supporto comparabile insufficiente. Link a schede dei gestori e fonti.
5. Analisi delle convergenze/divergenze, delle differenze per orizzonte/mandato e qualità documentale. Nessun portafoglio modello.

### Quality gate prima di pubblicare
- Verificare **entrambe le sezioni**, media storico, lista variazioni recenti e matrice macro/micro; non limitarsi ai KPI o al fatto che l'HTML esista.
- Controllare che il report precedente e lo storico siano letti e che il delta sia calcolato correttamente.
- Mantenere gli 219 record storici archiviati distinti dal registro legacy da 129 record: non sommarli.
- Non assumere che un punto di ripristino, una chat precedente o una dashboard HTML precedente trasmetta automaticamente istruzioni nuove all'automazione: rileggerle da questo contratto prima di generare.
- Se la fonte non consente confronto omogeneo, mostrarne il limite e conservare comunque le variazioni fonte-dichiarate con etichetta corretta.

## Layout canonico del checkpoint GO-20261112-2246

- **Sorgente grafica ESATTA e immutabile:** repository `magitenia-bot/trading-system-professional`, branch `report-center-publisher`, commit `27a29f184b08052836492d9ef7cbb6d3923d7a71`, file `publisher/reports/[slug-riservato].html`, blob Git SHA `73d8d0a1b558a8fd14b0d5e0ce903fa82d520142`. È il formato verde/blu esistente alle 22:46 Europe/Rome del 12/11/2026, non un mock-up.
- **Preservare CSS, struttura e interazioni dell'HTML originario.** Le ancore centrali sono `focus-21d`, `confronto-recenti`, `variazioni-posizioni-21g`, `confronto-globale`, `quadro`, `global-publication-average`, `macro`, `micro`, `settori`, `registro`, `sintesi-fonti`, `metodo`.
- L'edizione 13/11/2026, nel **layout ripristinato**, è stata pubblicata come `publisher/reports/[slug-riservato].html` (commit `69ed032cc3b30ead4ab03ece42e49c91772b1072`); conserva le 219 view, 62 gestori, 84 URL, con 86 view/18 gestori/30 documenti nella finestra recente; 5 variazioni fonte-dichiarate e data media dello storico.
- Aggiornare i dati significa cambiare le osservazioni, i KPI e le finestre temporali mantenendo identica l'impostazione visuale; **non riprogettare** la dashboard a ogni esecuzione. Lasciare l'originale del checkpoint immutato e usare una nuova edizione per ogni rilascio.
- Non considerare completo un report se mancano la data media delle view nell'intero periodo, le variazioni nella sezione recenti, le matrici e le schede fonti. Le modifiche alla struttura non vanno inferite dai soli CSV.
