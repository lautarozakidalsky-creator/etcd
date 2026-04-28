#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
watcher_to_json.py - Integrado con tu página de Pandas
Escucha etcd y genera un JSON compatible con tu frontend existente.
"""

import etcd3
import json
import os
from datetime import datetime

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

ETCD_HOST = 'localhost'  # Cambia a la IP de tu Jetson si es remoto
ETCD_PORT = 2379
WATCH_PREFIX = '/heroes/'

# Ruta del JSON (ajustada para tu estructura de carpetas)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "datos_publicos")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "datos_heroes.json")

# =============================================================================
# FUNCIONES
# =============================================================================

def transformar_para_frontend(heroes_dict):
    """
    Convierte el formato de etcd al formato que espera tu JavaScript:
    De: {"/heroes/activo/gandalf": {"clase":"Mago", "poder":"Fuego"}}
    A: [{"nombre": "gandalf", "clase": "Mago", "poder": "Fuego"}, ...]
    """
    lista_heroes = []
    
    for key, value in heroes_dict.items():
        # Extraer el nombre del héroe desde la clave completa
        # Ej: "/heroes/activo/gandalf" -> "gandalf"
        nombre = key.split('/')[-1] if '/' in key else key
        
        # Crear objeto compatible con tu tabla
        heroe = {"nombre": nombre}
        
        if isinstance(value, dict):
            # Copiar todas las propiedades del héroe
            heroe.update(value)
        else:
            # Si el valor no es dict, lo guardamos como "poder" por defecto
            heroe["poder"] = str(value)
        
        lista_heroes.append(heroe)
    
    return lista_heroes

def guardar_json(data):
    """Guarda los datos transformados en el formato que espera tu JS"""
    try:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)
        
        # Transformar al formato de array que espera tu frontend
        heroes_lista = transformar_para_frontend(data)
        
        temp_file = OUTPUT_FILE + ".tmp"
        with open(temp_file, 'w', encoding='utf-8') as f:
            # Guardamos SOLO el array, sin metadata extra, para compatibilidad
            json.dump(heroes_lista, f, indent=4, ensure_ascii=False)
        
        os.replace(temp_file, OUTPUT_FILE)
        print(f"💾 [{datetime.now().strftime('%H:%M:%S')}] JSON actualizado ({len(heroes_lista)} héroes)")
        
    except Exception as e:
        print(f"❌ Error al escribir JSON: {e}")

def cargar_estado_inicial(client):
    """Carga el estado actual de etcd antes de empezar a escuchar"""
    heroes_data = {}
    try:
        values, _ = client.get_prefix(WATCH_PREFIX)
        for value in values:
            key = value[0].decode('utf-8')
            val = value[1].decode('utf-8')
            try:
                heroes_data[key] = json.loads(val)
            except json.JSONDecodeError:
                heroes_data[key] = {"raw": val}
    except Exception as e:
        print(f"⚠️ Error cargando estado inicial: {e}")
    return heroes_data

def main():
    print("🦸 WATCHER DE HÉROES - Compatible con tu página de Pandas")
    print(f"📡 Conectando a {ETCD_HOST}:{ETCD_PORT}...")
    
    client = None
    try:
        client = etcd3.client(host=ETCD_HOST, port=ETCD_PORT)
        client.status()  # Prueba de conexión
        print("✅ Conectado a etcd")
        
        # Cargar estado inicial
        heroes_data = cargar_estado_inicial(client)
        guardar_json(heroes_data)
        
        # Iniciar watcher
        print("👁️  Escuchando cambios en tiempo real...")
        events_iterator, cancel_watch = client.watch_prefix(WATCH_PREFIX)

        for event in events_iterator:
            try:
                key = event.key.decode('utf-8')
                
                if event.delete:
                    print(f"❌ Héroe eliminado: {key}")
                    if key in heroes_data:
                        del heroes_data[key]
                else:
                    val_str = event.value.decode('utf-8')
                    print(f"✨ Cambio en {key}")
                    try:
                        heroes_data[key] = json.loads(val_str)
                    except json.JSONDecodeError:
                        heroes_data[key] = {"raw": val_str}
                
                guardar_json(heroes_data)
                
            except Exception as e:
                print(f"⚠️ Error procesando evento: {e}")
                continue

    except KeyboardInterrupt:
        print("\n🛑 Cerrando watcher...")
    except ConnectionError as e:
        print(f"\n❌ Error de conexión: {e}\n💡 Verifica que etcd esté corriendo")
    except Exception as e:
        print(f"\n❌ Error crítico: {e}\n💡 pip install etcd3")
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    main()