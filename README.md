# AVM70 Diagnostics

Selvstændig diagnostik-app til Anthem AVM 70-lydprocessoren. Appen viser al system-relevant info og runtime-data live i browseren, sammen med rå protokol-trafik og en hændelseslog.

## Start

```powershell
.\run.ps1
```

Første gang opretter scriptet `backend\.venv` og installerer afhængigheder. Derefter starter appen på <http://127.0.0.1:8070>.

AVM70-adressen sættes i `backend\.env` (kopiér fra `.env.example`) eller direkte i UI'et under **Indstillinger**:

```
AVM_HOST=10.1.1.7
AVM_PORT=14999
```

> AVM70 accepterer kun én netværksklient ad gangen. Lukker du ikke anden software der er forbundet til den, kan appen ikke forbinde.

Under **Setup → Network** på AVM70 skal **IP Control** være slået til. Vil du kunne læse fra enheden mens den står i standby, skal **Standby IP Control** også være slået til.

## Udvikling uden enheden

```powershell
cd backend
.venv\Scripts\python.exe -m app.tools.fake_avm      # fake AVM70 på 127.0.0.1:14999
```

Sæt derefter host til `127.0.0.1` i UI'et.

## Tests

```powershell
cd backend
.venv\Scripts\python.exe -m pytest
```

Se [ARCHITECTURE.md](ARCHITECTURE.md) for opbygningen og [CLAUDE.md](CLAUDE.md) for projektreglerne.
