# Common patterns for secrets and credentials
SECRET_PATTERNS = [
    (r'(?i)(api_key|apikey)\s*=\s*["\']([A-Za-z0-9_\-]{20,})["\']', "API Key"),
    (r'(?i)(password|passwd|pwd)\s*=\s*["\']([^"\']{6,})["\']', "Password"),
    (r'(?i)(secret|token)\s*=\s*["\']([A-Za-z0-9_\-]{20,})["\']', "Secret/Token"),
    (r'(?i)(aws_access_key_id)\s*=\s*["\']([A-Z0-9]{20})["\']', "AWS Access Key"),
    (r'(?i)(aws_secret_access_key)\s*=\s*["\']([A-Za-z0-9/+=]{40})["\']', "AWS Secret"),
    (r'["\']([A-Za-z0-9+/]{40,}={0,2})["\']', "Possible Base64 Secret"),
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv"}
SKIP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".zip", ".exe"}


def scan_file(filepath):
    findings = []
    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in SECRET_PATTERNS:
                if re.search(pattern, line):
                    findings.append(
                        {
                            "file": filepath,
                            "line": line_num,
                            "type": secret_type,
                            "content": line.strip(),
                        }
                    )
    except Exception:
        pass
    return findings


def scan_directory(root_dir):
    all_findings = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in SKIP_EXTENSIONS:
                continue
            filepath = os.path.join(dirpath, filename)
            findings = scan_file(filepath)
            all_findings.extend(findings)
    return all_findings


def generate_report(findings):
    if not findings:
        print("[CLEAN] No secrets detected in the codebase.")
        return
    print(f"\n[WARNING] {len(findings)} potential secret(s) found:\n")
    for f in findings:
        print(f"  File    : {f['file']}")
        print(f"  Line    : {f['line']}")
        print(f"  Type    : {f['type']}")
        print(f"  Content : {f['content']}")
        print()


if __name__ == "__main__":
    project_root = "."  # Change this to your project path
    print("Running Secret Scanner...")
    results = scan_directory(project_root)
    generate_report(results)
