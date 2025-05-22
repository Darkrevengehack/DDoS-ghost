# DDoS Ghost 2025 - Herramienta de Pruebas de Estrés Avanzada

<img src="https://raw.githubusercontent.com/0xAbbarhSF/0xBotNet/main/images%20(3).png">

![Versión](https://img.shields.io/badge/Versión-4.0.0-brightgreen)
![Python](https://img.shields.io/badge/Python-3.7+-blue)
![Plataforma](https://img.shields.io/badge/Plataforma-Android/Termux-orange)
![Licencia](https://img.shields.io/badge/Licencia-MIT-yellow)

## ⚠️ Descargo de Responsabilidad

**Esta herramienta está diseñada exclusivamente para fines educativos, de investigación y pruebas de seguridad en entornos controlados y autorizados.**

- El uso de esta herramienta contra sistemas sin permiso explícito es **ILEGAL** y puede resultar en consecuencias legales severas.
- El desarrollador NO se hace responsable del mal uso de esta herramienta.
- Al usar este software, aceptas utilizarlo solo en sistemas que posees o para los cuales tienes autorización explícita para realizar pruebas.

## 🆕 Novedades de la Versión 4.0.0

- ✨ **Menú interactivo** con 5 opciones principales
- 🔄 **Sistema de configuración persistente** (ghost_config.json)
- 📊 **Reportes automáticos** de ataques (ghost_reports.json)
- 🔍 **Verificación avanzada de proxies** con puntuación por velocidad
- 🕵️ **15+ User-Agents reales** actualizados para 2025
- ⏱️ **4 patrones de timing** inteligentes (aggressive, normal, stealth, human_like)
- 🥷 **Modo sigiloso** que simula tráfico web legítimo
- 🎨 **Interfaz mejorada** con colores y estadísticas en tiempo real

<img src="https://raw.githubusercontent.com/0xAbbarhSF/0xBotNet/main/images%20(21).jpeg">

## 📋 Características Completas

### 🎯 Vectores de Ataque
- ✅ **Múltiples protocolos**: TCP, UDP, HTTP
- ✅ **Métodos aleatorios** para mayor efectividad
- ✅ **Puertos configurables** o aleatorios

### 🔒 Anonimato Avanzado
- ✅ **Rotación automática de proxies** SOCKS4/SOCKS5/HTTP
- ✅ **Verificación de proxies** antes del uso
- ✅ **Frecuencia de rotación configurable**
- ✅ **Soporte para archivos de proxies personalizados**

### 🧠 Inteligencia Artificial
- ✅ **Paquetes con contenido aleatorio** para evadir detección
- ✅ **Headers HTTP realistas** que simulan navegadores reales
- ✅ **Patrones de timing humanos** para evitar filtros
- ✅ **Ofuscación avanzada** de firmas de tráfico

### 📱 Optimización para Termux
- ✅ **No requiere permisos root**
- ✅ **Optimizado para dispositivos móviles**
- ✅ **Instalación automática de dependencias**
- ✅ **Interfaz táctil amigable**

## 🛠️ Instalación

### Requisitos
- **Android 7+** con Termux instalado
- **Python 3.7+** (se instala automáticamente)
- **Conexión a Internet** estable

### Instalación Rápida
```bash
# Actualizar Termux
pkg update && pkg upgrade -y

# Instalar dependencias básicas
pkg install python git -y

# Clonar el repositorio
git clone https://github.com/Darkrevengehack/DDoS-ghost.git

# Entrar al directorio
cd DDoS-ghost

# Instalar dependencias Python (opcional - se instalan automáticamente)
pip3 install -r requirements.txt

# Ejecutar
python3 ddos_script.py
```

## 🎮 Uso

### Menú Interactivo
Al ejecutar el script, verás un menú con 5 opciones:

```
════════════════ MENÚ PRINCIPAL ════════════════
[1] Iniciar ataque DDoS
[2] Configuración avanzada  
[3] Ver reportes anteriores
[4] Verificar proxies
[5] Salir
════════════════════════════════════════════════
```

### Uso con Argumentos
```bash
# Ataque básico
python3 ddos_script.py -t 192.168.1.100 -p 80

# Ataque con proxies automáticos
python3 ddos_script.py -t 192.168.1.100 -p 80 -a

# Ataque con archivo de proxies
python3 ddos_script.py -t 192.168.1.100 -p 80 -pf ghost_tunnels.txt

# Modo sigiloso con verificación de proxies
python3 ddos_script.py -t 192.168.1.100 -p 80 -a -v -s

# Configuración completa
python3 ddos_script.py -t 192.168.1.100 -p 80 -th 150 -m tcp -tp stealth -rf 50
```

### Parámetros Disponibles
```
-t, --target          IP objetivo (requerido)
-p, --port            Puerto objetivo (0 para aleatorio)
-th, --threads        Número de hilos (1-500, default: 50)
-m, --method          Método: udp, tcp, random (default: random)
-a, --anonymous       Modo anónimo con proxies automáticos
-pf, --proxy-file     Archivo con lista de proxies
-v, --verify-proxies  Verificar proxies antes de usar
-tp, --timing-pattern Patrón: aggressive, normal, stealth, human_like
-s, --stealth         Activar modo sigiloso
-rf, --rotation-freq  Frecuencia rotación proxies (default: 25)
```

## 🔧 Configuración de Proxies

### Formato de Archivo de Proxies
Crea un archivo `.txt` con proxies en estos formatos:
```
# Formato recomendado
socks5:192.168.1.1:1080
socks4:10.0.0.1:4145
http:203.0.113.1:8080

# Formatos alternativos
192.168.1.1:1080:socks5
10.0.0.1:4145:socks4
203.0.113.1:8080:http

# Formato simple (default: http)
192.168.1.1:8080
10.0.0.2:3128
```

### Fuentes Recomendadas de Proxies
- [ProxyNova](https://www.proxynova.com/proxy-server-list/) - Proxies verificados
- [Free Proxy List](https://free-proxy-list.net/) - Actualización diaria
- [SOCKS Proxy](https://www.socks-proxy.net/) - Específico para SOCKS

## 📊 Características Avanzadas

### Patrones de Timing
- **Aggressive**: 0.001-0.005s (máxima velocidad)
- **Normal**: 0.01-0.05s (equilibrado)
- **Stealth**: 0.1-0.5s (sigiloso)
- **Human_like**: 1.0-3.0s (simula comportamiento humano)

### Modo Sigiloso
- Genera requests HTTP realistas
- Utiliza User-Agents de navegadores reales
- Simula patrones de navegación web normales
- Headers HTTP diversos y aleatorios

### Sistema de Reportes
Los reportes se guardan automáticamente en `ghost_reports.json`:
```json
{
  "timestamp": "2025-01-22T15:30:45",
  "duration": 120.5,
  "packets_sent": 15680,
  "packets_per_second": 130.12,
  "proxy_rotations": 45,
  "proxies_used": 23
}
```

## 🎯 Casos de Uso Legítimos

### Pruebas de Penetración
- Evaluación de la resistencia de servidores propios
- Pruebas de carga en aplicaciones web
- Verificación de sistemas de protección DDoS

### Investigación de Seguridad
- Análisis de patrones de tráfico
- Estudios de comportamiento de red
- Desarrollo de contramedidas

### Educación en Ciberseguridad
- Demostraciones en cursos de seguridad
- Laboratorios de ethical hacking
- Comprensión de ataques de denegación de servicio

## 🔥 Rendimiento

### Optimizaciones para Móviles
- **Uso eficiente de memoria**: Optimizado para dispositivos con RAM limitada
- **Gestión inteligente de hilos**: Previene sobrecarga del sistema
- **Conexiones asíncronas**: Máximo rendimiento con mínimo consumo
- **Rotación de proxies**: Distribución de carga entre múltiples puntos

### Benchmarks Típicos
- **Dispositivo gama baja**: 50-100 paquetes/segundo
- **Dispositivo gama media**: 100-300 paquetes/segundo  
- **Dispositivo gama alta**: 300-500+ paquetes/segundo

## 🛡️ Contramedidas y Detección

### Técnicas Anti-Detección Implementadas
- Rotación automática de proxies cada N paquetes
- User-Agents diversos y actualizados
- Patrones de timing variables
- Paquetes con contenido aleatorio
- Headers HTTP realistas

### Sistemas que Pueden Detectar/Bloquear
- **Cloudflare**: Protección avanzada contra DDoS
- **AWS Shield**: Mitigación automática
- **Fail2Ban**: Bloqueo por patrones de IP
- **Rate limiting**: Límites por conexión/IP

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:
- Haz fork del repositorio
- Crea una rama feature (`git checkout -b feature/mejora`)
- Commit tus cambios (`git commit -am 'Añadir nueva característica'`)
- Push a la rama (`git push origin feature/mejora`)
- Abre un Pull Request

### Directrices para Contribuir
- Mantén el código limpio y bien comentado
- Prueba todas las funcionalidades antes de enviar PR
- Documenta nuevas características
- Respeta la filosofía de uso ético

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](LICENSE) para más detalles.

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/Darkrevengehack/DDoS-ghost/issues)
- **Telegram**: [@Darkrevengehack](https://t.me/Darkrevengehack)
- **Documentación**: [Wiki del proyecto](https://github.com/Darkrevengehack/DDoS-ghost/wiki)

#### Happy Hacking 🕵️

---

**⚠️ Recordatorio Legal**: Este software se proporciona "tal cual", sin garantía de ningún tipo. El autor no se hace responsable por el mal uso o daños causados por esta herramienta. Usar únicamente en sistemas propios o con autorización explícita.
