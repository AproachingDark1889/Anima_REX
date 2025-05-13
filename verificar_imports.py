import os
import re
import sys

def encontrar_imports(path):
    resultado = []
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py"):
                ruta_completa = os.path.join(root, file)
                try:
                    with open(ruta_completa, encoding='utf-8') as f:
                        lineas = f.readlines()
                except Exception as e:
                    print(f"[ERROR] No se pudo leer: {ruta_completa} ({e})")
                    continue

                for i, linea in enumerate(lineas, 1):
                    if re.match(r'^\s*(from|import)\s+[a-zA-Z0-9_.]+', linea):
                        resultado.append((os.path.relpath(ruta_completa, path), i, linea.strip()))
    return resultado

if __name__ == "__main__":
    proyecto = os.path.abspath(".")
    print(f"\n🔍 Escaneando imports en: {proyecto}\n")

    imports = encontrar_imports(proyecto)
    if not imports:
        print("⚠️  No se encontraron imports.")
        sys.exit(1)

    for archivo, linea, codigo in sorted(imports):
        print(f"📄 {archivo:<40} [Línea {linea:>3}]: {codigo}")

    print(f"\n✅ Total de archivos escaneados: {len(set(a for a, _, _ in imports))}")
    print(f"✅ Total de líneas de import encontradas: {len(imports)}")
