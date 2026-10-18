
import json
import os
import re
from datetime import datetime

# ==========================================
# CONFIGURACIÓN
# ==========================================

ARCHIVO = "expedientes.json"
ARCHIVO_CONTADOR = "ultimo_codigo.txt"
ARCHIVO_TEMPORAL = ARCHIVO + ".tmp"

ESTADOS = [
    "Registrado",
    "En revisión",
    "Derivado",
    "Atendido"
]

TIPOS_IDENTIDAD = [
    "DNI",
    "Carné de extranjería",
    "Pasaporte",
    "Otro"
]

TIPOS_DOCUMENTO = [
    "Carta",
    "Solicitud",
    "Informe",
    "Oficio",
    "Memorando",
    "Otro"
]

CAMPOS = [
    "codigo",
    "nombre_completo",
    "tipo_documento_identidad",
    "numero_documento",
    "tipo_documento_presentado",
    "asunto",
    "fecha_recepcion",
    "folios",
    "estado",
    "fecha_actualizacion"
]

expedientes = []


# ==========================================
# 1. VALIDACIONES
# ==========================================

def validar_nombre(texto):
    texto = texto.strip()

    if not texto:
        return False, "El nombre es obligatorio."

    if not any(c.isalpha() for c in texto):
        return False, "El nombre debe contener letras."

    if not all(
        c.isalpha() or c.isspace() or c in ".'-"
        for c in texto
    ):
        return False, "El nombre contiene caracteres no permitidos."

    return True, ""


def validar_asunto(texto):
    texto = texto.strip()

    if not texto:
        return False, "El asunto es obligatorio."

    if len(texto) < 3:
        return False, "El asunto debe tener al menos 3 caracteres."

    if not any(c.isalnum() for c in texto):
        return False, "El asunto debe contener letras o números."

    return True, ""


def validar_numero_documento(numero, tipo):
    numero = numero.strip()

    if not numero:
        return False, "El número de documento es obligatorio."

    if tipo == "DNI":
        if not re.fullmatch(r"\d{8}", numero):
            return False, "El DNI debe tener exactamente 8 números."
    else:
        if not re.fullmatch(r"[A-Za-z0-9-]{6,15}", numero):
            return False, (
                "El número debe tener entre 6 y 15 caracteres "
                "alfanuméricos."
            )

    return True, ""


def validar_folios(valor):
    texto = str(valor).strip()

    if not texto.isdigit():
        return False, "Los folios deben ser números enteros."

    if int(texto) <= 0:
        return False, "Los folios deben ser mayores que cero."

    return True, ""


def validar_fecha(fecha, permitir_futura=False):
    try:
        fecha_objeto = datetime.strptime(
            fecha, "%Y-%m-%d"
        ).date()

        if fecha_objeto.strftime("%Y-%m-%d") != fecha:
            return False, "Use el formato AAAA-MM-DD."

        if not permitir_futura and fecha_objeto > datetime.now().date():
            return False, "No se permiten fechas futuras."

        return True, ""

    except (ValueError, TypeError):
        return False, "Fecha inválida. Use AAAA-MM-DD."


def solicitar_nombre(mensaje):
    while True:
        valor = input(mensaje).strip()
        valido, error = validar_nombre(valor)

        if valido:
            return valor

        print(error)


def solicitar_asunto(mensaje="Asunto del expediente: "):
    while True:
        valor = input(mensaje).strip()
        valido, error = validar_asunto(valor)

        if valido:
            return valor

        print(error)


def solicitar_folios():
    while True:
        valor = input("Cantidad de folios: ").strip()
        valido, error = validar_folios(valor)

        if valido:
            return int(valor)

        print(error)


def solicitar_codigo():
    while True:
        numero = input(
            "Ingresa los 3 números del código (ej. 001): "
        ).strip()

        if re.fullmatch(r"\d{3}", numero):
            return f"EXP-{numero}"

        print("Código inválido. Ingresa exactamente 3 números.")


def seleccionar_opcion(titulo, opciones):
    print(f"\n{titulo}")

    for i, opcion in enumerate(opciones, start=1):
        print(f"{i}. {opcion}")

    while True:
        seleccion = input("Selecciona una opción: ").strip()

        if seleccion.isdigit():
            numero = int(seleccion)

            if 1 <= numero <= len(opciones):
                return opciones[numero - 1]

        print("Opción inválida.")


def solicitar_identidad():
    tipo = seleccionar_opcion(
        "Tipo de documento de identidad:",
        TIPOS_IDENTIDAD
    )

    while True:
        numero = input("Número de documento: ").strip()
        valido, error = validar_numero_documento(numero, tipo)

        if valido:
            return tipo, numero

        print(error)


# ==========================================
# 2. GENERACIÓN DE CÓDIGOS
# ==========================================

def generar_codigo():
    mayor_registrado = 0

    for expediente in expedientes:
        coincidencia = re.fullmatch(
            r"EXP-(\d{3})",
            expediente.get("codigo", "")
        )

        if coincidencia:
            mayor_registrado = max(
                mayor_registrado,
                int(coincidencia.group(1))
            )

    ultimo_guardado = 0

    if os.path.exists(ARCHIVO_CONTADOR):
        try:
            with open(
                ARCHIVO_CONTADOR, "r", encoding="utf-8"
            ) as archivo:
                contenido = archivo.read().strip()

                if contenido.isdigit():
                    ultimo_guardado = int(contenido)

        except OSError as error:
            print(f"Aviso: no se pudo leer el contador: {error}")

    numero = max(mayor_registrado, ultimo_guardado) + 1

    if numero > 999:
        print("Se alcanzó el límite de 999 expedientes.")
        return None

    try:
        with open(
            ARCHIVO_CONTADOR, "w", encoding="utf-8"
        ) as archivo:
            archivo.write(str(numero))

    except OSError as error:
        print(f"Error al guardar el contador: {error}")
        return None

    return f"EXP-{numero:03d}"


# ==========================================
# 3. BUSCAR EXPEDIENTES
# ==========================================

def buscar_por_codigo(codigo):
    for i, expediente in enumerate(expedientes):
        if expediente.get("codigo") == codigo:
            return i

    return None



def buscar_por_numero_documento(numero):
    encontrados = []

    for i, expediente in enumerate(expedientes):
        if expediente.get("numero_documento") == numero:
            encontrados.append(i)

    return encontrados



# ==========================================
# 4. CARGAR EXPEDIENTES JSON
# ==========================================
def cargar_expedientes():
    global expedientes

    if not os.path.exists(ARCHIVO):
        expedientes = []
        print("No existe un archivo previo. Se creará al guardar.")
        return True

    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)

        if not isinstance(datos, list):
            print("Error: el JSON debe contener una lista.")
            print("No se iniciará el sistema para proteger los datos.")
            return False

        registros_validos = []
        codigos_vistos = set()
        rechazados = 0

        for dato in datos:
            if not isinstance(dato, dict):
                rechazados += 1
                continue

            try:
                codigo = str(dato.get("codigo", "")).strip().upper()
                nombre = str(dato.get("nombre_completo", "")).strip()
                tipo_identidad = str(
                    dato.get("tipo_documento_identidad", "")
                ).strip()
                numero_documento = str(
                    dato.get("numero_documento", "")
                ).strip()
                tipo_presentado = str(
                    dato.get("tipo_documento_presentado", "")
                ).strip()
                asunto = str(dato.get("asunto", "")).strip()
                fecha = str(dato.get("fecha_recepcion", "")).strip()
                estado = str(dato.get("estado", "Registrado")).strip()
                fecha_actualizacion = str(
                    dato.get("fecha_actualizacion", fecha)
                ).strip()

                valido_nombre, _ = validar_nombre(nombre)
                valido_asunto, _ = validar_asunto(asunto)
                valido_fecha, _ = validar_fecha(
                    fecha, permitir_futura=True
                )
                valido_actualizacion, _ = validar_fecha(
                    fecha_actualizacion, permitir_futura=True
                )
                valido_documento, _ = validar_numero_documento(
                    numero_documento, tipo_identidad
                )
                valido_folios, _ = validar_folios(dato.get("folios", 1))

                if not re.fullmatch(r"EXP-\d{3}", codigo):
                    rechazados += 1
                    continue
                
                if codigo in codigos_vistos:
                    rechazados += 1
                    continue

                if (
                    not valido_nombre
                    or not valido_asunto
                    or not valido_fecha
                    or not valido_actualizacion
                    or not valido_documento
                    or not valido_folios
                    or tipo_identidad not in TIPOS_IDENTIDAD
                    or tipo_presentado not in TIPOS_DOCUMENTO
                ):
                    rechazados += 1
                    continue
                if estado not in ESTADOS:
                    rechazados += 1
                    continue

                registro = {
                    "codigo": codigo,
                    "nombre_completo": nombre,
                    "tipo_documento_identidad": tipo_identidad,
                    "numero_documento": numero_documento,
                    "tipo_documento_presentado": tipo_presentado,
                    "asunto": asunto,
                    "fecha_recepcion": fecha,
                    "folios": int(dato.get("folios", 1)),
                    "estado": estado,
                    "fecha_actualizacion": fecha_actualizacion
                }

                registros_validos.append(registro)
                codigos_vistos.add(codigo)

            except (ValueError, TypeError, AttributeError):
                rechazados += 1

        if rechazados:
            print(
                f"Error: se encontraron {rechazados} registros "
                "inválidos o duplicados."
            )
            print("No se iniciará el sistema para proteger el archivo.")
            print("Revisa expedientes.json antes de continuar.")
            return False

        expedientes = registros_validos
        print(f"Expedientes cargados: {len(expedientes)}")
        return True

    except (OSError, json.JSONDecodeError, UnicodeError) as error:
        print(f"Error al leer el archivo JSON: {error}")
        print("No se iniciará el sistema para proteger los datos.")
        return False

# ==========================================
# 5. GUARDAR EXPEDIENTES JSON
# ==========================================

def guardar_expedientes():
    try:
        with open(
            ARCHIVO_TEMPORAL, "w", encoding="utf-8"
        ) as archivo:
            json.dump(
                expedientes,
                archivo,
                ensure_ascii=False,
                indent=4
            )
            archivo.write("\n")

        os.replace(ARCHIVO_TEMPORAL, ARCHIVO)
        return True

    except (OSError, TypeError, ValueError) as error:
        print(f"Error al guardar los expedientes: {error}")

        try:
            if os.path.exists(ARCHIVO_TEMPORAL):
                os.remove(ARCHIVO_TEMPORAL)
        except OSError:
            pass

        return False


# ==========================================
# 6. MOSTRAR EXPEDIENTE
# ==========================================

def mostrar_expediente(i):
    expediente = expedientes[i]

    print("\n" + "=" * 55)
    print(f"Código                    : {expediente['codigo']}")
    print(f"Nombre completo           : {expediente['nombre_completo']}")
    print(
        "Tipo de identidad        : "
        f"{expediente['tipo_documento_identidad']}"
    )
    print(f"Número de documento       : {expediente['numero_documento']}")
    print(
        "Documento presentado     : "
        f"{expediente['tipo_documento_presentado']}"
    )
    print(f"Asunto                    : {expediente['asunto']}")
    print(f"Fecha de recepción        : {expediente['fecha_recepcion']}")
    print(f"Folios                    : {expediente['folios']}")
    print(f"Estado                    : {expediente['estado']}")
    print(
        "Última actualización      : "
        f"{expediente['fecha_actualizacion']}"
    )
    print("=" * 55)


# ==========================================
# 7. REGISTRAR EXPEDIENTE
# ==========================================

def registrar_expediente():
    print("\n--- REGISTRAR EXPEDIENTE ---")

    nombre = solicitar_nombre("Nombre completo del remitente: ")
    tipo_identidad, numero_documento = solicitar_identidad()

    tipo_presentado = seleccionar_opcion(
        "Tipo de documento presentado:",
        TIPOS_DOCUMENTO
    )

    asunto = solicitar_asunto()
    cantidad_folios = solicitar_folios()

    fecha = datetime.now().strftime("%Y-%m-%d")
    codigo = generar_codigo()

    if codigo is None:
        print("No se pudo generar el código.")
        return

    nuevo = {
        "codigo": codigo,
        "nombre_completo": nombre,
        "tipo_documento_identidad": tipo_identidad,
        "numero_documento": numero_documento,
        "tipo_documento_presentado": tipo_presentado,
        "asunto": asunto,
        "fecha_recepcion": fecha,
        "folios": cantidad_folios,
        "estado": "Registrado",
        "fecha_actualizacion": fecha
    }

    expedientes.append(nuevo)

    if guardar_expedientes():
        print("\nExpediente registrado correctamente.")
        mostrar_expediente(len(expedientes) - 1)
    else:
        expedientes.pop()
        print("El registro se revirtió porque falló el guardado.")


# ==========================================
# 8. BUSCAR POR CÓDIGO
# ==========================================

def opcion_buscar_codigo():
    print("\n--- BUSCAR POR CÓDIGO ---")

    codigo = solicitar_codigo()
    indice = buscar_por_codigo(codigo)

    if indice is None:
        print("No se encontró el expediente.")
        return

    mostrar_expediente(indice)


# ==========================================
# 9. BUSCAR POR NÚMERO DE DOCUMENTO
# ==========================================


def buscar_por_documento():
    print("\n--- BUSCAR POR NÚMERO DE DOCUMENTO ---")

    numero = input("Número de documento: ").strip()
    indices = buscar_por_numero_documento(numero)

    if not indices:
        print("No se encontró ningún expediente con ese documento.")
        return

    for indice in indices:
        mostrar_expediente(indice)

    print(f"Total de expedientes encontrados: {len(indices)}")


# ==========================================
# 10. BUSCAR POR NOMBRE
# ==========================================

def buscar_por_nombre():
    print("\n--- BUSCAR POR NOMBRE ---")

    nombre = input("Nombre o parte del nombre: ").strip().casefold()

    if not nombre:
        print("Debes ingresar un nombre.")
        return

    encontrados = 0

    for i, expediente in enumerate(expedientes):
        if nombre in expediente["nombre_completo"].casefold():
            mostrar_expediente(i)
            encontrados += 1

    print(f"Total encontrados: {encontrados}")


# ==========================================
# 11. MOSTRAR TODOS
# ==========================================

def mostrar_todos():
    print("\n--- TODOS LOS EXPEDIENTES ---")

    if not expedientes:
        print("No hay expedientes registrados.")
        return

    for i in range(len(expedientes)):
        mostrar_expediente(i)

    print(f"Total de expedientes: {len(expedientes)}")


# ==========================================
# 12. ACTUALIZAR EXPEDIENTE
# ==========================================

def actualizar_expediente():
    print("\n--- ACTUALIZAR EXPEDIENTE ---")

    codigo = solicitar_codigo()
    i = buscar_por_codigo(codigo)

    if i is None:
        print("No se encontró el expediente.")
        return

    original = expedientes[i]
    mostrar_expediente(i)

    print("\nDeja vacío un campo para conservar el valor actual.")

    nuevo = original.copy()

    nombre = input("Nuevo nombre completo: ").strip()

    if nombre:
        valido, error = validar_nombre(nombre)

        if not valido:
            print(error)
            return

        nuevo["nombre_completo"] = nombre

    cambiar_identidad = input(
        "¿Cambiar tipo o número de identidad? (S/N): "
    ).strip().upper()

    if cambiar_identidad == "S":
        tipo, numero = solicitar_identidad()

        nuevo["tipo_documento_identidad"] = tipo
        nuevo["numero_documento"] = numero

    cambiar_tipo = input(
        "¿Cambiar tipo de documento presentado? (S/N): "
    ).strip().upper()

    if cambiar_tipo == "S":
        nuevo["tipo_documento_presentado"] = seleccionar_opcion(
            "Tipo de documento presentado:",
            TIPOS_DOCUMENTO
        )

    asunto = input("Nuevo asunto: ").strip()

    if asunto:
        valido, error = validar_asunto(asunto)

        if not valido:
            print(error)
            return

        nuevo["asunto"] = asunto

    cantidad = input("Nueva cantidad de folios: ").strip()

    if cantidad:
        valido, error = validar_folios(cantidad)

        if not valido:
            print(error)
            return

        nuevo["folios"] = int(cantidad)

    if nuevo == original:
        print("No se realizaron cambios.")
        return

    nuevo["fecha_actualizacion"] = datetime.now().strftime("%Y-%m-%d")
    expedientes[i] = nuevo

    # La fecha de recepción original se conserva.
    if guardar_expedientes():
        print("Expediente actualizado correctamente.")
        mostrar_expediente(i)
    else:
        expedientes[i] = original
        print("Los cambios se revirtieron porque falló el guardado.")


# ==========================================
# 13. ELIMINAR EXPEDIENTE
# ==========================================

def eliminar_expediente():
    print("\n--- ELIMINAR EXPEDIENTE ---")

    codigo = solicitar_codigo()
    i = buscar_por_codigo(codigo)

    if i is None:
        print("No se encontró el expediente.")
        return

    mostrar_expediente(i)

    confirmar = input(
        "¿Confirma la eliminación? (S/N): "
    ).strip().upper()

    if confirmar != "S":
        print("Eliminación cancelada.")
        return

    eliminado = expedientes.pop(i)

    if guardar_expedientes():
        print("Expediente eliminado correctamente.")
    else:
        expedientes.insert(i, eliminado)
        print("La eliminación se revirtió porque falló el guardado.")


# ==========================================
# 14. CAMBIAR ESTADO
# ==========================================

def cambiar_estado():
    print("\n--- CAMBIAR ESTADO ---")

    codigo = solicitar_codigo()
    i = buscar_por_codigo(codigo)

    if i is None:
        print("No se encontró el expediente.")
        return

    mostrar_expediente(i)

    nuevo_estado = seleccionar_opcion(
        "Estados disponibles:",
        ESTADOS
    )

    if nuevo_estado == expedientes[i]["estado"]:
        print("El expediente ya tiene ese estado.")
        return

    estado_anterior = expedientes[i]["estado"]
    fecha_anterior = expedientes[i]["fecha_actualizacion"]

    expedientes[i]["estado"] = nuevo_estado
    expedientes[i]["fecha_actualizacion"] = (
        datetime.now().strftime("%Y-%m-%d")
    )

    if guardar_expedientes():
        print("Estado actualizado correctamente.")
        mostrar_expediente(i)
    else:
        expedientes[i]["estado"] = estado_anterior
        expedientes[i]["fecha_actualizacion"] = fecha_anterior
        print("El cambio se revirtió porque falló el guardado.")


# ==========================================
# 15. CONSULTAR POR ESTADO
# ==========================================

def consultar_por_estado():
    print("\n--- CONSULTAR POR ESTADO ---")

    estado_buscado = seleccionar_opcion(
        "Selecciona el estado:",
        ESTADOS
    )

    encontrados = 0

    for i, expediente in enumerate(expedientes):
        if expediente["estado"] == estado_buscado:
            mostrar_expediente(i)
            encontrados += 1

    print(f"Total encontrados: {encontrados}")


# ==========================================
# 16. ESTADÍSTICAS
# ==========================================

def mostrar_estadisticas():
    print("\n--- REPORTE Y ESTADÍSTICAS ---")

    total = len(expedientes)

    if total == 0:
        print("No hay expedientes registrados.")
        return

    total_folios = sum(
        expediente["folios"] for expediente in expedientes
    )

    print(f"Total de expedientes: {total}")
    print(f"Total de folios: {total_folios}")
    print(f"Promedio de folios: {total_folios / total:.2f}")

    print("\nExpedientes por estado:")

    for estado in ESTADOS:
        cantidad = sum(
            1 for expediente in expedientes
            if expediente["estado"] == estado
        )
        print(f"- {estado}: {cantidad}")

    pendientes = sum(
        1 for expediente in expedientes
        if expediente["estado"] != "Atendido"
    )

    print(f"\nPendientes de atención: {pendientes}")

    fechas_validas = [
        expediente["fecha_recepcion"]
        for expediente in expedientes
    ]

    print(f"Fecha de recepción más antigua: {min(fechas_validas)}")


# ==========================================
# 17. MENÚ PRINCIPAL
# ==========================================

def mostrar_menu():
    print("""
=======================================================
                MESA DE PARTES DIGITAL
=======================================================
 1. Registrar expediente
 2. Buscar por código
 3. Buscar por número de documento
 4. Buscar por nombre
 5. Mostrar todos los expedientes
 6. Actualizar expediente
 7. Eliminar expediente
 8. Cambiar estado
 9. Consultar por estado
10. Reporte y estadísticas
11. Salir
=======================================================
""")


# ==========================================
# 18. PROGRAMA PRINCIPAL
# ==========================================

def main():
    print("=" * 55)
    print("             MESA DE PARTES DIGITAL")
    print("=" * 55)
    if not cargar_expedientes():
        print("Sistema cerrado para proteger los datos existentes.")
        return

    opciones = {
        "1": registrar_expediente,
        "2": opcion_buscar_codigo,
        "3": buscar_por_documento,
        "4": buscar_por_nombre,
        "5": mostrar_todos,
        "6": actualizar_expediente,
        "7": eliminar_expediente,
        "8": cambiar_estado,
        "9": consultar_por_estado,
        "10": mostrar_estadisticas
    }

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()

        if opcion == "11":
            if guardar_expedientes():
                print("Datos guardados correctamente.")
                print("Sistema cerrado.")
                break

            print("No se pudo guardar. El sistema permanecerá abierto.")

        elif opcion in opciones:
            opciones[opcion]()

        else:
            print("Opción inválida. Selecciona del 1 al 11.")


if __name__ == "__main__":
    main()
