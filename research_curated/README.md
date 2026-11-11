# Archivio Global Outlook diretto (ChatGPT)

Il file [chatgpt_direct_views_219_2026-11-11.csv](./chatgpt_direct_views_219_2026-11-11.csv) conserva le **219 view** del report HTML autonomo dell'11 novembre 2026: **62 gestori**, **84 URL originali**. Non sovrascrive il registro legacy `validated_views.csv` (129 view).

**Attenzione:** una parte delle view è qualitativa, condizionale, relativa a singoli fondi o priva di un estratto documentale completo. La presenza nel database non equivale a riverifica delle fonti né a consenso investibile. Le date mese/anno e anno sono meno precise.

**Flusso operativo:** GitHub Actions individua e archivia i candidati (senza attribuire view); ChatGPT interpreta documenti ufficiali, confronta i dati con lo storico e costruisce direttamente il report HTML (non in questo repository). Non si importa automaticamente un candidato come view validata. Il report HTML esistente non si aggiorna da solo: occorre rigenerare una nuova versione dal database sincronizzato nell'esecuzione ChatGPT.

Il file `manifest.json` descrive conteggi e limiti. Conservare i precedenti file storici immutati.
