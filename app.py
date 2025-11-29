import streamlit as st
import google.generativeai as genai
import json
import datetime
import geonamescache
import pandas as pd # Per la mappa
from fpdf import FPDF # Per il PDF

# --- CONFIGURAZIONE CHIAVE API ---
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- STILE CSS PERSONALIZZATO (Design Moderno) ---
st.markdown("""
<style>
    /* Stile Card Attività */
    .activity-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border-left: 6px solid #8B4513; /* Bronzo Storia */
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .activity-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    .card-title {
        color: #2c3e50;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .card-desc {
        color: #555;
        font-size: 0.95em;
        margin-bottom: 10px;
    }
    .card-meta {
        font-size: 0.85em;
        color: #888;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .maps-link {
        color: #4285F4;
        text-decoration: none;
        font-weight: bold;
    }
    .maps-link:hover { text-decoration: underline; }
    
    /* Time Badge */
    .time-badge {
        background-color: #8B4513;
        color: white;
        padding: 5px 10px;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9em;
        text-align: center;
        width: fit-content;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE LOCALE ---
@st.cache_data
def load_location_data():
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    country_names = sorted([data['name'] for code, data in countries.items()])
    map_name_code = {data['name']: code for code, data in countries.items()}
    
    cities = gc.get_cities()
    cities_by_country_code = {}
    for city_id, data in cities.items():
        cc = data['countrycode']
        if cc not in cities_by_country_code: cities_by_country_code[cc] = []
        cities_by_country_code[cc].append(data['name'])
    
    for cc in cities_by_country_code: cities_by_country_code[cc].sort()
    return country_names, map_name_code, cities_by_country_code

all_nations, map_name_code, db_cities = load_location_data()

# --- FUNZIONE PDF EXPORT ---
def create_pdf(trip_data, destination):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 15)
            self.cell(0, 10, f'Itinerario Culturale: {destination}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Titolo e Riassunto
    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 10, f"Titolo: {trip_data.get('trip_title', '')}")
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 10, f"Riassunto: {trip_data.get('summary', '')}")
    pdf.ln(5)

    for day in trip_data.get("days", []):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, f"Giorno {day['day_number']} - {day['date']}", 0, 1)
        pdf.ln(2)
        
        pdf.set_font("Arial", '', 11)
        for act in day.get("activities", []):
            time_str = f"{act['time']} ({act['duration']})"
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(40, 10, time_str)
            pdf.cell(0, 10, act['place_name'], 0, 1)
            
            pdf.set_font("Arial", '', 10)
            # Puliamo il testo da caratteri non supportati standard
            desc = act['description'].encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 6, f" - {desc}")
            pdf.ln(2)
        pdf.ln(5)
        
    return pdf.output(dest='S').encode('latin-1')

# --- FUNZIONE GENERAZIONE ITINERARIO ---
def get_itinerary(destination, start_date, arrival_time, end_date, departure_time):
    if not api_key or "INSERISCI" in api_key:
        st.error("⚠️ Chiave API mancante.")
        return None

    genai.configure(api_key=api_key)
    
    generation_config = {"temperature": 0.2, "top_p": 1, "top_k": 32, "max_output_tokens": 8192}
    model = genai.GenerativeModel(model_name="gemini-2.0-flash", generation_config=generation_config)

    str_arr = arrival_time.strftime("%H:%M")
    str_dep = departure_time.strftime("%H:%M")

    # PROMPT POTENZIATO: Chiede coordinate GPS
    prompt = f"""
    Agisci come una guida turistica esperta. Crea un itinerario culturale per {destination}.
    
    DATI INPUT:
    - ARRIVO: {start_date} ore {str_arr}.
    - RITORNO: {end_date}, partenza ore {str_dep}.
    
    OBIETTIVO:
    Itinerario focalizzato su **Musei, Storia, Arte**.
    
    REGOLE LOGISTICHE:
    1. **Arrivo ({str_arr}):** +2h per uscire aeroporto.
    2. **Partenza ({str_dep}):** Stop attività 4h prima.
    3. **Coordinate:** Per OGNI attività devi fornire le coordinate (lat, lon) approssimative per la mappa.

    FORMATO OUTPUT (SOLO JSON):
    {{
      "trip_title": "Titolo",
      "summary": "Riassunto",
      "days": [
        {{
          "day_number": 1,
          "date": "YYYY-MM-DD",
          "activities": [
            {{
              "time": "HH:MM",
              "place_name": "Nome",
              "description": "Descrizione",
              "duration": "2h",
              "coordinates": {{ "lat": 41.9028, "lon": 12.4964 }},
              "tips": "Consiglio"
            }}
          ]
        }}
      ]
    }}
    """

    with st.spinner(f'Generazione mappa e itinerario per {destination}...'):
        try:
            response = model.generate_content(prompt)
            text_response = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(text_response)
        except Exception as e:
            st.error(f"Errore: {e}")
            return None

# --- UI PRINCIPALE ---
st.title("🏛️ AI Cultural Travel Planner")
st.markdown("Itinerari storici con **Mappe Interattive** ed **Export PDF**.")

col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Destinazione")
    default_ix = all_nations.index("Italy") if "Italy" in all_nations else 0
    selected_nation = st.selectbox("Seleziona Nazione", all_nations, index=default_ix)
    nation_code = map_name_code.get(selected_nation)
    available_cities = db_cities.get(nation_code, [])
    city_options = ["Scrivi manualmente..."] + available_cities
    selected_city_opt = st.selectbox(f"Città in {selected_nation}", city_options, index=1 if len(city_options) > 1 else 0)
    city_input = st.text_input("Inserisci città") if selected_city_opt == "Scrivi manualmente..." else selected_city_opt
    final_destination = f"{city_input}, {selected_nation}"

with col2:
    st.subheader("✈️ Date e Orari")
    c_date_in, c_time_in = st.columns(2)
    with c_date_in: start_date = st.date_input("Giorno Arrivo", datetime.date.today())
    with c_time_in: arrival_time = st.time_input("Ora Atterraggio", datetime.time(10, 00))
    
    st.write("")
    c_date_out, c_time_out = st.columns(2)
    with c_date_out: end_date = st.date_input("Giorno Partenza", datetime.date.today() + datetime.timedelta(days=3))
    with c_time_out: departure_time = st.time_input("Ora Decollo", datetime.time(18, 00))

st.markdown("---")

if st.button("✨ Genera Itinerario Completo", type="primary", use_container_width=True):
    if not city_input:
        st.warning("Seleziona una città valida.")
    else:
        trip_data = get_itinerary(final_destination, start_date, arrival_time, end_date, departure_time)
        
        if trip_data:
            st.success(f"Itinerario creato per {final_destination}!")
            st.markdown("---")
            
            # Intestazione
            st.header(trip_data.get("trip_title", ""))
            st.write(trip_data.get("summary", ""))
            
            # Pulsante PDF in alto (comodo)
            pdf_bytes = create_pdf(trip_data, final_destination)
            st.download_button(
                label="📄 Scarica Itinerario PDF",
                data=pdf_bytes,
                file_name=f"Itinerario_{city_input}.pdf",
                mime="application/pdf",
            )

            # Loop Giorni
            for day in trip_data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day['date']}", expanded=True):
                    
                    # 1. VISUALIZZAZIONE MAPPA DEL GIORNO
                    # Estraiamo le coordinate di tutte le attività del giorno
                    map_points = []
                    for act in day.get("activities", []):
                        if "coordinates" in act:
                            map_points.append(act["coordinates"])
                    
                    if map_points:
                        # Creiamo un DataFrame per st.map
                        df_map = pd.DataFrame(map_points)
                        # Rinominiamo colonne se necessario (st.map vuole 'lat', 'lon' o 'latitude', 'longitude')
                        # Gemini di solito restituisce 'lat' e 'lon', perfetto.
                        st.map(df_map, size=20, color='#8B4513') # Colore marrone per i punti
                    
                    # 2. LISTA ATTIVITÀ (Card Design)
                    for activity in day.get("activities", []):
                        c_time, c_content = st.columns([1, 4])
                        
                        with c_time:
                            st.markdown(f"<div class='time-badge'>{activity['time']}</div>", unsafe_allow_html=True)
                            st.caption(f"Durata: {activity['duration']}")
                        
                        with c_content:
                            # Link a Google Maps
                            clean_place = activity['place_name'].replace(" ", "+")
                            maps_url = f"https://www.google.com/maps/search/?api=1&query={clean_place}+{city_input}"
                            
                            st.markdown(f"""
                            <div class="activity-card">
                                <div class="card-title">{activity['place_name']}</div>
                                <div class="card-desc">{activity['description']}</div>
                                <div class="card-meta">
                                    <span><i>💡 Tip: {activity['tips']}</i></span>
                                    <a href="{maps_url}" target="_blank" class="maps-link">📍 Vedi su Maps</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

st.markdown("---")
st.caption("Powered by Google Gemini 2.0 Flash, Streamlit & OpenStreetMap Data")