# Global Outlook — protocollo ricerca v4 (18/11/2026)

## Stato e universo
- Universo chiuso: 30 case presenti in research_curated/asset_class_matrix_2026-11-17.json.
- Catalogo verificato: 45 URL attive in sources.csv, riferite a 30 istituzioni (controllo catalogo, non controllo HTTP delle singole pagine).
- Baseline editoriale: 118 osservazioni approvate al 17 novembre. current_views.csv contiene 264 righe storiche, di cui 135 in perimetro e 129 fuori; la differenza di 17 rispetto alla baseline NON identifica 17 nuove view.
- Ultima ricerca registrata 18 novembre: 2 documenti letti, 0 nuove view; copertura incompleta.

## Flusso
1. Alle 05:00 monitorare le 45 fonti attive, distinguendo esito HTTP, cambiamento pagina e scoperta di un documento.
2. Esaminare il contenuto dei documenti originali di tutte le frequenze e orizzonti. select_outlooks_v2.py non elimina più le candidate rilevanti per frequenza non classificata o data fuori dalla finestra precedente.
3. Per ogni asset call sulle 16 classi registrare manager, URL fonte primaria, data documento, evidenza testuale, stance, orizzonte e limiti. Non trasformare commenti macro in raccomandazioni implicite.
4. Deduplicare per documento/gestore/asset/data/stance/evidenza contro baseline approvata.
5. Per ogni nuova candidata utilizzare validate_candidate.py: due tentativi distinti documentati; approvazione solo con evidenza completa; dopo secondo fallimento rimozione dalla coda operativa e registro separato. Non cancellare mai le view storiche approvate. Il file è un ledger operativo e NON un estrattore automatico di house view.
6. Alle 07:20 generare report da baseline approvata più nuove view validate, con matrice 30x16, grafici, sintesi e data media. Non bloccare per candidate non validate.
7. QA e pubblicazione: file cap-<32/48 hex>.html nel publisher, link /r/<slug>, Render LIVE del commit e verifica HTTP ove possibile, quindi aggiornare puntatore ed inviare una email HTML.

## KPI obbligatori per ogni run
30 case target; URL attive; URL effettivamente controllate; errori HTTP; documenti candidati; documenti integralmente letti; asset call estratte; duplicati; nuove view validate; tentativi di verifica; candidate escluse dopo due fallimenti; view totali approvate; copertura per ciascuna delle 16 asset class; età media delle view; backlog; HTML pubblicato; stato LIVE; test HTTP; email inviata.

## Limiti noti
Il solo monitoraggio hash non legge e interpreta le view. La lettura e la verifica primaria delle fonti devono essere eseguite nella fase A: il nuovo ledger non le sostituisce. Le 45 URL censite non garantiscono la copertura integrale delle pubblicazioni. Non affermare completamento se il numero di documenti letti resta inferiore al numero di documenti candidati.
