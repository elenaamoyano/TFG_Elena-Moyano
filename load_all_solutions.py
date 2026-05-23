import requests
import time
from datetime import datetime

FASTAPI_URL = "http://localhost:8001"

BASE_DIR = Path(__file__).parent

SOLUCIONES_POR_COLECCION = {
    "code": BASE_DIR / "solutions" / "code.txt",
    "config": BASE_DIR / "solutions" / "config.txt",
    "docker": BASE_DIR / "solutions" / "docker.txt",
    "env": BASE_DIR / "solutions" / "env.txt"
}

def leer_soluciones(archivo):
    try:
        with open(archivo, 'r', encoding='utf-8') as f:
            lineas = [linea.strip() for linea in f if linea.strip()]
        return lineas
    except FileNotFoundError:
        print(f"Archivo no encontrado: {archivo}")
        return []

def subir_solucion(solucion, indice, coleccion):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_virtual = f"solucion_{coleccion}_{timestamp}_{indice:03d}.txt"
    
    payload = {
        "text": solucion,
        "collection": coleccion
    }
    
    try:
        response = requests.post(
            f"{FASTAPI_URL}/ingest",
            json=payload,
            timeout=30
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

print("Subiendo soluciones a Chroma por colección")

total_exitos = 0
total_soluciones = 0

for coleccion, archivo in SOLUCIONES_POR_COLECCION.items():
    print(f"\nColección: {coleccion}")
    print(f"Archivo: {archivo}")
    
    soluciones = leer_soluciones(archivo)
    if not soluciones:
        print(" Sin soluciones. Saltando...")
        continue
    
    print(f" Encontradas {len(soluciones)} soluciones")
    
    exitosos = 0
    for i, sol in enumerate(soluciones, 1):
        print(f"   Subiendo {i}/{len(soluciones)}...", end=" ")
        if subir_solucion(sol, i, coleccion):
            exitosos += 1
        time.sleep(0.5)
    
    print(f"Subidas {exitosos}/{len(soluciones)} a '{coleccion}'")
    total_exitos += exitosos
    total_soluciones += len(soluciones)

print("\n" + "=" * 50)
print(f"RESUMEN FINAL")
print(f"Total soluciones: {total_soluciones}")
print(f"Subidas exitosas: {total_exitos}")
print(f"Tasa de éxito: {total_exitos/total_soluciones*100:.1f}%")
print("=" * 50)