import subprocess
import os
import sys
import time
import json
import signal
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from pathlib import Path
from datetime import datetime

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
BRAND = "NetLeafy Scanner"
VERSION = "2.0"
PASTE_URL = "https://code-leafy.github.io/NetLeafy"
CHANNEL = "https://t.me/codeleafy"
RESULTS_FILE = Path.home() / ".netleafy" / "last_scan.json"

R, B, DIM = "\033[0m", "\033[1m", "\033[2m"
CY, WH = "\033[96m", "\033[97m"

BAD_CODES = {"000", "403", "404", "502", "503", "521", "522", "523", "530"}

# ─── DATABASES ────────────────────────────────────────────────────────────────
DOMAINS = sorted(list(set([
    "akamaihd.net", "argo-cd.readthedocs.io", "blog.helm.sh", "calico.org", 
    "cert-manager.io", "cilium.io", "cloudflare.com", "cloudfront.net", 
    "cluster-api.sigs.k8s.io", "cluster-proportional-autoscaler.sigs.k8s.io", 
    "cncf.io", "container.sigs.k8s.io", "containerd.io", "controller-runtime.sigs.k8s.io", 
    "crossplane.io", "descheduler.sigs.k8s.io", "docs.helm.sh", "docusign.com", 
    "etcd.io", "external-dns.sigs.k8s.io", "fastly-edge.com", "fluxcd.io", 
    "gateway-api.sigs.k8s.io", "github.io", "grafana.com", "harbor.io", 
    "helm.sh", "herokuapp.com", "hierarchical-namespaces.sigs.k8s.io", 
    "image-builder.sigs.k8s.io", "istio.io", "jobset.sigs.k8s.io", "kaniko.sigs.k8s.io", 
    "keda.sh", "kind.sigs.k8s.io", "kops.sigs.k8s.io", "krew.sigs.k8s.io", 
    "kubectl.docs.kubernetes.io", "kubebuilder.io", "kubernetes.io", 
    "kueue.sigs.k8s.io", "kustomize.sigs.k8s.io", "kwok.sigs.k8s.io", 
    "letsencrypt.org", "linkerd.io", "longhorn.io", "metrics-server.sigs.k8s.io", 
    "minikube.sigs.k8s.io", "netlify.app", "node-feature-discovery.sigs.k8s.io", 
    "nuxt.com", "nuxr.com", "openebs.io", "operatorframework.io", "pages.dev", 
    "pnpm.io", "prometheus-operator.sigs.k8s.io", "prometheus.io", 
    "registry.k8s.io", "rook.io", "scheduler-plugins.sigs.k8s.io", 
    "secrets-store-csi-driver.sigs.k8s.io", "security-profiles-operator.sigs.k8s.io", 
    "service-apis.sigs.k8s.io", "smashingmagazine.com", "tekton.dev", 
    "vercel.app", "vitejs.dev", "vuejs.org"
])))

IPS = sorted(list(set([
    "104.16.80.15", "104.17.96.15", "104.18.25.10", "104.18.25.196", "104.18.32.45",
    "104.198.14.52", "104.21.1.100", "104.21.33.34", "104.21.40.50", "104.21.60.220",
    "104.21.63.202", "104.22.10.20", "13.224.50.30", "13.32.50.30", "136.243.128.223",
    "138.201.54.122", "142.54.178.211", "144.76.1.88", "148.251.100.110", "148.251.65.39",
    "15.197.167.100", "15.197.167.90", "162.158.100.50", "168.119.202.236", "172.64.32.100",
    "172.66.40.100", "172.67.150.14", "172.67.158.128", "172.67.70.100", "172.67.80.200",
    "178.22.122.101", "178.63.240.111", "18.160.10.40", "184.171.110.10", "185.134.23.172",
    "185.53.177.50", "188.114.96.10", "188.114.96.200", "188.114.96.3", "188.114.96.6",
    "188.114.97.20", "188.114.97.3", "188.114.97.6", "188.114.98.0", "188.114.98.100",
    "188.114.99.0", "188.114.99.150", "188.40.147.23", "188.40.181.55", "198.202.211.1",
    "198.252.206.1", "204.12.192.223", "204.12.196.34", "212.83.100.120", "213.180.193.56",
    "216.150.1.193", "216.198.79.3", "216.239.38.120", "23.185.0.3", "3.160.200.10",
    "3.162.200.50", "3.162.247.34", "3.162.247.38", "3.162.247.45", "3.162.247.77",
    "3.33.186.135", "34.160.100.20", "34.96.108.209", "35.157.26.135", "35.186.200.50",
    "37.16.18.81", "40.114.177.246", "49.13.100.70", "5.161.50.60", "5.9.210.65",
    "5.9.248.38", "50.7.5.83", "50.7.5.85", "50.7.85.43", "50.7.87.2", "50.7.87.3",
    "50.7.87.4", "50.7.87.5", "52.222.214.108", "52.222.214.124", "52.222.214.38",
    "52.222.214.99", "54.232.119.62", "63.141.252.203", "63.141.252.207", "63.176.8.218",
    "65.108.50.80", "65.109.34.234", "75.2.60.5", "76.76.21.112", "76.76.21.21",
    "83.136.211.95", "85.10.207.48", "85.10.207.51", "88.99.249.74", "91.99.175.105",
    "94.130.13.19", "94.130.33.41", "94.130.50.12", "94.130.70.160", "95.216.69.37"
])))

# ─── PROFILES ─────────────────────────────────────────────────────────────────
PERF_PROFILES = {
    "1": {"name": "Low-End Mobile / Termux", "threads": 15, "timeout": 6, "ping_count": 2},
    "2": {"name": "Mid-Range Mobile",        "threads": 30, "timeout": 4, "ping_count": 3},
    "3": {"name": "Desktop / Laptop",        "threads": 60, "timeout": 3, "ping_count": 4},
    "4": {"name": "High-End PC / Server",    "threads": 120,"timeout": 2, "ping_count": 5},
    "5": {"name": "Custom",                  "threads": None,"timeout": None,"ping_count": None},
}

DNS_PROFILES = {
    "1": {"name": "Direct (System DNS)", "servers": None},
    "2": {"name": "Shecan DNS Bypass",  "servers": ["178.22.122.101", "185.51.200.2"]},
    "3": {"name": "Cloudflare DNS",     "servers": ["1.1.1.1", "1.0.0.1"]},
    "4": {"name": "Google DNS",         "servers": ["8.8.8.8", "8.8.4.4"]},
}

STABILITY_FILTERS = {
    "1": {"name": "Top 3 Fastest",  "limit": 3},
    "2": {"name": "Top 5 Fastest",  "limit": 5},
    "3": {"name": "Top 10 Fastest", "limit": 10},
    "4": {"name": "All Working",    "limit": None},
}

# ─── GLOBAL STATE ─────────────────────────────────────────────────────────────
last_scan_results = []
current_profile = None
interrupted = False

# ─── TERMINAL HELPERS ─────────────────────────────────────────────────────────
def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_width():
    try:
        return min(os.get_terminal_size().columns, 80)
    except:
        return 80

def box_header(title):
    print(f"\n{CY}╭── {WH}{B}{title}{R}")

def box_item(idx, name, desc=""):
    d_str = f" {DIM}{desc}{R}" if desc else ""
    print(f"{CY}│ {WH}{idx}{CY}  {WH}{name}{d_str}{R}")

def box_footer():
    print(f"{CY}╰──────────────────────────────────────────────{R}")

def box_text(text):
    print(f"{CY}│ {WH}{text}{R}")

def prompt(text, default=None, choices=None):
    suffix = f" {DIM}[{default}]{R}" if default else ""
    if choices:
        suffix += f" {DIM}({', '.join(choices)}){R}"
    try:
        while True:
            val = input(f"{CY}│ {WH}› {text}{suffix}: {WH}").strip()
            if val:
                if choices and val not in choices:
                    print(f"{CY}│ {WH}⚠ Invalid choice.{R}")
                    continue
                return val
            if default:
                return default
    except KeyboardInterrupt:
        print(f"\n{CY}│ {WH}⚠ Cancelled.{R}\n")
        sys.exit(0)

def print_banner():
    clear()
    logo = f"""{CY}
 _   _      _   _               __       
| \\ | | ___| |_| |    ___  __ _/ _|_   _ 
|  \\| |/ _ \\ __| |   / _ \\/ _` | |_| | | |
| |\\  |  __/ |_| |__|  __/ (_| |  _| |_| |
|_| \\_|\\___|\\__|_____\\___|\\__,_|_|  \\__, |
                                    |___/ {R}
  {WH}{B}S C A N N E R{R} {DIM}v{VERSION}{R}
"""
    print(logo)
    box_header("Information")
    box_text(f"Paste results at : {CY}{PASTE_URL}{R}")
    box_text(f"Telegram         : {CY}{CHANNEL}{R}")
    box_footer()

def progress_bar(done, total, found):
    bar_w = 30
    filled = done * bar_w // total
    pct = done * 100 // total
    bar = f"{WH}{'█' * filled}{DIM}{'░' * (bar_w - filled)}{R}"
    sys.stdout.write(f"\r{' ' * (term_width()-1)}\r{CY}│ {bar} {WH}{B}{pct:3d}%{R} {CY}│ {WH}✓ {found} found{R}")
    sys.stdout.flush()

def erase_line():
    sys.stdout.write(f"\r{' ' * (term_width()-1)}\r")
    sys.stdout.flush()

# ─── SYSTEM CHECKS ────────────────────────────────────────────────────────────
def check_curl():
    try:
        r = subprocess.run(["curl", "-V"], capture_output=True, text=True, timeout=3)
        return r.returncode == 0, ""
    except FileNotFoundError:
        return False, "cURL not in PATH"
    except Exception as e:
        return False, f"cURL error: {e}"

def has_dns_support():
    try:
        r = subprocess.run(
            ["curl", "--dns-servers", "8.8.8.8", "-o", "/dev/null", "-w", "%{http_code}",
             "--max-time", "1", "https://127.0.0.1"],
            capture_output=True, text=True, timeout=2)
        return "unknown option" not in r.stderr and "doesn't support" not in r.stderr
    except:
        return False

def get_output_dir():
    prefix = os.environ.get("PREFIX", "")
    if "termux" in prefix.lower():
        dl = Path.home() / "storage" / "downloads"
        return dl if dl.exists() else Path.home()
    dl = Path.home() / "Downloads"
    return dl if dl.exists() else Path.cwd()

def ensure_results_dir():
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_last_results():
    global last_scan_results
    if RESULTS_FILE.exists():
        try:
            with open(RESULTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                last_scan_results = data.get("results", [])
                return True
        except:
            pass
    return False

def save_last_results(results, meta):
    ensure_results_dir()
    data = {"timestamp": datetime.now().isoformat(), "results": results, "meta": meta}
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ─── PROBING WORKERS ──────────────────────────────────────────────────────────
def _flags():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0

def probe_pair(ip, sni, timeout, dns_servers):
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}:%{time_appconnect}:%{time_total}",
           "--max-time", str(timeout), "--connect-timeout", str(timeout),
           f"https://{sni}/", "--resolve", f"{sni}:443:{ip}",
           "-H", f"Host: {sni}", "-H", "User-Agent: Mozilla/5.0"]
    if dns_servers:
        cmd += ["--dns-servers", ",".join(dns_servers)]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True,
                           creationflags=_flags(), timeout=timeout+2).stdout.strip()
        if not out or ":" not in out:
            return None
        parts = out.split(":")
        if len(parts) < 3 or not parts[1] or not parts[2]:
            return None
        code, tls_s, total_s = parts[0], float(parts[1]), float(parts[2])
        ms = total_s * 1000
        if code in BAD_CODES or ms <= 0 or ms > timeout*1000:
            return None
        return {"ip": ip, "sni": sni, "ms": round(ms, 1), "code": code}
    except:
        return None

def tcp_ping_ip(ip, timeout, count):
    times = []
    for _ in range(count):
        try:
            start = time.time()
            sock = socket.create_connection((ip, 443), timeout=timeout)
            sock.close()
            times.append((time.time() - start) * 1000)
        except Exception:
            pass
    if times:
        avg_ms = sum(times) / len(times)
        return {"ip": ip, "reachable": True, "avg_ms": round(avg_ms, 1)}
    return {"ip": ip, "reachable": False, "avg_ms": None}

# ─── SCAN ENGINES ─────────────────────────────────────────────────────────────
def run_pair_scanner(threads, timeout, dns_servers, target_ips=None, target_snis=None):
    global interrupted
    target_ips = target_ips or IPS
    target_snis = target_snis or DOMAINS
    tasks = [(ip, sni) for ip in target_ips for sni in target_snis]
    total, done, results = len(tasks), 0, []
    found_ips, found_snis = Counter(), Counter()
    
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = [ex.submit(probe_pair, ip, sni, timeout, dns_servers) for ip, sni in tasks]
        try:
            for fut in as_completed(futures):
                done += 1
                try:
                    res = fut.result()
                except:
                    res = None
                progress_bar(done, total, len(results))
                if res:
                    results.append(res)
                    found_ips[res["ip"]] += 1
                    found_snis[res["sni"]] += 1
                    erase_line()
                    print(f"{CY}│ {WH}✓ {res['ip']:<16} {CY}{res['sni']:<35} {WH}{res['ms']:.0f}ms{R} {DIM}{res['code']}{R}")
        except KeyboardInterrupt:
            interrupted = True
            erase_line()
            print(f"{CY}│ {WH}⚠ Stopped — saving {len(results)} results...{R}")
    print()
    return results, found_ips, found_snis

def run_ip_pinger(threads, timeout, count, target_ips=None):
    target_ips = target_ips or IPS
    results, reachable = [], 0
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = [ex.submit(tcp_ping_ip, ip, timeout, count) for ip in target_ips]
        total = len(futures)
        for done, fut in enumerate(as_completed(futures), 1):
            try:
                res = fut.result()
                if res and res["reachable"]:
                    results.append(res)
                    reachable += 1
                    ms_str = f"{res['avg_ms']:.0f}ms" if res["avg_ms"] else "OK"
                    print(f"{CY}│ {WH}✓ {res['ip']:<16} {CY}{ms_str}{R}")
                progress_bar(done, total, reachable)
            except:
                pass
    print()
    return results

def run_stability_check(candidates, threads, timeout, dns_servers):
    stable_results = []
    box_text(f"{DIM}Testing stability: 3 probes per candidate...{R}\n")
    
    def test_candidate(item):
        scores = []
        for _ in range(3):
            res = probe_pair(item["ip"], item["sni"], timeout, dns_servers)
            scores.append(res["ms"] if res and res["ms"] > 0 else 9999)
        avg_ms = sum(scores) / 3
        jitter = max(scores) - min(scores)
        is_stable = jitter < 200 and avg_ms < 1500
        return {**item, "avg_ms": round(avg_ms, 1), "jitter": round(jitter, 1), "stable": is_stable}
        
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futures = [ex.submit(test_candidate, c) for c in candidates]
        try:
            for fut in as_completed(futures):
                res = fut.result()
                status = f"{WH}STABLE{R}" if res["stable"] else f"{DIM}UNSTABLE{R}"
                if res["stable"]:
                    stable_results.append(res)
                print(f"{CY}│ {WH}✓ {res['ip']:<16} {CY}{res['sni']:<30} {WH}{res['avg_ms']:.0f}ms±{res['jitter']:.0f}{R} {status}")
        except KeyboardInterrupt:
            pass
    
    return stable_results

# ─── OUTPUT & SUMMARY ─────────────────────────────────────────────────────────
def save_results(results, top_ips, top_snis, mode, out_dir):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = out_dir / f"NetLeafy_{mode}_{ts}.txt"
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# {BRAND} v{VERSION} | {datetime.now()}\n")
        f.write(f"# Paste these results at: {PASTE_URL}\n")
        f.write(f"# Channel: {CHANNEL}\n\n")
        
        f.write(f"{'='*60}\nTOP IPs ({len(top_ips)})\n{'='*60}\n")
        for ip in top_ips:
            f.write(f"{ip}\n")
        
        f.write(f"\n{'='*60}\nTOP SNIs ({len(top_snis)})\n{'='*60}\n")
        for sni in top_snis:
            f.write(f"{sni}\n")
        
        f.write(f"\n{'='*60}\nAll Verified Pairs (IP | SNI | Latency | HTTP Code)\n{'='*60}\n")
        for r in sorted(results, key=lambda x: x.get("ms", x.get("avg_ms", 9999))):
            ms = r.get("ms", r.get("avg_ms", 0))
            f.write(f"{r['ip']} | {r['sni']} | {ms:.0f}ms | {r.get('code', '200')}\n")
    return path

def print_summary(results, found_ips, found_snis, mode, out_dir):
    if not results:
        box_text(f"{WH}⚠ No results found. Try different settings.{R}")
        box_footer()
        return
    
    top_ips = [ip for ip, _ in found_ips.most_common(20)]
    top_snis = [sni for sni, _ in found_snis.most_common(20)]
    saved = save_results(results, top_ips, top_snis, mode, out_dir)
    
    save_last_results(results, {"ips": len(IPS), "domains": len(DOMAINS), "mode": mode})
    
    box_header("SCAN SUMMARY")
    box_text(f"Top IPs (first 10):")
    for ip in top_ips[:10]:
        box_text(f"  {CY}{ip}{R}")
    
    box_text(f"\nTop SNIs (first 10):")
    for sni in top_snis[:10]:
        box_text(f"  {CY}{sni}{R}")
    
    box_text(f"\nFastest 5 Pairs:")
    for r in sorted(results, key=lambda x: x["ms"])[:5]:
        box_text(f"  {DIM}{r['ms']:.0f}ms{R} {WH}{r['ip']}{R} | {CY}{r['sni']}{R}")
    
    box_text(f"\n📁 Saved : {WH}{saved}{R}")
    box_text(f"✓ Stats : {WH}{len(results)} pairs | {len(top_ips)} IPs | {len(top_snis)} SNIs{R}")
    box_footer()

# ─── MAIN MENU SYSTEM ─────────────────────────────────────────────────────────
def select_profile():
    box_header("System Profile")
    for k, v in PERF_PROFILES.items():
        box_item(k, v['name'])
    box_footer()
    choice = prompt("Select profile", "2", choices=list(PERF_PROFILES.keys()))
    prof = PERF_PROFILES[choice]
    if prof["threads"] is None:
        prof["threads"] = int(prompt("Thread count", "40"))
        prof["timeout"] = int(prompt("Timeout (seconds)", "4"))
        prof["ping_count"] = int(prompt("Ping count per IP", "3"))
    return prof

def select_dns_mode():
    box_header("DNS Mode")
    for k, v in DNS_PROFILES.items():
        box_item(k, v['name'])
    box_footer()
    choice = prompt("Select DNS mode", "1", choices=list(DNS_PROFILES.keys()))
    cfg = DNS_PROFILES[choice]
    if cfg["servers"] and not has_dns_support():
        box_text(f"{WH}⚠ cURL lacks --dns-servers — using system DNS{R}")
        cfg = DNS_PROFILES["1"]
    return cfg

def main_menu():
    print_banner()
    global current_profile
    current_profile = select_profile()
    
    while True:
        print_banner()
        box_header("Main Menu")
        box_item("1", "Auto Find Best", "Ping -> Scan -> Stability Test")
        box_item("2", "IP/SNI Scanner", "Find working IP+SNI combos")
        box_item("3", "IP Pinger", "Test IP TCP latency")
        box_item("4", "Stability Checker", "Re-test stable results")
        box_item("0", "Exit")
        box_footer()
        
        choice = prompt("Select option", "1", choices=["0","1","2","3","4"])
        
        if choice == "0":
            box_text(f"👋 Goodbye!{R}")
            box_footer()
            break
        elif choice == "1":
            run_auto_mode()
        elif choice == "2":
            run_scanner_mode()
        elif choice == "3":
            run_pinger_mode()
        elif choice == "4":
            run_stability_mode()
        
        if not interrupted:
            input(f"{CY}│ {DIM}Press Enter to continue...{R}")

# ─── MODES ────────────────────────────────────────────────────────────────────
def run_auto_mode():
    box_header("Auto Find Best")
    box_text(f"{DIM}1. Ping all IPs to find reachable ones{R}")
    box_text(f"{DIM}2. Scan working IPs with all SNIs{R}")
    box_text(f"{DIM}3. Put working pairs into Stability Test{R}")
    box_text(f"{DIM}4. Display the absolute best pairs{R}")
    box_text("")
    box_text(f"{WH}⚠ This process might take some time.{R}")
    box_footer()
    
    ans = prompt("Proceed?", "y", choices=["y", "n"])
    if ans != "y":
        return
        
    dns_cfg = select_dns_mode()
    out_dir = get_output_dir()
    
    # STEP 1: Ping
    box_header("Step 1/3: Pinging IPs")
    reachable_ip_results = run_ip_pinger(current_profile["threads"], current_profile["timeout"], current_profile["ping_count"])
    working_ips = [r["ip"] for r in reachable_ip_results if r["reachable"]]
    
    if not working_ips:
        box_text("⚠ No working IPs found. Aborting.")
        box_footer()
        return
    
    # STEP 2: Scan
    box_header(f"Step 2/3: Scanning Pairs ({len(working_ips)} IPs × {len(DOMAINS)} SNIs)")
    results, ips_c, snis_c = run_pair_scanner(
        current_profile["threads"], current_profile["timeout"], dns_cfg["servers"], working_ips, DOMAINS
    )
    
    if not results:
        box_text("⚠ No working pairs found. Aborting.")
        box_footer()
        return
        
    # STEP 3: Stability
    box_header(f"Step 3/3: Stability Test ({len(results)} Working Pairs)")
    stable_results = run_stability_check(results, current_profile["threads"], current_profile["timeout"], dns_cfg["servers"])
    
    if not stable_results:
        box_text("⚠ No stable pairs survived. Aborting.")
        box_footer()
        return
        
    # FINAL RESULTS
    stable_results.sort(key=lambda x: x["avg_ms"])
    
    box_header("AUTO MODE - FINAL BEST RESULTS")
    box_text(f"✓ Total Stable Pairs Found: {WH}{len(stable_results)}{R}")
    
    for limit in [3, 5, 10]:
        subset = stable_results[:limit]
        if not subset:
            continue
        box_text("")
        box_text(f"{WH}{B}► TOP {limit} BEST PAIRS{R}")
        for i, r in enumerate(subset, 1):
            box_text(f"  {DIM}{i}.{R} {CY}{r['ip']:<16}{R} {WH}|{R} {CY}{r['sni']:<30}{R} {WH}|{R} {WH}{r['avg_ms']:.0f}ms±{r['jitter']:.0f}{R}")
            
        if len(stable_results) <= limit:
            break
            
    # Save Logic
    top_ips = list(dict.fromkeys([r["ip"] for r in stable_results]))
    top_snis = list(dict.fromkeys([r["sni"] for r in stable_results]))
    
    saved = save_results(stable_results, top_ips[:20], top_snis[:20], "auto_best", out_dir)
    save_last_results(stable_results, {"ips": len(working_ips), "domains": len(DOMAINS), "mode": "auto"})
    
    box_text("")
    box_text(f"📁 Saved Full Results to : {CY}{saved}{R}")
    box_footer()

def run_scanner_mode():
    dns_cfg = select_dns_mode()
    out_dir = get_output_dir()
    total = len(IPS) * len(DOMAINS)
    
    box_header("Scanner Mode")
    box_text(f"DNS     : {CY}{dns_cfg['name']}{R}")
    box_text(f"Profile : {CY}{current_profile['name']} | {current_profile['threads']} thr / {current_profile['timeout']}s{R}")
    box_text(f"Tests   : {CY}{len(IPS)} IPs × {len(DOMAINS)} SNIs = {total:,} combos{R}")
    box_text(f"Output  : {CY}{out_dir}{R}")
    box_footer()
    time.sleep(0.3)
    
    results, ips, snis = run_pair_scanner(
        current_profile["threads"], current_profile["timeout"], dns_cfg["servers"]
    )
    print_summary(results, ips, snis, "pairs", out_dir)

def run_pinger_mode():
    box_header("IP Pinger")
    box_text(f"Testing {len(IPS)} IPs with TCP {current_profile['ping_count']} probes{R}")
    box_footer()
    
    results = run_ip_pinger(current_profile["threads"], current_profile["timeout"], current_profile["ping_count"])
    
    box_header("Pinger Summary")
    if results:
        reachable = [r for r in results if r["avg_ms"]]
        box_text(f"✓ {len(reachable)}/{len(results)} IPs responded")
        if reachable:
            best = sorted(reachable, key=lambda x: x["avg_ms"])[:10]
            fastest_str = ", ".join("{}({:.0f}ms)".format(r["ip"], r["avg_ms"]) for r in best)
            box_text(f"Fastest: {CY}{fastest_str}{R}")
    else:
        box_text(f"⚠ No IPs responded{R}")
    box_footer()

def run_stability_mode():
    if not load_last_results():
        box_header("Stability Checker")
        box_text(f"⚠ No previous scan results found.{R}")
        box_text(f"{DIM}Run Scanner first to generate results.{R}")
        box_footer()
        time.sleep(2)
        return
    
    box_header("Stability Checker")
    box_text(f"Loaded {len(last_scan_results)} results from last scan{R}")
    for k, v in STABILITY_FILTERS.items():
        box_item(k, v['name'])
    box_footer()
    
    limit_choice = prompt("Filter results", "2", choices=list(STABILITY_FILTERS.keys()))
    limit = STABILITY_FILTERS[limit_choice]["limit"]
    
    dns_cfg = select_dns_mode()
    out_dir = get_output_dir()
    
    candidates = sorted(last_scan_results, key=lambda x: x.get("ms", x.get("avg_ms", 9999)))
    if limit:
        candidates = candidates[:limit]
    
    box_header("Testing Stability")
    box_text(f"Testing : {CY}Top {limit or 'ALL'} candidates × 3 probes{R}")
    box_text(f"DNS     : {CY}{dns_cfg['name']}{R}")
    box_footer()
    
    stable = run_stability_check(candidates, current_profile["threads"], current_profile["timeout"], dns_cfg["servers"])
    
    box_header("Stability Summary")
    if stable:
        box_text(f"✓ {len(stable)} stable results found{R}")
        top_ips = [r["ip"] for r in sorted(stable, key=lambda x: x["avg_ms"])]
        top_snis = [r["sni"] for r in sorted(stable, key=lambda x: x["avg_ms"])]
        saved = save_results(stable, Counter(top_ips).most_common(20), Counter(top_snis).most_common(20), "stable", out_dir)
        box_text(f"📁 Saved to : {CY}{saved}{R}")
    else:
        box_text(f"⚠ No stable results found.{R}")
    box_footer()

# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
def main():
    if os.name != "nt":
        try:
            subprocess.run(["termux-wake-lock"], capture_output=True, check=False)
        except:
            pass
    else:
        os.system("color")
    
    ok, msg = check_curl()
    if not ok:
        box_header("Requirement Failed")
        box_text(f"⚠ {msg}")
        box_text("Install cURL: apt install curl | brew install curl | choco install curl")
        box_footer()
        sys.exit(1)
    
    try:
        main_menu()
    except KeyboardInterrupt:
        box_header("Interrupted")
        box_text("👋 Interrupted — results auto-saved.")
        box_footer()
    finally:
        if interrupted:
            os._exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s,f: os._exit(0))
    main()
