import os, sys, signal, socket, json, subprocess, time, shutil, ipaddress, re, tempfile, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs
from datetime import datetime

R, B, DIM = "\033[0m", "\033[1m", "\033[2m"
CY, WH, GR = "\033[96m", "\033[97m", "\033[90m"
YEL, RED, GRN = "\033[93m", "\033[91m", "\033[92m"

BRAND = "NetLeafyScanner"
VERSION = "Scanner V4"
PASTE_URL = "https://code-leafy.github.io/NetLeafy"
CHANNEL = "https://t.me/codeleafy"
RESULTS_DIR = Path.home() / ".netleafy"
BAD_CODES = {"000", "403", "404", "502", "503", "521", "522", "523", "530"}

PROFILES = {
    "1": {"name": "Low",    "threads": 20,  "timeout": 6,  "ping_count": 2},
    "2": {"name": "Mid",    "threads": 50,  "timeout": 4,  "ping_count": 3},
    "3": {"name": "High",   "threads": 100, "timeout": 3,  "ping_count": 4},
    "4": {"name": "Ultra",  "threads": 200, "timeout": 2,  "ping_count": 5},
    "5": {"name": "Custom", "threads": None, "timeout": None, "ping_count": None},
}

print_lock = threading.Lock()

def _flags():
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0

def clear():
    os.system("cls" if os.name == "nt" else "clear")

def term_w():
    try:
        return min(os.get_terminal_size().columns, 80)
    except:
        return 80

def strip_ansi(text):
    return re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', str(text))

def box(title=""):
    w = term_w() - 4
    print(f"\n{CY}╭{'─'*w}╮{R}")
    if title:
        ts = strip_ansi(title)
        pad = (w - len(ts)) // 2
        print(f"{CY}│{' '*pad}{WH}{B}{title}{' '*(w-pad-len(ts))}{CY}│{R}")
        print(f"{CY}├{'─'*w}┤{R}")

def endbox():
    w = term_w() - 4
    print(f"{CY}╰{'─'*w}╯{R}")

def line(text="", indent=2):
    w = term_w() - 4
    ts = strip_ansi(str(text))
    print(f"{CY}│{' '*indent}{text}{' '*max(w-indent-len(ts),0)}{CY}│{R}")

def item(num, name, desc=""):
    w = term_w() - 4
    d = f" {DIM}{desc}{R}" if desc else ""
    text = f"{WH}{num}.{CY} {WH}{name}{d}"
    ts = strip_ansi(text)
    print(f"{CY}│{' '*2}{text}{' '*max(w-2-len(ts),0)}{CY}│{R}")

def clrline():
    sys.stdout.write(f"\r{' ' * term_w()}\r")
    sys.stdout.flush()

def update_progress(cur, total, phase=""):
    w = term_w() - 4
    pct = cur / total if total > 0 else 0
    bw = 30
    full = int(pct * bw)
    rem = int((pct * bw - full) * 8)
    blocks = [" ", "▏", "▎", "▍", "▌", "▋", "▊", "▉", "█"]
    bar_fill = '█' * full
    bar_rem = blocks[rem] if full < bw else ""
    bar_empty = ' ' * (bw - full - 1) if full < bw else ""
    bar = f"{CY}{bar_fill}{WH}{bar_rem}{DIM}{bar_empty}{R}"
    spinners = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    spinner = f"{YEL}{spinners[int(time.perf_counter() * 15) % len(spinners)]}{R}"
    phase_str = f" {DIM}{phase}{R}" if phase else ""
    text = f"{spinner} {bar} {WH}{int(pct*100):3d}%{CY} | {WH}{cur}/{total}{phase_str}"
    ts = strip_ansi(text)
    sys.stdout.write(f"\r{CY}│  {text}{' '*max(w-2-len(ts),0)}{CY}│{R}")
    sys.stdout.flush()

def banner():
    clear()
    print(fr"""{CY}
███╗   ██╗███████╗████████╗██╗     ███████╗█████╗ ███████╗██╗   ██╗
████╗  ██║██╔════╝╚══██╔══╝██║     ██╔════╝██╔══██╗██╔════╝╚██╗ ██╔╝
██╔██╗ ██║█████╗     ██║   ██║     █████╗  ███████║█████╗   ╚████╔╝ 
██║╚██╗██║██╔══╝     ██║   ██║     ██╔══╝  ██╔══██║██╔══╝    ╚██╔╝  
██║ ╚████║███████╗   ██║   ███████╗███████╗██║  ██║██║        ██║   
╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝        ╚═╝   

{WH}{B}        {VERSION}  {CY}|{WH}  Made By CodeLeafy       {R}
""")

def prompt(text, default=None, choices=None):
    suffix = f" {DIM}[{default}]{R}" if default else ""
    if choices:
        suffix += f" {DIM}({','.join(choices)}){R}"
    try:
        while True:
            val = input(f"{CY}› {WH}{text}{suffix}: {WH}").strip()
            if val:
                if choices and val not in choices:
                    print(f"{CY}! {YEL}Invalid{R}")
                    continue
                return val
            if default:
                return default
    except KeyboardInterrupt:
        print(f"\n{CY}! {RED}Cancelled{R}")
        sys.exit(0)

def expand_ips(content):
    ips = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "/" in line:
            try:
                for ip in ipaddress.ip_network(line, strict=False).hosts():
                    ips.add(str(ip))
            except:
                pass
        elif "-" in line:
            try:
                start, end = [p.strip() for p in line.split("-")]
                if "." not in end:
                    end = ".".join(start.split(".")[:3] + [end])
                start_ip, end_ip = int(ipaddress.ip_address(start)), int(ipaddress.ip_address(end))
                for ip_int in range(start_ip, end_ip + 1):
                    ips.add(str(ipaddress.ip_address(ip_int)))
            except:
                pass
        else:
            try:
                ipaddress.ip_address(line)
                ips.add(line)
            except:
                pass
    return sorted(ips, key=lambda x: int(ipaddress.ip_address(x)))

def load_file(path, expand_ranges=True, default=""):
    try:
        p = Path(path)
        if not p.exists() and default:
            p.write_text(default, encoding="utf-8")
        if not p.exists():
            return []
        content = p.read_text(encoding="utf-8")
        return expand_ips(content) if expand_ranges else [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    except Exception:
        return []

def get_xray():
    for p in ["xray", "xray.exe", "C:\\xray\\xray.exe", "C:\\Program Files\\xray\\xray.exe", "/usr/local/bin/xray", "/usr/bin/xray"]:
        if shutil.which(p):
            return shutil.which(p)
    return "xray"

def check_dep(cmd):
    try:
        subprocess.run(cmd + ["--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3)
        return True
    except:
        return False

def tcp_ping(ip, timeout, count):
    times = []
    for _ in range(count):
        try:
            s = time.perf_counter()
            with socket.create_connection((ip, 443), timeout=timeout):
                pass
            times.append((time.perf_counter() - s) * 1000)
        except:
            continue
    return sum(times) / len(times) if times else None

def curl_probe(ip, sni, timeout):
    try:
        out = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}:%{time_total}",
             "--max-time", str(timeout), "--connect-timeout", str(timeout),
             f"https://{sni}/", "--resolve", f"{sni}:443:{ip}",
             "-H", f"Host: {sni}", "-H", "User-Agent: Mozilla/5.0"],
            capture_output=True, text=True, creationflags=_flags(), timeout=timeout + 2
        ).stdout.strip()
        if not out or ":" not in out:
            return None
        code, ms_sec = out.split(":")
        ms = float(ms_sec) * 1000
        if code not in BAD_CODES and 0 < ms <= timeout * 1000:
            return {"ip": ip, "sni": sni, "ms": round(ms, 1), "code": code}
    except:
        pass
    return None

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', 0))
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    port = s.getsockname()[1]
    s.close()
    return port

def build_xray_config_from_uri(uri, target_ip, local_port):
    try:
        if uri.startswith("vless://") or uri.startswith("trojan://"):
            parsed = urlparse(uri)
            pwd_or_uuid = parsed.username
            port = parsed.port or 443
            qs = parse_qs(parsed.query)

            def get_qs(k, def_val=""):
                v = qs.get(k, [""])[0]
                return v if v else def_val

            sni = get_qs("sni", parsed.hostname or "")
            net = get_qs("type", "tcp")
            tls = get_qs("security", "none")
            flow = get_qs("flow", "")
            alpn = get_qs("alpn", "")
            fp = get_qs("fp", "")

            outbound = {
                "protocol": "vless" if uri.startswith("vless://") else "trojan",
                "settings": {},
                "streamSettings": {"network": net, "security": tls}
            }

            if uri.startswith("vless://"):
                user = {"id": pwd_or_uuid, "encryption": "none"}
                if flow:
                    user["flow"] = flow
                outbound["settings"]["vnext"] = [{
                    "address": target_ip,
                    "port": int(port),
                    "users": [user]
                }]
            else:
                outbound["settings"]["servers"] = [{
                    "address": target_ip,
                    "port": int(port),
                    "password": pwd_or_uuid
                }]

            if tls == "tls":
                outbound["streamSettings"]["tlsSettings"] = {
                    "serverName": sni,
                    "allowInsecure": True
                }
                if fp: outbound["streamSettings"]["tlsSettings"]["fingerprint"] = fp
                if alpn: outbound["streamSettings"]["tlsSettings"]["alpn"] = alpn.split(",")
                    
            elif tls == "reality":
                outbound["streamSettings"]["realitySettings"] = {
                    "serverName": sni,
                    "publicKey": get_qs("pbk"),
                    "shortId": get_qs("sid"),
                    "spiderX": get_qs("spx", "/")
                }
                outbound["streamSettings"]["realitySettings"]["fingerprint"] = fp if fp else "chrome"
                if alpn: outbound["streamSettings"]["realitySettings"]["alpn"] = alpn.split(",")

            if net == "ws":
                outbound["streamSettings"]["wsSettings"] = {
                    "path": get_qs("path", "/"),
                    "headers": {"Host": get_qs("host", sni)}
                }
            elif net == "grpc":
                outbound["streamSettings"]["grpcSettings"] = {
                    "serviceName": get_qs("serviceName", ""),
                    "multiMode": get_qs("mode", "multi") != "gun"
                }
            elif net == "tcp":
                header_type = get_qs("headerType", "none")
                if header_type == "http":
                    outbound["streamSettings"]["tcpSettings"] = {
                        "header": {
                            "type": "http",
                            "request": {
                                "path": [get_qs("path", "/")],
                                "headers": {
                                    "Host": [get_qs("host", sni)]
                                }
                            }
                        }
                    }

            return {
                "log": {"loglevel": "warning"},
                "inbounds": [{"listen": "127.0.0.1", "port": local_port, "protocol": "socks"}],
                "outbounds": [outbound],
                "routing": {"domainStrategy": "IPIfNonMatch", "rules": []}
            }
    except Exception:
        pass
    return None

def test_xray_speed(ip, uri, timeout):
    local_port = find_free_port()
    config_dict = build_xray_config_from_uri(uri, ip, local_port)
    if not config_dict:
        return None
        
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, 'w') as f:
        json.dump(config_dict, f)
        
    flags = _flags()
    proc = subprocess.Popen([get_xray(), "run", "-c", temp_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags)
    
    time.sleep(0.5) 
    result = None
    try:
        s = time.perf_counter()
        res = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{speed_download}", "--max-time", str(timeout),
             "-x", f"socks5h://127.0.0.1:{local_port}", "https://speed.cloudflare.com/__down?bytes=100000"],
            capture_output=True, text=True, timeout=timeout + 1, creationflags=flags
        )
        if res.stdout.strip():
            try:
                speed = float(res.stdout.strip())
                if speed > 0:
                    result = {"ip": ip, "latency": round((time.perf_counter() - s) * 1000, 1), "speed": speed}
            except:
                pass
    except:
        pass
        
    try:
        proc.terminate()
        proc.wait(timeout=1)
    except:
        try:
            proc.kill()
        except:
            pass
            
    try:
        os.remove(temp_path)
    except:
        pass
    return result

def show_profile_select():
    box("Performance Profile")
    for k, v in PROFILES.items():
        line(f"{k}. {v['name']}")
    endbox()
    choice = prompt("Select", "2", list(PROFILES.keys()))
    prof = dict(PROFILES[choice])
    if prof["threads"] is None:
        prof["threads"] = int(prompt("Threads", "60"))
        prof["timeout"] = int(prompt("Timeout (sec)", "3"))
        prof["ping_count"] = int(prompt("Ping count", "4"))
    return prof

def netlify_full(profile):
    banner()
    box("Netlify Full Scan")
    ips = load_file(Path(__file__).parent / "ip.txt", default="104.16.0.0/24\n104.17.0.0/24")
    snis = load_file(Path(__file__).parent / "sni.txt", expand_ranges=False, default="speedtest.net\nnzoom.us")
    if not ips or not snis:
        line(f"{RED}! Missing ip.txt or sni.txt{R}")
        endbox()
        return
    total = len(ips) * len(snis)
    line(f"IPs: {CY}{len(ips)}{WH} | SNIs: {CY}{len(snis)}{WH} | Total: {CY}{total:,}{R}")
    line(f"Threads: {CY}{profile['threads']}{WH} | Timeout: {CY}{profile['timeout']}s{R}")
    endbox()
    if prompt("Start scan?", "y", ["y", "n"]) != "y":
        return
    box("Scanning")
    results, done = [], 0
    with ThreadPoolExecutor(max_workers=profile["threads"]) as ex:
        futures = {ex.submit(curl_probe, ip, sni, profile["timeout"]): (ip, sni) for ip in ips for sni in snis}
        try:
            for fut in as_completed(futures):
                done += 1
                res = fut.result()
                with print_lock:
                    if res:
                        results.append(res)
                        clrline()
                        sni_short = res['sni'][:18]
                        print(f"{CY}│  {GRN}✓{WH} {res['ip']:<16} {CY}|{WH} {sni_short:<18} {CY}|{WH} {res['ms']:.0f}ms{DIM} {res['code']}{R}{' '*max(term_w()-80,0)}{CY}│{R}")
                    update_progress(done, total)
        except KeyboardInterrupt:
            with print_lock:
                clrline()
                line(f"{YEL}Stopped by user{R}")
    clrline()
    line(f"{GRN}Scan Complete!{R}")
    endbox()
    if results:
        sorted_res = sorted(results, key=lambda x: x["ms"])
        box(f"Top Results ({len(results)} found)")
        for i, r in enumerate(sorted_res[:20], 1):
            line(f"{i:2}. {CY}{r['ip']:<16} {WH}| {CY}{r['sni'][:18]:<18} {WH}| {GRN}{r['ms']:.0f}ms{DIM} {r['code']}{R}")
        endbox()
        out = RESULTS_DIR / f"netlify_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            for r in sorted_res[:100]:
                f.write(f"{r['ip']} | {r['sni']} | {r['ms']:.0f}ms | {r['code']}\n")
        box("Saved")
        line(f"Saved to: {CY}{out.name}{R}")
        endbox()
    else:
        box("Results")
        line(f"{YEL}No working combinations found{R}")
        endbox()

def netlify_ip_only(profile):
    banner()
    box("IP Only Scanner")
    ips = load_file(Path(__file__).parent / "ip.txt", default="104.16.0.0/24")
    if not ips:
        line(f"{RED}! ip.txt not found or empty{R}")
        endbox()
        return
    line(f"Testing {CY}{len(ips)}{WH} IPs | Probes: {CY}{profile['ping_count']}{R}")
    endbox()
    if prompt("Start scan?", "y", ["y", "n"]) != "y":
        return
    box("Pinging")
    results, done = [], 0
    with ThreadPoolExecutor(max_workers=profile["threads"]) as ex:
        futures = {ex.submit(tcp_ping, ip, profile["timeout"], profile["ping_count"]): ip for ip in ips}
        try:
            for fut in as_completed(futures):
                done += 1
                ms = fut.result()
                ip = futures[fut]
                with print_lock:
                    if ms:
                        results.append({"ip": ip, "ms": ms})
                    update_progress(done, len(ips), f"| {GRN}{len(results)} live{R}")
        except KeyboardInterrupt:
            with print_lock:
                clrline()
                line(f"{YEL}Stopped by user{R}")
    clrline()
    line(f"{GRN}Scan Complete!{R} {WH}{len(results)}/{len(ips)} responded")
    endbox()
    if results:
        sorted_res = sorted(results, key=lambda x: x["ms"])
        box(f"Fastest IPs")
        for i, r in enumerate(sorted_res[:20], 1):
            line(f"{i:2}. {CY}{r['ip']:<16} {WH}| {GRN}{r['ms']:.0f}ms{R}")
        endbox()
        out = RESULTS_DIR / f"iponly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            for r in sorted_res:
                f.write(f"{r['ip']}\n")
        box("Saved")
        line(f"Saved {len(sorted_res)} IPs to: {CY}{out.name}{R}")
        endbox()
    else:
        box("Results")
        line(f"{YEL}No IPs responded{R}")
        endbox()

def g2leafy_test(profile):
    banner()
    box("G2ray Real-Proxy Scanner")
    xray_path = get_xray()
    if not check_dep([xray_path]):
        line(f"{RED}! xray-core not found!{R}")
        line(f"{DIM}Install from: github.com/Code-Leafy/G2rayXCodeLeafy{R}")
        endbox()
        return
    ips = load_file(Path(__file__).parent / "ip.txt", default="104.16.0.0/24")
    if not ips:
        line(f"{RED}! ip.txt not found or empty{R}")
        endbox()
        return
    line(f"Loaded {CY}{len(ips)}{WH} IPs")
    line(f"{DIM}Enter VLESS link (vless://...) or UUID@sni:port{R}")
    endbox()
    try:
        config = input(f"{CY}› {WH}Config: {WH}").strip()
    except KeyboardInterrupt:
        return
    if not config:
        return
        
    uri = config
    if not uri.startswith("vless://") and not uri.startswith("trojan://"):
        if "@" in config:
            parts = config.split("@")
            sni_port = parts[1] if len(parts) > 1 else ""
            sni = sni_port.split(":")[0] if ":" in sni_port else sni_port
            port = int(sni_port.split(":")[1]) if ":" in sni_port else 443
            uri = f"vless://{parts[0]}@{sni}:{port}?type=ws&security=tls&sni={sni}"
        else:
            print(f"{RED}! Invalid format{R}")
            return
            
    max_show = int(prompt("Show top X IPs", "10", ["5", "10", "20", "50", "100"]))
    endbox()

    box("Phase 1: Finding Live IPs")
    line(f"Testing {CY}{len(ips)}{WH} IPs for connectivity...")
    endbox()

    ping_results = []
    done = 0
    with ThreadPoolExecutor(max_workers=profile["threads"]) as ex:
        futures = {ex.submit(tcp_ping, ip, profile["timeout"], 2): ip for ip in ips}
        try:
            for fut in as_completed(futures):
                done += 1
                ms = fut.result()
                if ms:
                    ping_results.append({"ip": futures[fut], "ms": ms})
                update_progress(done, len(ips), f"| {GRN}{len(ping_results)} live{R}")
        except KeyboardInterrupt:
            pass

    clrline()
    line(f"{GRN}Ping Complete!{R} {WH}{len(ping_results)}/{len(ips)} responded")
    endbox()

    if not ping_results:
        line(f"{RED}! No live IPs found{R}")
        endbox()
        return

    box("Phase 2: Speed Test")
    line(f"Testing {CY}{len(ping_results)}{WH} live IPs for real proxy speed...")
    endbox()

    speed_results = []
    done = 0
    xray_threads = min(profile["threads"], 20)

    with ThreadPoolExecutor(max_workers=xray_threads) as ex:
        futures = {ex.submit(test_xray_speed, r["ip"], uri, profile["timeout"]): r["ip"] for r in ping_results}
        try:
            for fut in as_completed(futures):
                done += 1
                res = fut.result()
                with print_lock:
                    if res and res.get("speed"):
                        speed_results.append(res)
                    update_progress(done, len(ping_results), f"| {GRN}{len(speed_results)} working{R}")
        except KeyboardInterrupt:
            pass

    clrline()
    line(f"{GRN}Speed Test Complete!{R} {WH}{len(speed_results)}/{len(ping_results)} give speed")
    endbox()

    if speed_results:
        sorted_res = sorted(speed_results, key=lambda x: x.get("latency", 9999))
        box(f"Top {max_show} Working IPs")
        for i, r in enumerate(sorted_res[:max_show], 1):
            spd = r.get("speed", 0)
            spd_str = f"{spd/1024:.0f} KB/s" if spd < 1024*1024 else f"{spd/1024/1024:.1f} MB/s"
            line(f"{i:2}. {CY}{r['ip']:<18} {WH}| {GRN}{r['latency']:.0f}ms{R} {WH}| {CY}{spd_str}{R}")
        endbox()
        out = RESULTS_DIR / f"g2ray_working_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        with open(out, "w") as f:
            for r in sorted_res[:max_show]:
                f.write(f"{r['ip']}\n")
        box("Saved")
        line(f"Saved {len(sorted_res[:max_show])} IPs to: {CY}{out.name}{R}")
        endbox()
    else:
        box("Results")
        line(f"{YEL}No IPs gave actual speed{R}")
        line(f"{DIM}Try different config or increase timeout{R}")
        endbox()

def main():
    if os.name != "nt":
        try:
            subprocess.run(["termux-wake-lock"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        except:
            pass
    else:
        os.system("color")
    if not check_dep(["curl"]):
        print(f"{RED}! curl not found!{R}")
        sys.exit(1)
    while True:
        banner()
        box("Select Mode")
        item("1", "Netlify", "IP + SNI scan")
        item("2", "G2ray", "Real proxy speed test")
        item("0", "Exit")
        endbox()
        mode = prompt("Mode", "1", ["0", "1", "2"])
        if mode == "0":
            print(f"\n{WH}Goodbye!{R}\n")
            break
        profile = show_profile_select()
        if mode == "1":
            while True:
                banner()
                box("Netlify Options")
                item("1", "Full Scan", "Test IP × SNI combinations")
                item("2", "IP Only", "Latency test only")
                item("0", "Back")
                endbox()
                opt = prompt("Select", "1", ["0", "1", "2"])
                if opt == "0":
                    break
                elif opt == "1":
                    netlify_full(profile)
                elif opt == "2":
                    netlify_ip_only(profile)
                if opt != "0":
                    input(f"\n{CY}Press Enter to continue...{WH}")
        elif mode == "2":
            g2leafy_test(profile)
            input(f"\n{CY}Press Enter to continue...{WH}")

if __name__ == "__main__":
    signal.signal(signal.SIGINT, lambda s, f: os._exit(0))
    main()
