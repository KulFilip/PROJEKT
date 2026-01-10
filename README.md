# Midas Project - SMT & ZigZag Analysis

System do automatycznej analizy danych Forex z MetaTrader 5, wykorzystujący statystyczne podobieństwo (Nearest Neighbors) do przewidywania swingów.

## Struktura Projektu

- `main.py`: Główny skrypt procesujący. Pobiera dane z MT5, zapisuje do bazy i wykonuje analizę.
- `config.py`: Konfiguracja połączenia, symboli i parametrów ZigZag.
- `database.py`: Obsługa bazy danych SQLite (`market_data.db`).
- `data_connector.py`: Moduł komunikacji z MetaTrader 5.
- `analysis.py`: Rdzeń analityczny (ZigZag, SMT, Predykcja NN).
- `midas.ipynb`: Interaktywny notebook do wizualizacji i testów.

## Instalacja

1. Upewnij się, że masz zainstalowany Python 3.10+.
2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```
3. Upewnij się, że terminal MetaTrader 5 jest uruchomiony i zalogowany na konto demo/live.

## Użycie

### 1. Praca w tle (Automatyzacja)
Aby pobrać dane i zaktualizować bazę danych oraz zobaczyć aktualne predykcje, uruchom:
```bash
python main.py
```

### 2. Analiza Interaktywna (Jupyter)
1. Uruchom serwer Jupyter (możesz użyć `run_jupyter.ps1`).
2. Otwórz `midas.ipynb`.
3. Notebook jest skonfigurowany tak, aby pobierać dane bezpośrednio z bazy danych stworzonej przez `main.py` lub prosto z MT5. Możesz tam modyfikować wykresy i parametry "na żywo".

## Parametry Analysis
W pliku `config.py` możesz dostosować:
- `ZIGZAG_DEPTH`, `DEVIATION`, `BACKSTEP`: Czułość wskaźnika ZigZag.
- `SYMBOLS`: Listę instrumentów do obserwacji (np. `['XAUUSD', 'XAGUSD']`).
- `HISTORY_BARS`: Liczbę świec pobieranych do analizy.
