#!/usr/bin/env python
"""
Script de inicio para el proyecto voice-bot.
Ejecuta el build del frontend y luego inicia el servidor backend.
"""
import subprocess
import sys
import os

# Activar el entorno virtual si no está activo
def activate_venv():
    """Activa el entorno virtual si no está ya activo."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Determinar el ejecutable de Python según el sistema operativo
    if sys.platform == "win32":
        venv_python = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    else:
        venv_python = os.path.join(base_dir, ".venv", "bin", "python")
    
    # Verificar que el entorno virtual existe
    if not os.path.exists(venv_python):
        print("❌ Error: No se encontró el entorno virtual", file=sys.stderr)
        print(f"Esperado en: {venv_python}", file=sys.stderr)
        print("Crea el entorno virtual ejecutando: python -m venv .venv")
        sys.exit(1)
    
    # Si no estamos usando el Python del entorno virtual, reiniciar con él
    if sys.executable != venv_python:
        print(f"🔄 Reiniciando con el entorno virtual...")
        os.execv(venv_python, [venv_python] + sys.argv)

# Activar entorno virtual primero
activate_venv()

# Ahora sí, importar las dependencias
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


def main():
    """Ejecuta el build del frontend y luego inicia el servidor backend."""
    
    # Obtener el directorio base del proyecto
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Obtener la ruta del frontend desde .env
    frontend_path = os.getenv("FRONTEND_PATH", "gas-app")
    
    # Determinar el ejecutable de Python según el sistema operativo
    if sys.platform == "win32":
        python_executable = os.path.join(base_dir, ".venv", "Scripts", "python.exe")
    else:
        python_executable = os.path.join(base_dir, ".venv", "bin", "python")
    
    # Verificar que el entorno virtual existe
    if not os.path.exists(python_executable):
        print("❌ Error: No se encontró el entorno virtual", file=sys.stderr)
        print(f"Esperado en: {python_executable}", file=sys.stderr)
        print("Crea el entorno virtual ejecutando: python -m venv .venv")
        sys.exit(1)
    
    # Rutas
    chat_bot_dir = os.path.join(base_dir, frontend_path)
    
    print("=" * 60)
    print("🚀 Iniciando Voice Bot")
    print("=" * 60)
    print(f"🐍 Usando Python: {python_executable}")
    print(f"📁 Frontend: {frontend_path}")
    print("=" * 60)
    
    # Paso 1: Build del frontend
    print("\n📦 Construyendo el frontend (npm run build)...")
    print("-" * 60)
    
    try:
        # En Windows, usar shell=True para que encuentre npm correctamente
        if sys.platform == "win32":
            result = subprocess.run(
                f'npm run build --prefix "./{frontend_path}"',
                cwd=base_dir,
                shell=True,
                check=True
            )
        else:
            result = subprocess.run(
                ["npm", "run", "build", "--prefix", f"./{frontend_path}"],
                cwd=base_dir,
                check=True
            )
        print("✅ Build del frontend completado exitosamente")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error durante el build del frontend: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Error: npm no está instalado o no se encuentra en el PATH", file=sys.stderr)
        sys.exit(1)
    
    # Paso 2: Iniciar el servidor backend
    print("\n🐍 Iniciando el servidor backend...")
    print("-" * 60)
    
    try:
        # Ejecutar el servidor Python
        subprocess.run(
            [python_executable, "-m", "app.main"],
            cwd=base_dir,
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar el servidor backend: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"❌ Error: Python no se encuentra en {python_executable}", file=sys.stderr)
        print("Asegúrate de que el entorno virtual esté configurado correctamente.")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Proceso interrumpido por el usuario")
        sys.exit(0)
