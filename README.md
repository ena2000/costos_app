# Calculadora de Costos — PUBLISTIK

App de escritorio para Windows (máquina, mano de obra, tinta, materiales e historial).

## Cómo descargar la app

### Opción 1 — Archivo `.exe` (recomendado)

1. Abre las [Releases](https://github.com/ena2000/costos_app/releases) del repositorio.
2. En la versión más reciente, descarga **`CalculadoraCostos-PUBLISTIK.exe`**.
3. Haz doble clic para abrirla.

Si Windows muestra *“Windows protegió tu PC”*, elige **Más información** → **Ejecutar de todas formas**. Es normal: el archivo no está firmado con un certificado de Microsoft.

La base de datos y la configuración se guardan en:

`C:\Users\TU_USUARIO\AppData\Roaming\PUBLISTIK\CostosApp`

Si todavía no hay ninguna Release, entra a la pestaña **Actions**, abre el flujo **Build Windows** más reciente y descarga el artefacto **CalculadoraCostos-PUBLISTIK**.

### Opción 2 — Código fuente (ZIP)

1. En [github.com/ena2000/costos_app](https://github.com/ena2000/costos_app) pulsa **Code** → **Download ZIP**.
2. Extrae la carpeta.
3. Instala [Python 3.12](https://www.python.org/downloads/) (marca *Add python.exe to PATH*).
4. En una terminal, dentro de `COSTOS_APP`:

```bat
python -m pip install -r requirements.txt
python main.py
```

### Generar el `.exe` en tu PC

En Windows, entra a `COSTOS_APP` y ejecuta `build_exe.bat`. El resultado queda en `COSTOS_APP\dist\CalculadoraCostos-PUBLISTIK.exe`.
