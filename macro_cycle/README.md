# GLOBAL MACRO CYCLE INTELLIGENCE 1.0

Modulo interno del solo repository **Global Outlook**. Non usa, scrive o modifica altri repository. La cartella `macro_cycle/` è autonoma: i workflow e i dati storici originali di Global Outlook non devono essere sovrascritti.

## Obiettivo

Determinare la fase attuale e le transizioni del ciclo economico, per area geografica, con dati verificabili e indicatori anticipatori. Classificare separatamente il momentum della crescita e il regime dell'inflazione, riconoscendo espansione, ripresa/reflazione, rallentamento, stagnazione, contrazione/recessione, surriscaldamento, stagflazione e disinflazione. Disinflazione e stagflazione sono combinazioni di dinamiche crescita/prezzi, non necessariamente stadi alternativi dello stesso asse.

## Universo iniziale

Stati Uniti, Eurozona, Italia, Germania, Cina, Giappone, India e Regno Unito. Espansione pianificata a 25-30 economie e aggregati, senza dedurre la fase di un Paese da quella della sua regione.

## Componenti

- `indicator_catalog.csv`: primo registro di 37 indicatori chiave (obiettivo finale 80-120).
- `data/yield_curves.csv`: osservazioni di rendimenti governativi con scadenza, metodo, data e fonte, senza interpolazioni sintetiche registrate come dati.
- `data/cycle_status.json`: stati delle aree. I campi non verificati restano null = n.d.
- `dashboard_macro_cycle.html`: prima dashboard HTML interattiva con confronto internazionale delle curve e spread.
- `ingest_yield_curves.py`: importatore delle serie ufficiali; se una fonte fallisce conserva l'ultimo dato.
- `.github/workflows/macro-cycle-collect.yml`: workflow dedicato, indipendente dai monitor Global Outlook.

## Metodologia prevista

1. Registro fonti: priorità a OCSE, Eurostat, BCE, FMI, FRED/ALFRED, BIS, World Bank e autorità nazionali; per la curva USA U.S. Treasury; Giappone MOF.
2. Standard dati: geography, indicator_id, period, frequency, value, unit, seasonal_adjustment, source_url, released_at, retrieved_at, vintage, revision, quality.
3. Data quality: monitoraggio valori mancanti, outlier, revisioni, frequenze disomogenee; trasformazioni annualizzate solo se esplicitate.
4. Scoring iniziale da tarare storicamente: 25% attività reale, 25% leading, 15% lavoro, 15% credito/moneta, 10% condizioni finanziarie, 10% commercio/aspettative. Normalizzazione robusta per Paese; penalità per scarsa copertura e serie non aggiornate; inflazione valutata separatamente.
5. Matrice: momentum crescita × momentum inflazione; livelli di attività e prezzi necessari per distinguere recessione, stagflazione e reflazione. Nessuna fase basata solo sulla forma della curva dei rendimenti.
6. Backtest: dataset point-in-time, vintage storici, revisione dati e confronto con eventi del ciclo; walk-forward rigorosamente fuori campione.
7. Probabilità a 3/6/12 mesi: pubblicabili solo dopo calibrazione e verifica out-of-sample. Altrimenti n.d.
8. ChatGPT cura interpretazione, sintesi, classificazione macro documentata e aggiornamento del report HTML; GitHub conserva fonti, misure, registri e versioni. L'ingestione automatica non assegna fasi macro.

## Curve dei rendimenti

Grafico comparativo con linee per Paese/scadenza; futura estensione a eurozona, Germania, Italia, Cina, Regno Unito, India. Calcoli 10Y–2Y e 10Y–3M (quando i due punti esistono), mutamenti daily/weekly/monthly, bear/bull steepening e flattening, inversioni, pendenza e curvatura. Per ciascuna serie indicare se par, spot, zero-coupon o rendimento di un titolo benchmark: le metodologie **non sono completamente intercambiabili**, soprattutto in un grafico internazionale.

### Dati iniziali effettivamente verificati
- **USA 9 e 10 novembre 2026**: Treasury Daily Par Yield Curve (CMT), fonte primaria: https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value_month=202611&type=daily_treasury_yield_curve .
- **Giappone 9 e 10 novembre 2026**: valori attribuiti al MOF e confrontati con https://saiken.net/en/curve/ ; fonte primaria CSV https://www.mof.go.jp/jgbs/reference/interest_rate/jgbcm.csv . Lettura diretta del CSV MOF da verificare nell'importazione automatica; la serie è tracciata con questa limitazione.
- Le altre curve e tutti gli score macro rimangono **n.d.** finché la verifica non è completata.

## Stato progetto

*11 novembre 2026*: realizzata struttura minima di archivio e dashboard. Non ancora completati database storico macro, validazione di tutte le aree, modelli probabilistici, monitor automatico effettivamente testato e pubblicazione programmata ChatGPT. Non trattare una connessione o un workflow definito come prova della sua esecuzione.

## Integrazioni

Il report `macro_cycle/dashboard_macro_cycle.html` può essere collegato da Global Outlook, Report Private e dal Report Center, ma senza scrivere in repository esterni. Mantenere distinte le view degli asset manager dagli indicatori macro ufficiali.
