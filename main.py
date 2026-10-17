
import csv
import os
import re
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DEL SISTEMA
# ==========================================

ARCHIVO = "expedientes.csv"
ARCHIVO_CONTADOR = "ultimo_codigo.txt"
ARCHIVO_TEMPORAL = ARCHIVO + ".tmp"

CAMPOS = [
    "codigo",
    "remitente",
    "asunto",
    "fecha",
    "folios",
    "estado",
    "fecha_actualizacion"
]

ESTADOS = [
    "Registrado",
    "En revisión",
    "Derivado",
    "Atendido"
]

codigos = []
remitentes = []
asuntos = []
fechas = []
folios = []
estados = []
fechas_actualizacion = []


# ==========================================
# 1. VALIDACIONES
# ==========================================

def validar_texto(texto, campo):
    if not texto.strip():
        return False, f"El campo {campo} es obligatorio."

    if not any(caracter.isalpha() for caracter in texto):
        return False, f"El campo {campo} debe contener letras."

    permitidos = ".,'-"

    if not all(
        caracter.isalpha()
        or caracter.isspace()
        or caracter in permitidos
        for caracter in texto
    ):
        return False, (
            f"El campo {campo} contiene caracteres no permitidos."
        )

    return True, "Dato válido."


def validar_fecha(fecha):
    try:
        fecha_convertida = datetime.strptime(
            fecha, "%Y-%m-%d"
        ).date()

        # strptime puede aceptar algunas variaciones de formato.
        if fecha_convertida.strftime("%Y-%m-%d") != fecha:
            return False, "Use el formato AAAA-MM-DD."

        if fecha_convertida > datetime.now().date():
            return False, "No se permiten fechas futuras."

        return True, "Fecha válida."

    except ValueError:
        return False, "Fecha inválida. Use el formato AAAA-MM-DD."


def validar_folios(cantidad):
    if not cantidad.isdigit():
        return False, "Los folios deben ser números enteros."

    if int(cantidad) <= 0:
        return False, "Los folios deben ser mayores que cero."

    return True, "Cantidad válida."


def solicitar_texto(mensaje, campo):
    while True:
        texto = input(mensaje).strip()
        valido, respuesta = validar_texto(texto, campo)

        if valido:
            return texto

        print(respuesta)


def solicitar_folios():
    while True:
        cantidad = input("Cantidad de folios: ").strip()
        valido, respuesta = validar_folios(cantidad)

        if valido:
            return int(cantidad)

        print(respuesta)


def solicitar_codigo():
    while True:
        numero = input(
            "Ingresa el código (solo 3 números, ej. 001): "
        ).strip()

        if numero.isdigit() and len(numero) == 3:
            return f"EXP-{numero}"

        print(
            "Error: ingresa exactamente 3 números, "
            "por ejemplo 001."
        )


def listas_sincronizadas():
    cantidades = {
        len(codigos),
        len(remitentes),
        len(asuntos),
        len(fechas),
        len(folios),
        len(estados),
        len(fechas_actualizacion)
    }

    return len(cantidades) == 1


# ==========================================
# 2. GENERACIÓN DE CÓDIGOS
# ==========================================

def generar_codigo():
    mayor_registrado = 0

    for codigo in codigos:
        coincidencia = re.fullmatch(r"EXP-(\d{3})", codigo)

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
# 3. BÚSQUEDA POR CÓDIGO
# ==========================================

def buscar_por_codigo(codigo):
    for i, valor in enumerate(codigos):
        if valor == codigo:
            return i

    return None


# ==========================================
# 4. CARGAR EXPEDIENTES
# ==========================================

def cargar_expedientes():
    if not os.path.exists(ARCHIVO):
        print("Todavía no existe un archivo de expedientes.")
        return

    # Se cargan primero en listas temporales para evitar
    # dejar las listas principales parcialmente modificadas.
    registros = []
    codigos_vistos = set()
    rechazados = 0

    try:
        with open(
            ARCHIVO,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as archivo:

            lector = csv.DictReader(archivo)

            columnas = lector.fieldnames or []

            if not all(campo in columnas for campo in CAMPOS[:5]):
                print(
                    "Error: el CSV no contiene las columnas "
                    "obligatorias. No se cargaron expedientes."
                )
                return

            for fila in lector:
                try:
                    codigo = (fila.get("codigo") or "").strip().upper()
                    remitente = (fila.get("remitente") or "").strip()
                    asunto = (fila.get("asunto") or "").strip()
                    fecha = (fila.get("fecha") or "").strip()
                    cantidad_texto = (fila.get("folios") or "").strip()

                    estado = (
                        fila.get("estado") or "Registrado"
                    ).strip()

                    fecha_actualizacion = (
                        fila.get("fecha_actualizacion") or fecha
                    ).strip()

                    if not re.fullmatch(r"EXP-\d{3}", codigo):
                        rechazados += 1
                        continue

                    if codigo in codigos_vistos:
                        rechazados += 1
                        continue

                    valido_remitente, _ = validar_texto(
                        remitente, "remitente"
                    )
                    valido_asunto, _ = validar_texto(
                        asunto, "asunto"
                    )

                    if not valido_remitente or not valido_asunto:
                        rechazados += 1
                        continue

                    valido_fecha, _ = validar_fecha(fecha)

                    if not valido_fecha:
                        rechazados += 1
                        continue

                    valido_actualizacion, _ = validar_fecha(
                        fecha_actualizacion
                    )

                    if not valido_actualizacion:
                        rechazados += 1
                        continue

                    valido_folios, _ = validar_folios(
                        cantidad_texto
                    )

                    if not valido_folios:
                        rechazados += 1
                        continue

                    cantidad = int(cantidad_texto)

                    if estado not in ESTADOS:
                        estado = "Registrado"

                    registros.append({
                        "codigo": codigo,
                        "remitente": remitente,
                        "asunto": asunto,
                        "fecha": fecha,
                        "folios": cantidad,
                        "estado": estado,
                        "fecha_actualizacion": fecha_actualizacion
                    })

                    codigos_vistos.add(codigo)

                except (ValueError, TypeError, KeyError):
                    rechazados += 1

        # Pasar los registros válidos a las listas principales.
        for registro in registros:
            codigos.append(registro["codigo"])
            remitentes.append(registro["remitente"])
            asuntos.append(registro["asunto"])
            fechas.append(registro["fecha"])
            folios.append(registro["folios"])
            estados.append(registro["estado"])
            fechas_actualizacion.append(
                registro["fecha_actualizacion"]
            )

        print(f"Expedientes cargados: {len(registros)}")

        if rechazados:
            print(
                f"Aviso: se omitieron {rechazados} filas "
                "por contener datos inválidos."
            )

        if not listas_sincronizadas():
            print("Error interno: las listas no están sincronizadas.")

    except (OSError, csv.Error, UnicodeError) as error:
        print(
            f"Error al leer el archivo. "
            f"No se guardaron cambios: {error}"
        )


# ==========================================
# 5. GUARDAR EXPEDIENTES
# ==========================================

def guardar_expedientes():
    if not listas_sincronizadas():
        print(
            "Error: las listas de datos no están sincronizadas. "
            "No se guardó el archivo."
        )
        return False

    try:
        # Se escribe primero un archivo temporal para reducir
        # el riesgo de perder el CSV si ocurre un error.
        with open(
            ARCHIVO_TEMPORAL,
            "w",
            newline="",
            encoding="utf-8"
        ) as archivo:

            escritor = csv.DictWriter(
                archivo,
                fieldnames=CAMPOS
            )

            escritor.writeheader()

            for i in range(len(codigos)):
                escritor.writerow({
                    "codigo": codigos[i],
                    "remitente": remitentes[i],
                    "asunto": asuntos[i],
                    "fecha": fechas[i],
                    "folios": folios[i],
                    "estado": estados[i],
                    "fecha_actualizacion": fechas_actualizacion[i]
                })

        # Sustituye el archivo anterior solo cuando termina la escritura.
        os.replace(ARCHIVO_TEMPORAL, ARCHIVO)
        return True

    except (OSError, csv.Error, UnicodeError) as error:
        print(f"Error al guardar los expedientes: {error}")

        try:
            if os.path.exists(ARCHIVO_TEMPORAL):
                os.remove(ARCHIVO_TEMPORAL)
        except OSError:
            pass

        return False


# ==========================================
# 6. MOSTRAR UN EXPEDIENTE
# ==========================================

def mostrar_expediente(i):
    print("\n" + "=" * 50)
    print(f"Código                 : {codigos[i]}")
    print(f"Remitente              : {remitentes[i]}")
    print(f"Asunto                 : {asuntos[i]}")
    print(f"Fecha de registro      : {fechas[i]}")
    print(f"Folios                 : {folios[i]}")
    print(f"Estado                 : {estados[i]}")
    print(f"Última actualización   : {fechas_actualizacion[i]}")
    print("=" * 50)


# ==========================================
# 7. REGISTRAR EXPEDIENTE
# ==========================================

def registrar_expediente():
    print("\n--- REGISTRO DE EXPEDIENTE ---")

    remitente = solicitar_texto(
        "Nombre del remitente: ", "remitente"
    )

    asunto = solicitar_texto(
        "Asunto del expediente: ", "asunto"
    )

    cantidad = solicitar_folios()
    fecha = datetime.now().strftime("%Y-%m-%d")
    codigo = generar_codigo()

    if codigo is None:
        print("No se pudo generar un código.")
        return

    # Guardar el tamaño anterior para poder revertir el registro.
    codigos.append(codigo)
    remitentes.append(remitente)
    asuntos.append(asunto)
    fechas.append(fecha)
    folios.append(cantidad)
    estados.append("Registrado")
    fechas_actualizacion.append(fecha)

    if guardar_expedientes():
        print(f"\nCódigo generado: {codigo}")
        print(f"Fecha de registro: {fecha}")
        print("Estado inicial: Registrado")
        print("Expediente registrado correctamente.")
    else:
        for lista in (
            codigos,
            remitentes,
            asuntos,
            fechas,
            folios,
            estados,
            fechas_actualizacion
        ):
            lista.pop()

        print("El registro se revirtió porque falló el guardado.")


# ==========================================
# 8. BUSCAR POR CÓDIGO
# ==========================================

def opcion_buscar_codigo():
    print("\n--- BUSCAR EXPEDIENTE ---")

    codigo = solicitar_codigo()
    indice = buscar_por_codigo(codigo)

    if indice is not None:
        mostrar_expediente(indice)
    else:
        print("No se encontró el expediente.")


# ==========================================
# 9. BUSCAR POR REMITENTE
# ==========================================

def buscar_por_remitente():
    print("\n--- BUSCAR POR REMITENTE ---")

    nombre = input(
        "Nombre o parte del nombre: "
    ).strip().casefold()

    if not nombre:
        print("Debes ingresar un nombre.")
        return

    encontrados = 0

    for i, remitente in enumerate(remitentes):
        if nombre in remitente.casefold():
            mostrar_expediente(i)
            encontrados += 1

    print(f"Total encontrados: {encontrados}")


# ==========================================
# 10. MOSTRAR TODOS
# ==========================================

def mostrar_todos():
    print("\n--- LISTA DE EXPEDIENTES ---")

    if not codigos:
        print("No hay expedientes registrados.")
        return

    for i in range(len(codigos)):
        mostrar_expediente(i)

    print(f"Total de expedientes: {len(codigos)}")


# ==========================================
# 11. ORDENAR EXPEDIENTES
# ==========================================

def mostrar_ordenados():
    print("\n--- ORDENAR EXPEDIENTES ---")

    if not codigos:
        print("No hay expedientes para ordenar.")
        return

    print("1. Ordenar por código")
    print("2. Ordenar por fecha")

    opcion = input("Seleccione el criterio: ").strip()

    if opcion == "1":
        indices = sorted(
            range(len(codigos)),
            key=lambda i: codigos[i]
        )

    elif opcion == "2":
        indices = sorted(
            range(len(fechas)),
            key=lambda i: (fechas[i], codigos[i])
        )

    else:
        print("Opción no válida.")
        return

    for i in indices:
        mostrar_expediente(i)


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

    mostrar_expediente(i)

    print("\nDeja vacío un campo para conservar su valor.")
    print("La fecha original de registro no se puede modificar.")

    nuevo_remitente = input("Nuevo remitente: ").strip()
    nuevo_asunto = input("Nuevo asunto: ").strip()
    nuevos_folios = input("Nueva cantidad de folios: ").strip()

    remitente_final = remitentes[i]
    asunto_final = asuntos[i]
    folios_final = folios[i]

    # Validar el remitente si se escribió un nuevo valor.
    if nuevo_remitente:
        valido, mensaje = validar_texto(
            nuevo_remitente, "remitente"
        )

        if not valido:
            print(mensaje)
            return

        remitente_final = nuevo_remitente

    # Validar el asunto si se escribió un nuevo valor.
    if nuevo_asunto:
        valido, mensaje = validar_texto(
            nuevo_asunto, "asunto"
        )

        if not valido:
            print(mensaje)
            return

        asunto_final = nuevo_asunto

    # Validar la cantidad de folios si se escribió un nuevo valor.
    if nuevos_folios:
        valido, mensaje = validar_folios(nuevos_folios)

        if not valido:
            print(mensaje)
            return

        folios_final = int(nuevos_folios)

    hubo_cambios = (
        remitente_final != remitentes[i]
        or asunto_final != asuntos[i]
        or folios_final != folios[i]
    )

    if not hubo_cambios:
        print("No se realizaron cambios.")
        return

    valores_anteriores = (
        remitentes[i],
        asuntos[i],
        folios[i],
        fechas_actualizacion[i]
    )

    remitentes[i] = remitente_final
    asuntos[i] = asunto_final
    folios[i] = folios_final
    fechas_actualizacion[i] = datetime.now().strftime("%Y-%m-%d")

    # La fecha de registro se conserva sin modificaciones.
    if guardar_expedientes():
        print("\nExpediente actualizado correctamente.")
        mostrar_expediente(i)
    else:
        (
            remitentes[i],
            asuntos[i],
            folios[i],
            fechas_actualizacion[i]
        ) = valores_anteriores

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

    listas = (
        codigos,
        remitentes,
        asuntos,
        fechas,
        folios,
        estados,
        fechas_actualizacion
    )

    datos = tuple(lista[i] for lista in listas)

    for lista in listas:
        lista.pop(i)

    if guardar_expedientes():
        print("Expediente eliminado correctamente.")
    else:
        for lista, valor in zip(listas, datos):
            lista.insert(i, valor)

        print("La eliminación se revirtió porque falló el guardado.")


# ==========================================
# 14. CAMBIAR ESTADO
# ==========================================

def cambiar_estado():
    print("\n--- CAMBIAR ESTADO DEL EXPEDIENTE ---")

    codigo = solicitar_codigo()
    i = buscar_por_codigo(codigo)

    if i is None:
        print("No se encontró el expediente.")
        return

    mostrar_expediente(i)

    print("\nEstados disponibles:")

    for numero, estado in enumerate(ESTADOS, start=1):
        print(f"{numero}. {estado}")

    opcion = input("Seleccione el nuevo estado: ").strip()

    if (
        not opcion.isdigit()
        or not 1 <= int(opcion) <= len(ESTADOS)
    ):
        print("Opción de estado no válida.")
        return

    nuevo_estado = ESTADOS[int(opcion) - 1]

    if nuevo_estado == estados[i]:
        print("El expediente ya tiene ese estado.")
        return

    estado_anterior = estados[i]
    fecha_anterior = fechas_actualizacion[i]

    estados[i] = nuevo_estado
    fechas_actualizacion[i] = datetime.now().strftime("%Y-%m-%d")

    if guardar_expedientes():
        print(f"Estado actualizado: {estados[i]}")
        print(f"Fecha de registro: {fechas[i]}")
        print(
            "Última actualización: "
            f"{fechas_actualizacion[i]}"
        )
    else:
        estados[i] = estado_anterior
        fechas_actualizacion[i] = fecha_anterior

        print("El cambio de estado se revirtió porque falló el guardado.")


# ==========================================
# 15. CONSULTAR POR ESTADO
# ==========================================

def consultar_por_estado():
    print("\n--- CONSULTAR EXPEDIENTES POR ESTADO ---")

    for numero, estado in enumerate(ESTADOS, start=1):
        print(f"{numero}. {estado}")

    opcion = input("Seleccione el estado: ").strip()

    if (
        not opcion.isdigit()
        or not 1 <= int(opcion) <= len(ESTADOS)
    ):
        print("Opción no válida.")
        return

    estado_buscado = ESTADOS[int(opcion) - 1]
    encontrados = 0

    for i, estado in enumerate(estados):
        if estado == estado_buscado:
            mostrar_expediente(i)
            encontrados += 1

    print(f"Expedientes encontrados: {encontrados}")


# ==========================================
# 16. ESTADÍSTICAS Y REPORTE
# ==========================================

def mostrar_estadisticas():
    print("\n--- REPORTE DEL SISTEMA ---")

    total = len(codigos)

    if total == 0:
        print("No hay expedientes registrados.")
        return

    total_folios = sum(folios)

    print(f"Total de expedientes: {total}")
    print(f"Total de folios: {total_folios}")
    print(f"Promedio de folios: {total_folios / total:.2f}")

    print("\nCantidad por estado:")

    for estado in ESTADOS:
        print(f"- {estado}: {estados.count(estado)}")

    pendientes = sum(
        1 for estado in estados
        if estado != "Atendido"
    )

    print(f"\nExpedientes pendientes de atención: {pendientes}")

    if fechas:
        print(f"Fecha del expediente más antiguo: {min(fechas)}")


# ==========================================
# 17. MENÚ PRINCIPAL
# ==========================================

def mostrar_menu():
    print("""
==================================================
             MESA DE PARTES DIGITAL
==================================================
 1. Registrar expediente
 2. Buscar expediente por código
 3. Buscar por remitente
 4. Mostrar todos los expedientes
 5. Ordenar expedientes
 6. Actualizar expediente
 7. Eliminar expediente
 8. Reporte y estadísticas
 9. Cambiar estado del expediente
10. Consultar expedientes por estado
11. Salir
==================================================
""")


# ==========================================
# 18. EJECUCIÓN DEL SISTEMA
# ==========================================

def main():
    print("=" * 50)
    print("       SISTEMA DE MESA DE PARTES DIGITAL")
    print("=" * 50)

    cargar_expedientes()

    opciones = {
        "1": registrar_expediente,
        "2": opcion_buscar_codigo,
        "3": buscar_por_remitente,
        "4": mostrar_todos,
        "5": mostrar_ordenados,
        "6": actualizar_expediente,
        "7": eliminar_expediente,
        "8": mostrar_estadisticas,
        "9": cambiar_estado,
        "10": consultar_por_estado
    }

    while True:
        mostrar_menu()
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "11":
            if guardar_expedientes():
                print("Datos guardados correctamente.")
                print("Sistema cerrado correctamente.")
                break

            print(
                "No se pudo confirmar el guardado. "
                "El sistema permanecerá abierto."
            )

        elif opcion in opciones:
            opciones[opcion]()

        else:
            print("Opción no válida. Seleccione del 1 al 11.")


if __name__ == "__main__":
    main()
