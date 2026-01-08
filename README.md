# 🌍 Itinera

**Itinera** è un'applicazione web intelligente sviluppata con **Streamlit** che ti aiuta a pianificare i tuoi viaggi. Grazie all'integrazione con **Google Gemini**, l'app è in grado di generare itinerari personalizzati e fornire suggerimenti basati sulle tue preferenze.

## Funzionalità

* **Pianificazione AI:** Generazione di itinerari di viaggio dettagliati utilizzando Google Gemini.
* **Database Geografico:** Selezione precisa delle destinazioni grazie all'integrazione con `geonamescache`.
* **Interfaccia Intuitiva:** Esperienza utente semplice e pulita garantita da Streamlit.

## Installazione e Configurazione

Segui questi passaggi per eseguire la Web App

### 1. Crea un ambiente virtuale
Utilizza nel tuo terminale il comando `python -m venv venv` (o `py -m venv venv`) per creare un ambiente virtuale.

### 2. Attiva l'ambiente virtuale
Se stai utilizzando **Windows** utilizza il comando `.\venv\Scripts\activate`; Se stai utilizzando **Mac/Linux** utilizza il comando `source venv/bin/activate`.

### 3. Installa le dipendenze
Esegui il comando `pip install -r requirements.txt`

## Utilizzo
Dopo esserti posizionato nella cartella **Itinera-main** con il comando `cd Itinera-main`, per avviare l'applicazione esegui il comando: `streamlit run app.py`, l'app si aprirà automaticamente all'indirizzo http://localhost:8501.

## Struttura dell'applicazione
 * **app.py** : file principale dell'applicazione
* **requirements.txt** : lista delle librerie necessarie
* **.streamlit/** : configurazione di Streamlit

