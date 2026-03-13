# vpn_connect.py
import requests
import base64
import tempfile
import subprocess
import sys

def main(country="Japan"):
    try:
        print("Đang tải danh sách máy chủ VPNGate...")
        response = requests.get("http://www.vpngate.net/api/iphone/", timeout=10)
        lines = response.text.strip().split("\n")
        servers = [line.split(",") for line in lines if line and "@" not in line]

        # Lọc máy chủ theo quốc gia
        matched = [s for s in servers[2:] if len(s) > 6 and country.lower() in s[5].lower()]
        if not matched:
            print(f"Không tìm thấy máy chủ cho {country}.")
            return

        # Chọn máy chủ tốt nhất theo tốc độ
        best = max(matched, key=lambda x: float(x[2].replace(',', '.')))
        config_b64 = best[-1]
        config = base64.b64decode(config_b64).decode("utf-8")

        # Lưu vào file tạm
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ovpn', delete=False) as f:
            f.write(config)
            f.write('\ndata-ciphers-fallback AES-128-CBC\n')
            config_path = f.name

        print(f"✅ Đã chọn máy chủ: {best[5]} ({best[0]}) - Tốc độ: {best[2]} KBps")
        print(f"🌐 IP trước: {get_public_ip()}")

        # Kết nối bằng OpenVPN
        print("🔌 Đang kết nối...")
        subprocess.run(["sudo", "openvpn", "--config", config_path], check=True)

    except Exception as e:
        print(f"❌ Lỗi: {e}")

def get_public_ip():
    try:
        return requests.get("https://api.ipify.org", timeout=5).text
    except:
        return "Không thể lấy IP"

if __name__ == "__main__":
    country = sys.argv[1] if len(sys.argv) > 1 else "Japan"
    main(country)   