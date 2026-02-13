import sys
import xml.etree.ElementTree as ET


CRITICAL_AREAS = {
    "accounts": {"prefixes": ("accounts",), "threshold": 95.0},
    "orders": {"prefixes": ("orders",), "threshold": 95.0},
    "products/menu": {"prefixes": ("products", "menu"), "threshold": 95.0},
}


def calculate_area_coverage(root, prefixes):
    total_lines = 0
    total_hits = 0
    for package in root.findall(".//package"):
        name = package.get("name")
        if not name or not any(name.startswith(prefix) for prefix in prefixes):
            continue
        for cls in package.findall(".//class"):
            for line in cls.findall(".//line"):
                total_lines += 1
                if line.get("hits") and int(line.get("hits")) > 0:
                    total_hits += 1
    return total_lines, total_hits


def main():
    try:
        tree = ET.parse("coverage.xml")
    except FileNotFoundError:
        print("coverage.xml not found. Run pytest with --cov-report=xml")
        return 2

    root = tree.getroot()
    line_rate = root.get("line-rate")
    global_pct = float(line_rate) * 100.0 if line_rate is not None else 0.0
    print(f"Global coverage (xml): {global_pct:.2f}%")
    print("Critical area coverage gates:")

    failed = False
    for area_name, config in CRITICAL_AREAS.items():
        total_lines, total_hits = calculate_area_coverage(root, config["prefixes"])
        threshold = config["threshold"]
        if total_lines == 0:
            print(f"- {area_name}: no executable lines found (threshold {threshold:.2f}%)")
            failed = True
            continue
        pct = (total_hits / total_lines) * 100.0
        status = "PASS" if pct >= threshold else "FAIL"
        print(f"- {area_name}: {pct:.2f}% / {threshold:.2f}% [{status}]")
        if pct < threshold:
            failed = True

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
