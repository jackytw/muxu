"""
用 Windows API (LoadLibraryEx / LoadString) 提取 zh-TW wsecedit.dll.mui
中所有字串資源，找出原則說明文字，輸出 JSON。
"""
import ctypes, json, re, sys
from ctypes import wintypes

LOAD_LIBRARY_AS_DATAFILE = 0x00000002
LOAD_LIBRARY_AS_IMAGE_RESOURCE = 0x00000020

kernel32 = ctypes.windll.kernel32
kernel32.LoadLibraryExW.argtypes = [wintypes.LPCWSTR, wintypes.HANDLE, wintypes.DWORD]
kernel32.LoadLibraryExW.restype  = wintypes.HMODULE
kernel32.FreeLibrary.argtypes    = [wintypes.HMODULE]

MUI = r"C:\Windows\System32\zh-TW\wsecedit.dll.mui"
flags = LOAD_LIBRARY_AS_DATAFILE | LOAD_LIBRARY_AS_IMAGE_RESOURCE
hmod = kernel32.LoadLibraryExW(MUI, None, flags)
if not hmod:
    print("LoadLibrary failed:", ctypes.GetLastError())
    sys.exit(1)

buf = ctypes.create_unicode_buffer(4096)
results = {}
EXPLAIN_RE = re.compile(
    r'^(此安全性設定|這個安全性設定|這項安全性設定|'
    r'此使用者權限|這個使用者權限|此原則設定|這個原則設定|'
    r'決定哪些使用者|每個唯一使用者的登入資訊|'
    r'此原則支援|此安全性選項|此設定決定)'
)

prev_str = ""
for i in range(1, 32768):
    n = kernel32.LoadStringW(hmod, i, buf, 4096)
    if n <= 0:
        continue
    s = buf.value.strip()
    if not s:
        continue
    if EXPLAIN_RE.match(s) and len(s) > 60:
        # 嘗試用前一個字串當原則名稱
        name = re.sub(r'^[^一-鿿（(a-zA-Z]+', '', prev_str).strip()
        name = re.sub(r'\s+', ' ', name)[:60]
        if len(name) >= 2:
            results[name] = s[:600]
        else:
            results[f"(ID={i})"] = s[:600]
    prev_str = s

kernel32.FreeLibrary(hmod)

with open(r"D:\devs\muxu\policy_explains.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"提取到 {len(results)} 條說明", file=sys.stderr)
for k, v in sorted(results.items()):
    print(f"【{k}】 {v[:100]}")
