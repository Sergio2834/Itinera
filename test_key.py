import google.generativeai as genai

# -----------------------------------------------------------
# INCOLLA QUI LA TUA CHIAVE TRA LE VIRGOLETTE
api_key = "AIzaSyC8EK2UwcM-gVqfY0iJ3qANiYnfzVHRy9Y"
# -----------------------------------------------------------

genai.configure(api_key=api_key)

print("🔍 Sto interrogando Google...")

try:
    print("\n✅ MODELLI DISPONIBILI PER TE:")
    found = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"   👉 {m.name}")
            found = True
    
    if not found:
        print("   ❌ Nessun modello trovato. La chiave potrebbe essere errata.")

except Exception as e:
    print(f"\n❌ ERRORE GRAVE: {e}")
    print("Controlla di aver copiato TUTTA la chiave (inizia con AIza...)")