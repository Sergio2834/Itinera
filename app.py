import streamlit as st
import google.generativeai as genai
import json
import datetime
import geonamescache
import pandas as pd
from fpdf import FPDF
import base64

# --- CONFIGURAZIONE ---
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"
st.set_page_config(page_title="Cultural Travel Planner", page_icon="🏛️", layout="wide")

# --- 1. FUNZIONI DI UTILITÀ ---
def generate_time_slots(step_minutes=30):
    """Genera lista orari."""
    times = []
    for h in range(24):
        for m in range(0, 60, step_minutes):
            times.append(datetime.time(h, m))
    return times

@st.cache_data
def load_location_data():
    """Carica e cache dei dati geografici."""
    gc = geonamescache.GeonamesCache()
    countries = gc.get_countries()
    cities = gc.get_cities()
    
    map_name_code = {data['name']: code for code, data in countries.items()}
    country_names = sorted(map_name_code.keys())
    
    cities_by_country = {}
    for data in cities.values():
        cc = data['countrycode']
        cities_by_country.setdefault(cc, []).append(data['name'])
    
    for cc in cities_by_country:
        cities_by_country[cc].sort()
    return country_names, map_name_code, cities_by_country

all_nations, map_name_code, db_cities = load_location_data()

# --- 2. GESTIONE CSS (MODIFICATA PER OPACITÀ TOTALE) ---
def apply_custom_css(bg_file="david.jpg"):
    # Gestione Sfondo Immagine
    bg_css = ""
    try:
        with open(bg_file, "rb") as f:
            data = base64.b64encode(f.read()).decode()
            bg_css = f""".stApp {{
                background-image: linear-gradient(rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 0.8)), url("data:image/jpeg;base64,{data}");
                background-size: cover; background-attachment: fixed; background-position: center 20%;
            }}"""
    except FileNotFoundError:
        pass 

    st.markdown(f"""
    <style>
        {bg_css}
        /* 1. NASCONDI HEADER STREAMLIT (Il "bordino" nero in alto) */
        header {{
            visibility: hidden;
        }}
        /* 2. RIDUCI SPAZIO VUOTO IN CIMA ALLA PAGINA */
        .block-container {{
            padding-top: 2rem !important; /* Riduci questo valore se vuoi il titolo ancora più in alto */
            padding-bottom: 2rem !important;
        }}
        /* 1. INPUT COMPLETAMENTE OPACHI */
        /* Impostiamo un colore solido (#262730) invece di variabili trasparenti */
        .stTextInput > div > div, 
        .stSelectbox > div > div, 
        .stDateInput > div > div {{
            background-color: #262730 !important; /* Colore solido (Background Secondario) */
            border: 1px solid #444 !important;
            border-radius: 8px !important;
            color: #fafafa !important;
            opacity: 1 !important; /* Forza opacità 100% */
        }}
        
        /* 2. CALENDARIO: DATE DISABILITATE */
        div[data-baseweb="calendar"] div[aria-disabled="true"] {{
            cursor: not-allowed !important;
            opacity: 0.4 !important;
            text-decoration: line-through !important;
            color: #888 !important;
        }}
        
        /* 3. CARD ATTIVITÀ COMPLETAMENTE OPACHE */
        .activity-card {{
            background-color: #262730; /* Colore solido, niente trasparenze */
            padding: 15px; 
            border-radius: 10px;
            border-left: 5px solid var(--primary-color); 
            margin-bottom: 12px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.6); /* Ombra leggermente più forte per stacco */
        }}
        .card-title {{ color: var(--primary-color) !important; font-size: 1.15em; font-weight: bold; margin-bottom: 5px; }}
        .card-desc {{ color: #e0e0e0 !important; font-size: 0.95em; line-height: 1.4; }}
        .card-meta {{ 
            font-size: 0.85em; color: #aaa !important; 
            margin-top: 8px; padding-top: 8px; border-top: 1px solid #444;
            display: flex; justify-content: space-between;
        }}
        .time-badge {{ 
            background: #444; color: #fff !important; 
            padding: 3px 8px; border-radius: 4px; 
            font-size: 0.85em; border: 1px solid #555; 
            font-family: monospace;
        }}
        
        /* Link */
        a {{ color: var(--primary-color) !important; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
    """, unsafe_allow_html=True)

apply_custom_css()

# --- 3. FUNZIONE PDF ---
def create_pdf(trip_data, destination):
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, f'Itinerario Culturale: {destination}', 0, 1, 'C')
            self.ln(10)

    pdf = PDF()
    pdf.add_page()
    
    def safe_txt(text):
        return text.encode('latin-1', 'replace').decode('latin-1') if text else ""

    pdf.set_font("Arial", 'B', 12)
    pdf.multi_cell(0, 10, f"Titolo: {safe_txt(trip_data.get('trip_title', 'Viaggio'))}")
    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 8, f"Riassunto: {safe_txt(trip_data.get('summary', ''))}")
    pdf.ln(8)

    for day in trip_data.get("days", []):
        pdf.set_font("Arial", 'B', 14)
        pdf.set_fill_color(240, 240, 240) 
        pdf.cell(0, 10, f"Giorno {day['day_number']} - {day['date']}", 0, 1, 'L', True)
        pdf.ln(2)
        
        for act in day.get("activities", []):
            pdf.set_font("Arial", 'B', 11)
            time_str = f"{act['time']} ({act['duration']})"
            pdf.cell(35, 8, time_str)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 8, safe_txt(act['place_name']), 0, 1)
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, safe_txt(act['description']))
            pdf.ln(3)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- 4. FUNZIONE AI ---
def get_itinerary(destination, start_date, arrival_time, end_date, departure_time):
    if not api_key:
        st.error("⚠️ Chiave API mancante.")
        return None

    genai.configure(api_key=api_key)
    generation_config = {"temperature": 0.2, "response_mime_type": "application/json"}
    model = genai.GenerativeModel("gemini-2.5-flash-lite", generation_config=generation_config)

    str_arr = arrival_time.strftime("%H:%M")
    str_dep = departure_time.strftime("%H:%M") if departure_time else "Non specificato"

    prompt = f"""
    Agisci come guida turistica esperta. Crea itinerario culturale per {destination}.
    INPUT: ARRIVO {start_date} ore {str_arr}. PARTENZA {end_date} ore {str_dep}.
    REGOLE: Focus musei/arte. Ottimizza per vicinanza. Rispetta orari. Coordinate precise.
    JSON OUTPUT: {{ "trip_title": "...", "summary": "...", "days": [ {{ "day_number": 1, "date": "YYYY-MM-DD", "activities": [ {{ "time": "HH:MM", "place_name": "...", "description": "...", "duration": "...", "coordinates": {{ "lat": 0.0, "lon": 0.0 }}, "tips": "..." }} ] }} ] }}
    """

    with st.spinner(f'Analisi destinazione {destination}...'):
        try:
            response = model.generate_content(prompt)
            return json.loads(response.text)
        except Exception as e:
            st.error(f"Errore API: {e}")
            return None

# --- UI PRINCIPALE ---
st.title(" AI Cultural Travel Planner")

col1, col2 = st.columns(2)

# SELEZIONE DESTINAZIONE
with col1:
    st.subheader(" Destinazione")
    sel_nation = st.selectbox("Nazione", all_nations, index=all_nations.index("Italy") if "Italy" in all_nations else 0)
    nation_code = map_name_code.get(sel_nation)
    cities_list = db_cities.get(nation_code, [])
    city_opts = ["Scrivi manualmente..."] + cities_list
    sel_city = st.selectbox(f"Città ({sel_nation})", city_opts, index=1 if len(city_opts) > 1 else 0)
    city_input = st.text_input("Inserisci città", placeholder="Es. Firenze") if sel_city == "Scrivi manualmente..." else sel_city

# DATE E ORARI
with col2:
    st.subheader(" Date e Orari")
    all_times = generate_time_slots(30)
    time_labels = [t.strftime("%H:%M") for t in all_times]

    c1, c2 = st.columns(2)
    with c1: start_date = st.date_input("Data Arrivo", datetime.date.today())
    with c2: 
        arr_str = st.selectbox("Ora Arrivo", time_labels, index=20)
        h, m = map(int, arr_str.split(':'))
        arrival_time = datetime.time(h, m)

    c3, c4 = st.columns(2)
    with c3: 
        # min_value abilita la logica di disattivazione date precedenti
        end_date = st.date_input("Data Partenza", start_date, min_value=start_date)
    
    with c4:
        is_same_day = (start_date == end_date)
        final_times = time_labels
        if is_same_day:
            valid = [t for t in all_times if t > arrival_time]
            final_times = [t.strftime("%H:%M") for t in valid] if valid else ["Nessun orario valido"]
        
        def_idx = len(final_times) - 4 if len(final_times) > 4 else 0
        dep_str = st.selectbox("Ora Partenza", final_times, index=def_idx)
        
        departure_time = None
        if dep_str != "Nessun orario valido":
            hd, md = map(int, dep_str.split(':'))
            departure_time = datetime.time(hd, md)

    if is_same_day and departure_time:
        diff = (departure_time.hour * 60 + departure_time.minute) - (arrival_time.hour * 60 + arrival_time.minute)
        if diff < 120:
            st.warning(f"Attenzione: Permanenza di soli {diff} minuti.", icon="⚠️")

st.markdown("---")

# GENERAZIONE
if st.button("Genera Itinerario Ottimizzato", type="primary", use_container_width=True):
    errors = []
    if not city_input: errors.append("Città mancante.")
    if departure_time is None: errors.append("Orario partenza non valido.")
    elif is_same_day:
        md = departure_time.hour * 60 + departure_time.minute
        ma = arrival_time.hour * 60 + arrival_time.minute
        if md - ma < 60: errors.append("⛔ Errore: Permanenza troppo breve (< 1 ora).")

    if errors:
        for e in errors: st.error(e)
    else:
        full_dest = f"{city_input}, {sel_nation}"
        data = get_itinerary(full_dest, start_date, arrival_time, end_date, departure_time)
        
        if data:
            st.success(f"Itinerario per {full_dest}!")
            hc1, hc2 = st.columns([3, 1])
            hc1.header(data.get("trip_title", "Viaggio"))
            hc1.write(data.get("summary", ""))
            hc2.download_button("📄 PDF", create_pdf(data, full_dest), f"Itinerario_{city_input}.pdf", "application/pdf", use_container_width=True)
            st.markdown("---")

            for day in data.get("days", []):
                with st.expander(f"📅 Giorno {day['day_number']} - {day['date']}", expanded=True):
                    cl, cm = st.columns([1.8, 1.2])
                    with cl:
                        points = []
                        for act in day.get("activities", []):
                            if "coordinates" in act: points.append(act["coordinates"])
                            link = f"https://www.google.com/maps/search/?api=1&query={act['place_name'].replace(' ', '+')}+{city_input}"
                            st.markdown(f"""
                            <div class="activity-card">
                                <div style="display:flex; justify-content:space-between;">
                                    <div class="card-title">{act['place_name']}</div>
                                    <div class="time-badge">{act['time']}</div>
                                </div>
                                <div class="card-desc">{act['description']}</div>
                                <div class="card-meta">
                                    <span>⏳ {act['duration']} | 💡 {act.get('tips','-')}</span>
                                    <a href="{link}" target="_blank">📍 Maps</a>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    with cm:
                        st.markdown("###### 🗺️ Mappa")
                        if points:
                            st.map(pd.DataFrame(points), size=30, use_container_width=True)
                        else:
                            st.info("No coordinate.")