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
2 bis. **Matrice settoriale recente obbligatoria** nella sezione verde: 11 settori GICS con numero gestori, numero view, semafori verde/giallo/rosso, link diretti alle view e ai gestori e indicazione n.d. quando il campione non è sufficiente. Calcolare usando solo pubblicazioni con data giornaliera certa nei 21 giorni. Inserire anche un **livello tematico distinto** (IA, semiconduttori, industria/materiali, difensivi), non assimilabile a overweight GICS; evitare duplicazioni di osservazioni e scartare le attribuzioni gestore/fonte discordanti fino a riconciliazione. Non alterare il CSS del checkpoint.

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

## Ordine di lettura e dashboard grafica — 14 novembre 2026 (1.5)

La prima schermata del report, subito dopo la navigazione dei due capitoli, presenta **«Global Outlook — sintesi e view recenti»** e **«Lettura integrata · decisioni per il comitato investimenti»**. Non collocare questi contenuti dopo i registri o le tabelle di dettaglio: quella gerarchia non soddisfa il requisito executive-first.

Ordine obbligatorio:

1. Executive summary con KPI verificati e lettura integrata di azionario, obbligazionario, diversificazione e rischi; includere i principali cambiamenti rispetto all'edizione precedente e le limitazioni della fonte.
2. **Quattro visualizzazioni** visibili prima dei registri: istogramma per asset class delle view precise degli ultimi 30 giorni (composizione per semaforo); distribuzione delle view datate per intervalli non sovrapposti nei 30 giorni; semafori su 30 giorni, data solo mensile e archivio storico; acquisizioni aggiuntive per fonte/gestore/mandato (senza confondere controllate e case indipendenti).
3. Dettagli verde 30 giorni con matrice GICS, date originali e separata aggiunta delle view con sola precisione mensile (mese corrente/precedente), variazioni documentate, fonti e registri;
4. Blu con **intero archivio storico** e matrici macro/micro/settori, data media storica, schede e fonti. Non spostare il focus 30 giorni nella blu.

Gli istogrammi sono calcolati ogni mattina dal dataset validato e dallo snapshot precedente. Non sono dati di mercato o di performance, né consenso equi-pesato per asset manager. Mostrare unità, numeri grezzi e caveat metodologici. I grafici devono essere statici, responsive, accessibili anche senza script esterni, mantenendo invariati i cinque blocchi CSS del checkpoint `GO-20261112-2246`. Ancore obbligatorie: `executive-front-title`, `executive-visuals`, `chart-macro-30d`, `chart-cadenza-30d`, `chart-orientamenti`, `chart-nuove-view`. La sezione approfondimenti può usare `recenti-dettaglio` e l'ancora originaria `recenti` punta ora alla sintesi iniziale.

## Correzione definitiva del perimetro temporale — 14 novembre 2026 (1.4, prevale su 1.3)

**Richiesta esplicita correttiva: la sezione VERDE è ampliata a 30 giorni; la BLU NON è ridotta né ampliata a una finestra di 30 giorni.**

- **VERDE / SEZIONE 01:** 30 giorni di calendario esatti, data del report meno 29 giorni fino alla data del report (estremi inclusi), con view che hanno pubblicazione `YYYY-MM-DD`. Aggiungere in tabella distinta tutte le osservazioni con data solo `YYYY-MM` corrispondente al mese corrente del report o precedente. KPI separati per giorno e mese; somma consultabile senza duplicazione, senza affermare che tutte le date mensili sono sicuramente nei 30 giorni.
- **BLU / SEZIONE 02:** mantenere l'INTERO periodo storico e tutte le 232 view archiviate al 14/11; per le edizioni future aggiornare il totale dal dataset. **Nessun modulo o filtro rolling 30 giorni all'interno della blu.** Conservarne matrici macro/micro/settoriali, variabilità delle view, dossier, fonti, provenienza e data media storica (con metodo di imputazione trasparente).
- **Controlli:** modulo principale `green-30day-window` e registro `green-30day-rows`, supplemento `green-monthly-views` / `green-monthly-rows`. La matrice settoriale GICS nella verde deve riflettere il nucleo a giorno certo dei **30** giorni; i temi mensili sono sempre separati. Le vecchie ancore HTML `focus-21d` e `edition-rows` possono essere mantenute per compatibilità/collegamenti, ma i KPI principali della verde devono descrivere correttamente il 30 giorni.
- **Layout e consegna:** cinque blocchi CSS invariati secondo checkpoint `GO-20261112-2246`; fase 05:00 analisi e fase 07:00 report/posta HTML invariati. Le date parziali non vengono artificialmente portate al giorno 15 per certificare la finestra (imputazione consentita solo per calcolo della data media storica).

## Procedura permanente di validazione incrementale — 14 novembre 2026

- **Backlog persistente:** `research_curated/review_queue.csv` raccoglie 90 coppie gestore-documento candidate emerse il 14/11 dopo deduplicazione rispetto alle scoperte precedenti. `B01` identifica i primi 20 candidati da valutare; la mera iscrizione in coda non comporta verifica né validazione.
- **Fase A 05:00:** interpretazione ChatGPT di fino a 20 documenti prioritari, uno per volta, con verifica autore/gestore, fonte originale, pubblicazione e data esatta o parziale, eventuale posizione, metodo (assoluta/relativa/qualitativa/fondo), deduplica, aggiornamento della coda. Le fonti bloccate o non verificabili restano in attesa, le false attribuzioni sono scartate, le posizioni di singoli fondi non diventano house view.
- **Persistenza:** appende solo nuove view documentate a `research_curated/current_views.csv` conservando integralmente baseline dei 219 record e file legacy separati. Effettua rilettura SHA, conteggio e controllo degli ID. Registra metriche verificabili: candidati prioritari e letti, scartati, attese, fonti realmente consultate, nuove view e nuovi gestori, nuove posizioni esplicite e limiti.
- **Fase B 07:00:** usa il dataset verificato, il precedente snapshot e il formato immutabile `GO-20261112-2246`, senza iniziare una seconda ricerca. Le nuove view con data parziale entrano solo nella sezione blu, non nei 21 giorni verdi.
- **Primo risultato registrato:** il 14/11/2026 7 view di Eastspring Investments (ID 220–226) sono state inserite sulla base dell'outlook Q4 2026 pubblicato in ottobre. Nessun nuovo gestore (Eastspring già presente). La data è mensile, quindi nessun inserimento artificiale nella finestra recente. Il resto della coda conserva lo stato per la successiva lettura.
- **Limite operativo:** la schedulazione non è garanzia di 20 documenti effettivamente letti; contare solo le fonti consultate e registrare le ragioni di incompletezza. Un filtro sui titoli e sulle notizie RSS non è verifica del contenuto documentale.
