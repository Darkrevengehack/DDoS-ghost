# DDoS-ghost
Herramienta de Estrés avanzada 2025

<img src="https://raw.githubusercontent.com/0xAbbarhSF/0xBotNet/main/images%20(3).png">

### Instalación
Requisitos
Python 3.7+
Termux actualizado (o cualquier sistema Linux)
Conexión a Internet
Instalación en Termux

* pkg update -y && pkg upgrade -y
* pkg install python git -y
* git clone https://github.com/Darkrevengehack/DDoS-ghost.git
cd DDoS-ghost
* pip3 install -r requirements.txt

## 📚 Uso

### Uso Básico

python3 ddos_anonymous.py -t [IP_OBJETIVO] -p [PUERTO] -th [HILOS] -m [MÉTODO]
```

### Opciones Disponibles

```
-t, --target      Dirección IP objetivo
-p, --port        Puerto objetivo (0 para aleatorio)
-th, --threads    Número de hilos (default: 50)
-m, --method      Método de ataque: udp, tcp, random (default: random)
-a, --anonymous   Usar modo anónimo con proxies automáticos
-pf, --proxy-file Archivo con lista de proxies
```

### Ejemplos

#### Ataque básico:

python3 ddos_anonymous.py -t 192.168.1.1 -p 80 -th 50 -m tcp
```

#### Ataque con modo anónimo (proxies automáticos):

python ddos_anonymous.py -t 192.168.1.1 -p 80 -a
```

#### Ataque con tu propia lista de proxies:

python ddos_anonymous.py -t 192.168.1.1 -p 80 -pf proxies_socks5anon.txt
```

## 🔒 Proxies

### Formato de archivo de proxies
Puedes crear un archivo de texto con proxies en cualquiera de estos formatos:
```
ip:puerto
ip:puerto:tipo
tipo:ip:puerto
```

Proxies reales
```
socks5:51.158.119.88:1080
socks5:95.216.181.107:9070
socks5:207.180.204.70:48462
socks5:72.210.221.197:4145
socks5:103.240.161.101:6667
socks5:159.89.228.253:38172
socks5:184.178.172.13:15311
socks5:188.166.104.152:39088
socks5:184.181.217.206:4145
socks5:198.8.94.170:4145
socks5:184.170.245.148:4145
socks5:98.170.57.231:4145
socks5:98.162.25.16:4145
socks5:148.251.249.251:1080
socks5:51.79.52.80:3080
socks5:198.8.94.174:39074
socks5:104.248.63.17:30588
socks5:199.102.106.94:4145
socks5:192.111.139.163:19404
socks5:37.187.133.177:55899
```
* o simplemente puedes ejecutar python3 ddos_script.py

### Tipos de proxies soportados
- **HTTP**: Proxies web estándar
- **SOCKS4**: Proxies sin autenticación
- **SOCKS5**: Proxies avanzados con soporte UDP (recomendados)

## 🔄 Anonimato Avanzado

Para maximizar el anonimato durante las pruebas legítimas, se recomienda:

1. Usar una VPN junto con los proxies SOCKS5
2. Configurar Orbot (Tor para Android) para enrutar el tráfico de Termux
3. Usar proxies privados en lugar de proxies públicos gratuitos
4. Cambiar regularmente de ubicación de red
5. Limitar la duración de las pruebas

## 📊 Estadísticas y Monitoreo

La herramienta proporciona estadísticas en tiempo real:
- Paquetes enviados
- Duración del ataque
- Paquetes por segundo
- Rotaciones de proxy

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor, asegúrate de:
- Seguir las pautas de código del proyecto
- No incluir código malicioso
- Documentar adecuadamente los cambios
- Respetar el enfoque ético del proyecto

## 📜 Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo LICENSE para más detalles.

*Este software se proporciona "tal cual", sin garantía de ningún tipo. El autor no se hace responsable por el mal uso o daños causados por esta herramienta.*
<img src="https://raw.githubusercontent.com/0xAbbarhSF/0xBotNet/main/images%20(21).jpeg">
#### Happy

## 📧 Contacto

Para preguntas o sugerencias, abre un issue en este repositorio.
