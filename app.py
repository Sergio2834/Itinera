import streamlit as st
import google.generativeai as genai
import json
import datetime

# --- CONFIGURAZIONE CHIAVE API ---
# ⚠️ IMPORTANTE: Incolla qui sotto la tua chiave che inizia con AIza...
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- STILE CSS PERSONALIZZATO ---
st.markdown("""
<style>
    .activity-card {
        background-color: #fcfcfc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #8B4513; /* Colore "Bronzo/Storia" */
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .time-badge {
        font-weight: bold;
        color: #8B4513;
        font-size: 1.1em;
    }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, flight_in, end_date, flight_out):
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    # Usiamo 1.5 Flash perché è il più stabile e veloce
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    # Prompt Specializzato in Cultura
    prompt = f"""
    Agisci come una guida turistica esperta in Storia dell'Arte, Archeologia e Cultura. 
    Crea un itinerario JSON dettagliato per un viaggio culturale a {destination}.
    
    DATI INPUT:
    - Arrivo: {start_date} (Volo: {flight_in})
    - Partenza: {end_date} (Volo: {flight_out})
    
    OBIETTIVO:
    L'itinerario deve essere focalizzato ESCLUSIVAMENTE su **Luoghi di Interesse Culturale** (Musei, Siti Archeologici, Chiese Storiche, Palazzi, Monumenti).
    Escludi attività di puro svago, shopping generico o parchi divertimento se non hanno rilevanza storica.

    REGOLE ALGORITMO:
    1. **Clustering:** Raggruppa i monumenti vicini nello stesso blocco orario per minimizzare i passi.
    2. **Disjunction:** Evita i musei più famosi negli orari di massima affluenza.
    3. **Logistica:** Rispetta rigorosamente gli orari dei voli inseriti.

    FORMATO OUTPUT (SOLO JSON PURO):
    {{
      "trip_title": "Titolo evocativo del tour culturale",
      "summary": "Riassunto del percorso storico-artistico",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome Luogo",
              "description": "Descrizione storico-artistica",
              "duration": "2h",
              "tips": "Consiglio (es. biglietti, audio-guida)"
            }}
          ]
        }}
      ]
    }}
    """

    with st.spinner('Analisi dei siti culturali e calcolo percorso...'):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore: {e}")
            return None

# --- UI PRINCIPALE ---
st.title("🏛️ AI Cultural Travel Planner")
st.markdown("Pianificazione automatica di itinerari d'arte e storia.")

col1, col2 = st.columns(2)

with col1:
    destination = st.text_input("Destinazione", "Firenze, Italia")
    start_date = st.date_input("Data Arrivo", datetime.date.today())
    flight_in = st.text_input("Volo Andata", "FR5191")

with col2:
    # Qui non c'è più il campo Interessi
    end_date = st.date_input("Data Partenza", datetime.date.today() + datetime.timedelta(days=3))
    flight_out = st.text_input("Volo Ritorno", "W62361")

if st.button("✨ Genera Itinerario Culturale", type="primary"):
    if not destination:
        st.warning("Inserisci la destinazione.")
    else:
        # Chiamata alla funzione (senza interessi)
        trip_data = get_itinerary(destination, start_date, flight_in, end_date, flight_out)
        
        if trip_data:
            st.success("Percorso culturale elaborato con successo!")
            st.markdown("---")
            
            # Intestazione
            st.header(trip_data.get("trip_title", ""))
            st.write(trip_data.get("summary", ""))

            # Visualizzazione Giorni
            for day in trip_data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day['date']}", expanded=True):
                    for activity in day.get("activities", []):
                        c_time, c_content = st.columns([1, 4])
                        with c_time:
                            st.markdown(f"<div style='text-align:right; color:#8B4513;'><b>{activity['time']}</b><br><small>{activity['duration']}</small></div>", unsafe_allow_html=True)
                        with c_content:
                            st.markdown(f"""
                            <div class="activity-card">
                                <b>{activity['place_name']}</b><br>
                                {activity['description']}<br>
                                <i>💡 {activity['tips']}</i>
                            </div>
                            """, unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash API & Streamlit")