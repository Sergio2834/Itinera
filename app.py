import streamlit as st
import google.generativeai as genai
import json
import datetime
import geonamescache # Il database locale di Nazioni e Città

# --- CONFIGURAZIONE CHIAVE API ---
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- STILE CSS ---
st.markdown("""
<style>
    .activity-card {
        background-color: #fcfcfc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #8B4513;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    div[data-baseweb="select"] { margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNZIONE PER CARICARE IL DATABASE (OTTIMIZZATA) ---
# Usiamo @st.cache_data per non ricaricare il database ad ogni click
@st.cache_data
def load_location_data():
    gc = geonamescache.GeonamesCache()
    
    # 1. Recupera tutte le nazioni (Dizionario: Codice -> Dati)
    countries = gc.get_countries()
    # Crea una lista di nomi nazioni ordinata (es. "Italy", "France")
    # Creiamo anche una mappa inversa: "Italy" -> "IT" per trovare le città dopo
    country_names = []
    country_name_to_code = {}
    
    for code, data in countries.items():
        name = data['name']
        country_names.append(name)
        country_name_to_code[name] = code
        
    country_names.sort()

    # 2. Recupera le città (questo è un database grande!)
    cities = gc.get_cities()
    
    # 3. Organizziamo le città per nazione: {'IT': ['Rome', 'Milan'], 'FR': ['Paris']...}
    cities_by_country_code = {}
    
    for city_id, data in cities.items():
        country_code = data['countrycode']
        city_name = data['name']
        
        if country_code not in cities_by_country_code:
            cities_by_country_code[country_code] = []
        
        cities_by_country_code[country_code].append(city_name)
    
    # Ordiniamo le città alfabeticamente per ogni nazione
    for code in cities_by_country_code:
        cities_by_country_code[code].sort()
        
    return country_names, country_name_to_code, cities_by_country_code

# Carichiamo i dati all'avvio dell'app
all_nations, map_name_code, db_cities = load_location_data()

# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, flight_in, end_date, flight_out):
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": 0.2,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 8192,
    }

    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    prompt = f"""
    Agisci come una guida turistica esperta in Storia dell'Arte e Cultura. 
    Crea un itinerario JSON dettagliato per un viaggio culturale a {destination}.
    
    DATI INPUT:
    - Arrivo: {start_date} (Volo: {flight_in})
    - Partenza: {end_date} (Volo: {flight_out})
    
    OBIETTIVO:
    L'itinerario deve essere focalizzato ESCLUSIVAMENTE su **Luoghi di Interesse Culturale** (Musei, Siti Archeologici, Chiese Storiche, Palazzi).
    
    REGOLE:
    1. **Clustering:** Raggruppa i monumenti vicini.
    2. **Disjunction:** Evita i musei più famosi negli orari di punta.
    3. **Logistica:** Rispetta orari voli.

    FORMATO OUTPUT (SOLO JSON PURO):
    {{
      "trip_title": "Titolo evocativo",
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

    with st.spinner(f'Analisi culturale di {destination} in corso...'):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore: {e}")
            return None

# --- UI PRINCIPALE ---
st.title("🏛️ AI Cultural Travel Planner")
st.markdown("Pianificazione automatica di itinerari d'arte e storia con Database Mondiale.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Destinazione")
    
    # 1. Menu Nazione (Dalla lista completa caricata)
    # Cerchiamo di mettere l'Italia come default
    default_ix = all_nations.index("Italy") if "Italy" in all_nations else 0
    selected_nation = st.selectbox("Seleziona Nazione", all_nations, index=default_ix)
    
    # 2. Logica per trovare le città di QUELLA nazione
    # Troviamo il codice (es. "Italy" -> "IT")
    nation_code = map_name_code.get(selected_nation)
    
    # Recuperiamo le città dal dizionario pre-caricato
    available_cities = db_cities.get(nation_code, [])
    
    # Aggiungiamo sempre l'opzione manuale nel caso manchi una città piccola
    city_options = ["Scrivi manualmente..."] + available_cities
    
    selected_city_opt = st.selectbox(f"Città in {selected_nation}", city_options, index=1 if len(city_options) > 1 else 0)
    
    if selected_city_opt == "Scrivi manualmente...":
        city_input = st.text_input("Inserisci il nome della città")
    else:
        city_input = selected_city_opt

    final_destination = f"{city_input}, {selected_nation}"

with col2:
    st.subheader("✈️ Dettagli Viaggio")
    c_date_in, c_flight_in = st.columns(2)
    with c_date_in:
        start_date = st.date_input("Data Arrivo", datetime.date.today())
    with c_flight_in:
        flight_in = st.text_input("Volo Andata", "FR5191")
        
    c_date_out, c_flight_out = st.columns(2)
    with c_date_out:
        end_date = st.date_input("Data Partenza", datetime.date.today() + datetime.timedelta(days=3))
    with c_flight_out:
        flight_out = st.text_input("Volo Ritorno", "W62361")

st.markdown("---")

if st.button("✨ Genera Itinerario Culturale", type="primary", use_container_width=True):
    if not city_input:
        st.warning("Seleziona una città valida.")
    else:
        trip_data = get_itinerary(final_destination, start_date, flight_in, end_date, flight_out)
        
        if trip_data:
            st.success(f"Itinerario per {final_destination} creato!")
            st.markdown("---")
            st.header(trip_data.get("trip_title", ""))
            st.write(trip_data.get("summary", ""))

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

st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash API & GeonamesCache")