import subprocess
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import parse_qs, quote, unquote
from collections import Counter
from pathlib import Path

# ─── CONSTANTS ────────────────────────────────────────────────────────────────

BRAND     = "NetLeafy Scanner"
VERSION   = "1.1"
PASTE_URL = "https://code-leafy.github.io/NetLeafy"
CHANNEL   = "https://t.me/codeleafy"

R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"
CY  = "\033[96m"
GR  = "\033[92m"
YL  = "\033[93m"
RD  = "\033[91m"
MG  = "\033[95m"
BL  = "\033[94m"
WH  = "\033[97m"

BAD_CODES = {"000", "403", "502", "503", "521", "522", "523", "530"}

# ─── DATABASES ────────────────────────────────────────────────────────────────

DOMAINS = [
    "helm.sh", "keda.sh", "rook.io", "istio.io", "cilium.io", "fluxcd.io",
    "harbor.io", "calico.org", "linkerd.io", "openebs.io", "tekton.dev",
    "longhorn.io", "blog.helm.sh", "docs.helm.sh", "crossplane.io",
    "kubernetes.io", "kubebuilder.io", "cert-manager.io", "letsencrypt.org",
    "kind.sigs.k8s.io", "kops.sigs.k8s.io", "krew.sigs.k8s.io",
    "kwok.sigs.k8s.io", "kueue.sigs.k8s.io", "jobset.sigs.k8s.io",
    "kaniko.sigs.k8s.io", "minikube.sigs.k8s.io", "operatorframework.io",
    "container.sigs.k8s.io", "kustomize.sigs.k8s.io", "argo-cd.readthedocs.io",
    "cluster-api.sigs.k8s.io", "descheduler.sigs.k8s.io", "gateway-api.sigs.k8s.io",
    "external-dns.sigs.k8s.io", "service-apis.sigs.k8s.io", "image-builder.sigs.k8s.io",
    "kubectl.docs.kubernetes.io", "metrics-server.sigs.k8s.io",
    "scheduler-plugins.sigs.k8s.io", "controller-runtime.sigs.k8s.io",
    "prometheus-operator.sigs.k8s.io", "node-feature-discovery.sigs.k8s.io",
    "hierarchical-namespaces.sigs.k8s.io", "secrets-store-csi-driver.sigs.k8s.io",
    "security-profiles-operator.sigs.k8s.io", "cluster-proportional-autoscaler.sigs.k8s.io",
    "cncf.io", "www.cncf.io", "landscape.cncf.io", "artifacthub.io",
    "etcd.io", "containerd.io", "cri-o.io", "prometheus.io",
    "opentelemetry.io", "openpolicyagent.org", "kubevirt.io", "thanos.io",
    "envoyproxy.io", "jaegertracing.io", "argo-project.io", "backstage.io",
    "knative.dev", "buildpacks.io", "k3s.io", "falco.org", "kyverno.io",
    "kubevela.io", "kubeflow.org", "karmada.io", "spinnaker.io",
    "docs.kubernetes.io", "blog.kubernetes.io", "get.helm.sh", "min.io",
    "grafana.com", "registry.k8s.io", "docusign.com", "vuejs.org"
]

IPS = sorted(set([
    "3.33.186.135",  "3.160.200.10",  "3.162.200.50",  "3.162.247.34",  "3.162.247.38",
    "3.162.247.45",  "3.162.247.77",  "5.9.210.65",    "5.9.248.38",    "5.9.248.39",
    "5.161.50.60",   "13.32.50.30",   "13.224.50.30",  "15.197.167.90", "15.197.167.100",
    "18.160.10.40",  "23.185.0.3",    "34.96.108.209", "34.160.100.20", "34.194.97.138",
    "35.157.26.135", "35.186.200.50", "37.16.18.81",   "40.114.177.246","40.160.22.170",
    "49.13.100.70",  "50.7.5.83",     "50.7.5.85",     "50.7.85.43",    "50.7.87.2",
    "50.7.87.3",     "50.7.87.4",     "50.7.87.5",     "51.210.100.30", "52.222.214.38",
    "52.222.214.99", "52.222.214.108","52.222.214.124", "52.250.41.2",  "54.232.119.62",
    "63.141.252.203","63.141.252.207","63.176.8.218",  "64.239.109.193","65.108.50.80",
    "65.109.34.234", "69.197.138.87", "69.197.146.178","69.197.146.183","74.91.29.207",
    "75.2.60.5",     "76.76.21.21",   "76.76.21.112",  "83.136.211.95", "85.10.207.48",
    "85.10.207.51",  "85.158.145.74", "88.99.249.74",  "91.99.175.105", "94.130.13.19",
    "94.130.33.41",  "94.130.50.12",  "94.130.70.160", "94.130.200.90", "95.216.69.37",
    "104.16.80.15",  "104.17.96.15",  "104.18.25.10",  "104.18.25.196", "104.18.32.45",
    "104.21.1.100",  "104.21.33.34",  "104.21.40.50",  "104.21.60.220", "104.21.63.202",
    "104.22.10.20",  "104.198.14.52", "136.243.128.223","138.201.54.122","138.201.100.100",
    "142.54.178.211","142.54.178.215","142.54.189.111", "144.76.1.88",  "145.239.100.40",
    "148.251.65.39", "148.251.100.110","149.154.167.99","162.158.100.50","168.119.202.236",
    "170.205.28.40", "172.64.32.100", "172.66.40.100", "172.67.70.100", "172.67.80.200",
    "172.67.150.14", "172.67.158.128","172.67.201.240","173.208.128.143","178.22.122.101",
    "178.63.240.111","184.171.110.10","185.53.177.50", "185.134.23.172","185.199.108.153",
    "185.199.109.153","185.199.110.153","185.199.111.153","188.40.147.23","188.40.181.55",
    "188.40.254.151","188.114.96.3",  "188.114.96.6",  "188.114.96.10", "188.114.96.200",
    "188.114.97.3",  "188.114.97.6",  "188.114.97.20", "188.114.98.0",  "188.114.98.100",
    "188.114.99.0",  "188.114.99.150","198.202.211.1", "198.252.206.1", "204.12.192.223",
    "204.12.196.34", "204.12.196.39", "204.12.223.183","204.79.197.220","212.83.100.120",
    "213.180.193.56","216.150.1.193", "216.198.79.3",  "216.239.38.120",
]))

# ─── PROFILES ─────────────────────────────────────────────────────────────────

PERF_PROFILES = {
    "1": {"name": "Low-End Mobile / Termux", "threads": 20,   "timeout": 5},
    "2": {"name": "Mid-Range Mobile",        "threads": 40,   "timeout": 4},
    "3": {"name": "Desktop / PC",            "threads": 80,   "timeout": 3},
    "4": {"name": "High-End PC / Server",    "threads": 150,  "timeout": 2},
    "5": {"name": "Custom",                  "threads": None, "timeout": None},
}

DNS_PROFILES = {
    "1": {"name": "Direct (No Bypass)", "servers": None},
    "2": {"name": "Shecan DNS Bypass",  "servers": ["178.22.122.101", "185.51.200.2"]},
}

# ─── DEPENDENCIES & OS CHECK ──────────────────────────────────────────────────

def check_curl():
    try:
        out = subprocess.run(["curl", "-V"], capture_output=True, text=True, timeout=3)
        if out.returncode != 0:
            return False, "cURL is returning an error."
        return True, ""
    except Exception:
        return False, "cURL is not installed or not in PATH."

def has_dns_support():
    try:
        out = subprocess.run(["curl", "--dns-servers", "8.8.8.8", "http://127.0.0.1"], capture_output=True, text=True, timeout=2)
        if "doesn't support this" in out.stderr or "unknown option" in out.stderr:
            return False
    except Exception:
        pass
    return True

def get_output_dir():
    if "com.termux" in os.environ.get("PREFIX", ""):
        termux_dl = Path.home() / "storage" / "downloads"
        if termux_dl.exists() and termux_dl.is_dir():
            return termux_dl
        return Path.home()
    dl = Path.home() / "Downloads"
    if dl.exists() and dl.is_dir():
        return dl
    return Path.cwd()

# ─── TERMINAL HELPERS ─────────────────────────────────────────────────────────

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def tw():
    try:
        return min(os.get_terminal_size().columns, 74)
    except Exception:
        return 70

def hline():
    return f"{CY}{'─' * tw()}{R}"

def box_line(text, color=WH):
    inner = tw() - 4
    return f"{CY}│{R} {color}{text[:inner]:<{inner}}{R} {CY}│{R}"

def prompt(text, default=None):
    suffix = f" {DIM}[{default}]{R}" if default is not None else ""
    try:
        val = input(f"  {YL}›{R} {WH}{text}{R}{suffix}  ").strip()
        return val if val else default
    except KeyboardInterrupt:
        print(f"\n\n  {RD}✗  Operation cancelled.{R}\n")
        sys.exit(0)

def section(title):
    print(f"\n  {B}{CY}── {title}{R}")

def print_header():
    clear()
    w     = tw()
    title = f"  🍃  {BRAND}  v{VERSION}  🍃  "
    pad   = max(0, w - 4 - len(title))
    lp    = pad // 2
    rp    = pad - lp
    print(f"\n{CY}╔{'═' * (w - 2)}╗{R}")
    print(f"{CY}║{' ' * (w - 2)}║{R}")
    print(f"{CY}║{' ' * lp}{B}{WH}{title}{R}{' ' * rp}{CY}║{R}")
    print(f"{CY}║{' ' * (w - 2)}║{R}")
    print(box_line(f"Paste Results  →  {PASTE_URL}", YL))
    print(box_line(f"Channel        →  {CHANNEL}",   BL))
    print(f"{CY}║{' ' * (w - 2)}║{R}")
    print(f"{CY}╚{'═' * (w - 2)}╝{R}\n")

def draw_progress(done, total, found):
    bar_w  = 30
    filled = done * bar_w // total
    pct    = done * 100 // total
    bar    = f"{CY}{'█' * filled}{'░' * (bar_w - filled)}{R}"
    sys.stdout.write(f"\r{' ' * (tw()-1)}\r  {bar}  {B}{pct:>3}%{R}  {GR}✔ {found}{R}   ")
    sys.stdout.flush()

def erase_line():
    sys.stdout.write(f"\r{' ' * (tw()-1)}\r")
    sys.stdout.flush()

# ─── VLESS HELPERS ────────────────────────────────────────────────────────────

def parse_vless(url):
    if not url.startswith("vless://"):
        return None
    try:
        rest        = url[8:]
        uuid, addr  = rest.split("@", 1)
        ip_port, qs = addr.split("?", 1) if "?" in addr else (addr, "")
        qs          = qs.split("#", 1)[0]
        params      = parse_qs(qs) if qs else {}
        return {
            "uuid":     uuid,
            "port":     ip_port.rsplit(":", 1)[1] if ":" in ip_port else "443",
            "host":     params.get("host",     [""])[0],
            "path":     params.get("path",     [""])[0],
            "alpn":     params.get("alpn",     [""])[0],
            "security": params.get("security", ["tls"])[0],
            "type":     params.get("type",     ["xhttp"])[0],
        }
    except Exception:
        return None

def build_vless(ip, sni, p, ms, tag):
    remark = f"NL_{tag}_{ms:.0f}ms_{sni.split('.')[0]}"
    v_host = p.get("host") or sni
    v_path = p.get("path") or "/"
    return (
        f"vless://{p['uuid']}@{ip}:{p['port']}?"
        f"allowInsecure=1&alpn={quote(p['alpn'], safe='')}&encryption=none"
        f"&host={quote(v_host, safe='')}&mode=auto"
        f"&path={quote(v_path, safe='')}&security={p['security']}"
        f"&sni={sni}&type={p['type']}#{remark}"
    )

# ─── PROBE WORKERS ────────────────────────────────────────────────────────────

def _flags():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0

def probe_vless(ip, sni, base, timeout, dns_servers):
    host = base.get("host") or sni
    path = unquote(base.get("path") or "/")
    if not path.startswith("/"):
        path = "/" + path

    cmd = [
        "curl", "-s", "-o", os.devnull,
        "-w", "%{http_code}:%{time_appconnect}:%{time_total}",
        "--max-time", str(timeout),
        "--connect-timeout", str(timeout),
        f"https://{sni}{path}",
        "--resolve", f"{sni}:443:{ip}",
        "-H", f"Host: {host}",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    ]
    if dns_servers:
        cmd += ["--dns-servers", ",".join(dns_servers)]

    try:
        out = subprocess.run(
            cmd, capture_output=True, text=True, creationflags=_flags(), timeout=timeout + 2
        ).stdout.strip()

        if not out or ":" not in out:
            return None

        parts = out.split(":")
        if len(parts) < 3 or not parts[1] or not parts[2]:
            return None

        code     = parts[0]
        tls_ms   = float(parts[1]) * 1000
        total_ms = float(parts[2]) * 1000

        if tls_ms <= 0 or code in BAD_CODES:
            return None

        return ip, sni, total_ms, code
    except Exception:
        return None

def probe_basic(ip, sni, timeout, dns_servers):
    cmd = [
        "curl", "-s", "-o", os.devnull,
        "-w", "%{http_code}",
        "--max-time", str(timeout),
        "--connect-timeout", str(timeout),
        f"https://{sni}",
        "--resolve", f"{sni}:443:{ip}",
        "-H", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    ]
    if dns_servers:
        cmd += ["--dns-servers", ",".join(dns_servers)]

    try:
        res = subprocess.run(
            cmd, capture_output=True, text=True, creationflags=_flags(), timeout=timeout + 2
        )
        code = res.stdout.strip()
        if code and code not in BAD_CODES:
            return ip, sni, code
    except Exception:
        pass
    return None

# ─── SCAN ENGINE ──────────────────────────────────────────────────────────────

def run_scan(mode, threads, timeout, dns_servers, base_params=None):
    tasks       = [(ip, sni) for ip in IPS for sni in DOMAINS]
    total       = len(tasks)
    done        = 0
    results     = []
    found_ips   = Counter()
    found_snis  = Counter()
    dns_tag     = "SH" if dns_servers else "DIR"
    interrupted = False

    ex = ThreadPoolExecutor(max_workers=threads)

    if mode == "vless":
        futures = [ex.submit(probe_vless, ip, sni, base_params, timeout, dns_servers) for ip, sni in tasks]
    else:
        futures = [ex.submit(probe_basic, ip, sni, timeout, dns_servers) for ip, sni in tasks]

    try:
        for fut in as_completed(futures):
            done += 1
            try:
                res = fut.result()
            except Exception:
                res = None

            draw_progress(done, total, len(results))

            if res:
                if mode == "vless":
                    ip, sni, ms, code = res
                    cfg = build_vless(ip, sni, base_params, ms, dns_tag)
                    results.append({"ip": ip, "sni": sni, "ms": ms, "code": code, "cfg": cfg})
                    col = GR if ms < 800 else YL
                    erase_line()
                    print(f"  {GR}✔{R}  {B}{ip:<17}{R}  {CY}{sni:<42}{R}  {col}{ms:.0f}ms{R}  {DIM}{code}{R}")
                else:
                    ip, sni, code = res
                    results.append({"ip": ip, "sni": sni, "code": code})
                    erase_line()
                    print(f"  {GR}✔{R}  {B}{ip:<17}{R}  {CY}{sni:<42}{R}  {DIM}{code}{R}")

                found_ips[ip]   += 1
                found_snis[sni] += 1

    except KeyboardInterrupt:
        erase_line()
        print(f"  {YL}⚠  Interrupted — bypassing stuck tasks and saving results instantly...{R}")
        ex.shutdown(wait=False, cancel_futures=True)
        interrupted = True

    print()
    return results, found_ips, found_snis, interrupted

# ─── FILE WRITER ──────────────────────────────────────────────────────────────

def _write_results_file(f, results, top_ips, top_snis, mode):
    f.write(f"# {BRAND} v{VERSION}\n")
    f.write(f"# {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"# Paste results at : {PASTE_URL}\n")
    f.write(f"# Channel          : {CHANNEL}\n\n")

    f.write("=" * 52 + "\n")
    f.write("IPs — copy and paste into NetLeafy\n")
    f.write("=" * 52 + "\n")
    for ip in top_ips:
        f.write(f"{ip}\n")

    f.write("\n" + "=" * 52 + "\n")
    f.write("SNIs — copy and paste into NetLeafy\n")
    f.write("=" * 52 + "\n")
    for sni in top_snis:
        f.write(f"{sni}\n")

    if mode == "vless":
        f.write("\n" + "=" * 52 + "\n")
        f.write("VLESS Configs — sorted fastest first\n")
        f.write("=" * 52 + "\n")
        for r in sorted(results, key=lambda x: x["ms"]):
            f.write(f"\n# {r['ms']:.0f}ms  {r['ip']}  {r['sni']}\n{r['cfg']}\n")
    else:
        f.write("\n" + "=" * 52 + "\n")
        f.write("Full Pairs\n")
        f.write("=" * 52 + "\n")
        for r in results:
            f.write(f"{r['ip']}  {r['sni']}  {r['code']}\n")

def save_results(results, found_ips, found_snis, mode, out_dir):
    top_ips  = [ip  for ip,  _ in found_ips.most_common(30)]
    top_snis = [sni for sni, _ in found_snis.most_common(30)]

    ts    = time.strftime("%Y%m%d_%H%M%S")
    label = "vless" if mode == "vless" else "pairs"
    path  = out_dir / f"NetLeafy_{label}_{ts}.txt"

    try:
        with open(path, "w", encoding="utf-8") as f:
            _write_results_file(f, results, top_ips, top_snis, mode)
    except PermissionError:
        path = Path.cwd() / f"NetLeafy_{label}_{ts}.txt"
        try:
            with open(path, "w", encoding="utf-8") as f:
                _write_results_file(f, results, top_ips, top_snis, mode)
        except Exception:
            pass

    return path, top_ips, top_snis

# ─── SUMMARY PRINTER ──────────────────────────────────────────────────────────

def print_summary(results, found_ips, found_snis, mode, out_dir):
    print(hline())

    if not results:
        print(f"\n  {RD}✗  No results. Try a different DNS mode or connection profile.{R}\n")
        return

    saved_path, top_ips, top_snis = save_results(results, found_ips, found_snis, mode, out_dir)

    print(f"\n  {B}{WH}── Copy these into {PASTE_URL} ──{R}\n")

    print(f"  {B}{GR}IPs:{R}")
    for ip in top_ips:
        print(f"     {WH}{ip}{R}")

    print(f"\n  {B}{GR}SNIs:{R}")
    for sni in top_snis:
        print(f"     {WH}{sni}{R}")

    if mode == "vless":
        top5 = sorted(results, key=lambda x: x["ms"])[:5]
        if top5:
            print(f"\n  {B}{GR}VLESS Configs (top 5 fastest):{R}")
            for r in top5:
                print(f"  {DIM}{r['ms']:.0f}ms{R}  {WH}{r['cfg']}{R}")

    print(f"\n  {BL}📄 {saved_path}{R}")
    print(f"  {B}{GR}✔  {len(results)} verified result(s) saved.{R}")
    print(f"\n{hline()}\n")

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    if os.name != "nt":
        try:
            subprocess.run(["termux-wake-lock"], capture_output=True, check=False)
        except Exception:
            pass
    else:
        os.system("color")

    print_header()

    ok, msg = check_curl()
    if not ok:
        print(f"\n  {RD}✗  System Requirement Failed: {msg}{R}")
        print(f"     Please install cURL to use this scanner.\n")
        sys.exit(1)

    out_dir = get_output_dir()

    section("Scan Mode")
    print(f"  {GR}[1]{R}  IP/SNI Pair Discovery   {DIM}find working IP + SNI pairs{R}")
    print(f"  {GR}[2]{R}  VLESS Config Generator  {DIM}paste a base VLESS, get optimised configs{R}")
    scan_choice = prompt("Mode", "1")

    base_params = None
    if scan_choice == "2":
        section("VLESS Base Config")
        raw         = prompt("Paste your working VLESS link")
        base_params = parse_vless((raw or "").strip())
        if not base_params:
            print(f"\n  {RD}✗  Invalid VLESS URL — switching to pair-discovery mode.{R}")
            scan_choice = "1"
        else:
            print(f"  {GR}✔  Parsed  {DIM}host: {base_params.get('host', 'N/A')}{R}")

    section("DNS / Network Mode")
    for k, v in DNS_PROFILES.items():
        print(f"  {GR}[{k}]{R}  {v['name']}")
    if scan_choice == "2":
        print(f"  {YL}  Note: Shecan requires your IP registered at shecan.ir{R}")
    dns_choice  = prompt("DNS mode", "1")
    dns_cfg     = DNS_PROFILES.get(dns_choice, DNS_PROFILES["1"])
    dns_servers = dns_cfg["servers"]

    if dns_servers and not has_dns_support():
        print(f"\n  {YL}⚠  Warning: Your system's cURL version lacks Custom DNS support.{R}")
        print(f"     Proceeding securely without DNS bypass...{R}")
        dns_servers = None

    section("Performance Profile")
    for k, v in PERF_PROFILES.items():
        thr = str(v["threads"]) if v["threads"] else "custom"
        print(f"  {GR}[{k}]{R}  {v['name']:<28}  {DIM}{thr} threads{R}")
    prof_choice = prompt("Profile", "2")
    prof        = PERF_PROFILES.get(prof_choice, PERF_PROFILES["2"])

    if prof["threads"] is None:
        try:
            threads = int(prompt("Thread count", "40"))
            timeout = int(prompt("Timeout per request (seconds)", "4"))
        except ValueError:
            threads, timeout = 40, 4
    else:
        threads = prof["threads"]
        timeout = prof["timeout"]

    mode_label  = "VLESS Generator" if scan_choice == "2" else "IP/SNI Discovery"
    total_tests = len(IPS) * len(DOMAINS)

    print(f"\n{hline()}")
    print(f"  {B}{WH}Mode    {R}  {mode_label}")
    print(f"  {B}{WH}DNS     {R}  {dns_cfg['name']}")
    print(f"  {B}{WH}Profile {R}  {prof['name']}  —  {threads} threads  /  {timeout}s timeout")
    print(f"  {B}{WH}Tests   {R}  {len(IPS)} IPs × {len(DOMAINS)} SNIs = {total_tests:,} combinations")
    print(f"  {B}{WH}Output  {R}  {out_dir}")
    print(hline())
    print(f"\n  {MG}Starting — press Ctrl+C at any time to stop and save.{R}\n")

    time.sleep(0.5)

    mode_key = "vless" if scan_choice == "2" else "basic"
    results, found_ips, found_snis, interrupted = run_scan(
        mode_key, threads, timeout, dns_servers, base_params
    )

    print_summary(results, found_ips, found_snis, mode_key, out_dir)

    if os.name == "nt":
        input("  Press Enter to exit...")

    if interrupted:
        os._exit(0)

if __name__ == "__main__":
    main()
