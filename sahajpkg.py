import sys, os, urllib.request
REG = "https://raw.githubusercontent.com/sayan9168/SahajCore/main/"
def install(name):
    url = REG + name + ".sahaj"
    try:
        data = urllib.request.urlopen(url).read().decode()
        os.makedirs("packages", exist_ok=True)
        open(f"packages/{name}.sahaj", "w").write(data)
        print(f"[sahaj-pkg] Installed {name} -> packages/{name}.sahaj")
    except Exception as e:
        print(f"[sahaj-pkg] Failed: {e}")
def list_pkg():
    if os.path.exists("packages"):
        for f in os.listdir("packages"): print("  " + f)
if len(sys.argv) < 2: print("Usage: sahajpkg install <name> | list"); sys.exit()
if sys.argv[1] == 'install': install(sys.argv[2])
elif sys.argv[1] == 'list': list_pkg()
