import streamlit as st
import google.generativeai as genai
import json
import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="AI Travel Planner", page_icon="✈️", layout="wide")

# --- STILE CSS PERSONALIZZATO (Per renderlo "visibilmente decente") ---
st.markdown("""
<style>
    .activity-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .time-badge {
        font-weight: bold;
        color: #ff4b4b;
        font-size: 1.1em;
    }
    .tag {
        background-color: #e0e0e0;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.8em;
        margin-right: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: CONFIGURAZIONE ---
with st.sidebar:
    st.header("⚙️ Configurazione")
    api_key = st.text_input("Inserisci la tua Gemini API Key", type="password")
    st.info("Ottieni la chiave su aistudio.google.com")
    
    st.divider()
    st.write("Questo tool usa Gemini Pro per calcolare percorsi ottimali basati su vincoli di orario e affollamento.")

# --- FUNZIONE GENERAZIONE ITINERARIO ---
# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, flight_in, end_date, flight_out, interests):
    if not api_key:
        st.error("Per favore inserisci la API Key nel menu laterale.")
        return None

    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    # QUI ABBIAMO MESSO IL MODELLO CHE ABBIAMO VISTO NELLA TUA LISTA
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    prompt = f"""
    Agisci come un esperto algoritmo di pianificazione viaggi. 
    Crea un itinerario JSON per un viaggio a {destination}.
    
    DATI INPUT:
    - Arrivo: {start_date} (Volo: {flight_in})
    - Partenza: {end_date} (Volo: {flight_out})
    - Interessi: {interests}

    REGOLE:
    1. **Clustering:** Raggruppa attività vicine nello stesso blocco orario.
    2. **Disjunction/Folla:** Evita luoghi affollati negli orari di punta.
    3. **Logistica:** Rispetta gli orari dei voli.

    FORMATO OUTPUT (SOLO JSON):
    {{
      "trip_title": "Titolo del viaggio",
      "summary": "Riassunto",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Descrizione",
              "duration": "2h",
              "tips": "Consiglio"
            }}
          ]
        }}
      ]
    }}
    """

    with st.spinner('Gemini sta pianificando il percorso ottimale...'):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore: {e}")
            return None

    genai.configure(api_key=api_key)
    
    # Configurazione del modello
    generation_config = {
        "temperature": 0.2, # Bassa temperatura per essere più deterministico/logico
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    model = genai.GenerativeModel(model_name="gemini-2.5-pro-preview-05-06", generation_config=generation_config)

    # --- IL PROMPT INGEGNERIZZATO ---
    # Qui applichiamo la logica di Disjunction e Clustering via linguaggio naturale
    prompt = f"""
    Agisci come un esperto algoritmo di pianificazione viaggi. 
    Il tuo compito è creare un itinerario JSON dettagliato per un viaggio a {destination}.
    
    DATI INPUT:
    - Arrivo: {start_date} (Volo: {flight_in})
    - Partenza: {end_date} (Volo: {flight_out})
    - Interessi: {interests}

    REGOLE DI OTTIMIZZAZIONE (ALGORITMO MENTALE):
    1. **Clustering Geografico:** Raggruppa le attività vicine tra loro nello stesso blocco temporale per minimizzare gli spostamenti.
    2. **Vincoli di Orario (Opening Hours):** NON suggerire luoghi chiusi nel giorno/ora specifica (es. Musei chiusi il Lunedì).
    3. **Euristica della Folla (Disjunction):** Se un luogo è famoso per essere affollato in un certo orario (es. weekend mattina), spostalo in uno slot meno affollato (es. mattina presto o tardo pomeriggio), anche se questo rompe leggermente il cluster geografico, purché sia logistico sensato.
    4. **Logistica Voli:** Considera che l'utente non può fare attività 2 ore prima del volo di partenza o appena atterrato se il volo è tardi.

    FORMATO OUTPUT RICHIESTO (STRETTAMENTE JSON):
    Devi restituire SOLO un oggetto JSON valido, senza markdown ```json``` e senza testo introduttivo.
    Struttura:
    {{
      "trip_title": "Titolo evocativo del viaggio",
      "summary": "Breve riassunto logistico",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Breve descrizione e motivo della scelta (es. 'Meno affollato ora')",
              "duration": "2h",
              "tips": "Consiglio pratico (es. prenota online)"
            }}
          ]
        }}
      ]
    }}
    """

    with st.spinner('Gemini sta calcolando il percorso ottimale e verificando gli orari...'):
        try:
            response = model.generate_content(prompt)
            # Pulizia della risposta nel caso Gemini inserisca backticks
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore nella generazione o nel parsing: {e}")
            return None

# --- INTERFACCIA PRINCIPALE ---
st.title("🗺️ AI Smart Travel Planner")
st.markdown("Inserisci i dettagli del volo e lascia che l'AI ottimizzi il percorso evitando le folle.")

col1, col2 = st.columns(2)

with col1:
    destination = st.text_input("Destinazione (Città/Paese)", "Roma, Italia")
    start_date = st.date_input("Data Arrivo", datetime.date.today())
    flight_in = st.text_input("Numero Volo Andata (es. AZ203)", "AZ203")

with col2:
    interests = st.text_input("Interessi particolari", "Arte, Cibo locale, Storia")
    end_date = st.date_input("Data Partenza", datetime.date.today() + datetime.timedelta(days=3))
    flight_out = st.text_input("Numero Volo Ritorno (es. AZ208)", "AZ208")

generate_btn = st.button("✨ Genera Itinerario Ottimizzato", type="primary")

# --- LOGICA DI VISUALIZZAZIONE ---
if generate_btn:
    if not destination or not flight_in:
        st.warning("Compila tutti i campi necessari.")
    else:
        # Chiamata all'AI
        trip_data = get_itinerary(destination, start_date, flight_in, end_date, flight_out, interests)

        if trip_data:
            st.success("Itinerario calcolato con successo!")
            st.markdown("---")
            
            # Intestazione Viaggio
            st.header(trip_data.get("trip_title", f"Viaggio a {destination}"))
            st.info(trip_data.get("summary", ""))

            # Loop attraverso i giorni (NON elenco puntato, ma struttura visiva)
            for day in trip_data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day['date']}", expanded=True):
                    
                    # Creiamo una timeline visiva
                    for activity in day.get("activities", []):
                        # Layout a colonne per ogni attività
                        c_time, c_content = st.columns([1, 4])
                        
                        with c_time:
                            st.markdown(f"<div style='text-align: right; margin-top: 15px;'><span class='time-badge'>{activity['time']}</span><br><small>{activity['duration']}</small></div>", unsafe_allow_html=True)
                        
                        with c_content:
                            # HTML personalizzato per la card
                            st.markdown(f"""
                            <div class="activity-card">
                                <h4>{activity['place_name']}</h4>
                                <p>{activity['description']}</p>
                                <p><i>💡 Tip: {activity['tips']}</i></p>
                            </div>
                            """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.caption("Powered by Google Gemini API & Streamlit")