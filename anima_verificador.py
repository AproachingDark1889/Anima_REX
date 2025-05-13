import yaml
import sys

def verificar_config(path="config.yml"):
    """
    Verifica la validez del archivo de configuración.
    Retorna una tupla (bool, mensaje).
    """
    errores = []
    advertencias = []

    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            if not isinstance(config, dict):
                errores.append("La configuración debe ser un diccionario.")
    except Exception as e:
        # Error crítico al leer o parsear el archivo
        return False, f"Error al leer el archivo de configuración: {e}"

    # Claves obligatorias en la raíz de la configuración
    for clave in ["credenciales", "duracion", "martingala"]:
        if clave not in config:
            errores.append(f"Falta la clave obligatoria: {clave}")

    # Validar estructura de 'credenciales'
    cred = config.get("credenciales", {})
    if not isinstance(cred, dict):
        errores.append("La clave 'credenciales' debe ser un diccionario.")
    else:
        for campo in ["email", "password"]:
            if campo not in cred:
                errores.append(f"Falta el campo '{campo}' en 'credenciales'.")

    # Validar campo 'demo' dentro de 'credenciales'
    cred_demo = cred.get("demo")
    if "demo" not in cred:
        errores.append("Falta el campo 'demo' en 'credenciales'.")
    elif not isinstance(cred_demo, bool):
        errores.append("El campo 'credenciales.demo' debe ser booleano.")

    # Validar 'duracion'
    dur = config.get("duracion")
    try:
        if dur is not None:
            try:
                dur_float = float(dur)
                if dur_float <= 0:
                    errores.append("El valor de 'duracion' debe ser mayor que 0.")
            except ValueError:
                errores.append("El valor de 'duracion' debe ser un número válido.")
        else:
            errores.append("El valor de 'duracion' no puede ser None.")
    except Exception:
        errores.append("El valor de 'duracion' debe ser un número.")

    # Validar sección 'martingala'
    mart = config.get("martingala")
    if not isinstance(mart, dict):
        errores.append("La clave 'martingala' debe ser un diccionario.")
    else:
        # Niveles debe existir y ser lista
        niveles = mart.get("niveles")
        if not isinstance(niveles, list) or not niveles:
            errores.append("La clave 'martingala.niveles' debe ser una lista no vacía.")
        # Validar stop_loss / stop_win si existen
        for clave in ["stop_loss", "stop_win"]:
            if clave in mart:
                try:
                    val = float(mart[clave])
                    if val < 0:
                        errores.append(f"El valor de 'martingala.{clave}' no puede ser negativo.")
                except Exception:
                    errores.append(f"El valor de 'martingala.{clave}' debe ser numérico.")

    # Construir mensaje de salida
    if errores:
        mensaje = "Errores: " + "; ".join(errores)
        return False, mensaje

    mensaje = "Configuración validada exitosamente."
    if advertencias:
        mensaje += " Advertencias: " + "; ".join(advertencias)

    return True, mensaje


def main():
    valido, mensaje = verificar_config("config.yml")
    if not valido:
        print(f"❌ {mensaje}")
        sys.exit(1)
    print(f"[OK] {mensaje}")

if __name__ == "__main__":
    main()
