NMAP_ALL = ("ping", "quick", "standard", "version", "custom_ports")


def to_command(profile: str, target: str, ports: str | None) -> str:
    p = (profile or "ping").lower()
    if p == "ping":
        return f"nmap -sn {target}"
    if p == "quick":
        return f"nmap -F -T4 {target}"
    if p == "standard":
        return f"nmap -T4 {target}"
    if p == "version":
        return f"nmap -sV -T4 --top-ports 30 {target}"
    if p == "custom_ports":
        pflag = f" -p{ports}" if ports else ""
        return f"nmap -T4{pflag} {target}"
    return f"nmap -sn {target}"
