from pathlib import Path
from shutil import copytree, rmtree, copyfileobj
from subprocess import check_output, Popen, PIPE, STDOUT, CalledProcessError
import os
import gzip
import mimetypes

Import("env")

mimeLookup = {
    "html": "text/html",
    "js": "application/javascript",
    "json": "application/json",
    "css": "text/css",
    "png": "image/png",
    "jpg": "image/jpeg",
    "ico": "image/x-icon",
    "svg": "image/svg+xml"
}

def gzipFile(file):
    with open(file, 'rb') as f_in:
        with gzip.open(file + '.gz', 'wb') as f_out:
            copyfileobj(f_in, f_out)
    os.remove(file)

def flagExists(flag):
    buildFlags = env.ParseFlags(env["BUILD_FLAGS"])
    for define in buildFlags.get("CPPDEFINES"):
        if (define == flag or (isinstance(define, list) and define[0] == flag)):
            return True

def buildProgMem():
    progmem = open('../lib/framework/WWWData.h', 'w')
    progmem.write('#include <Arduino.h>\n')

    progmemCounter = 0

    assetMap = {}

    # Iterate over all files in the data/www directory
    for path in Path("build").rglob("*.*"):
        asset_path = path.relative_to("build").as_posix()
        print("Converting " + str(asset_path))

        asset_var = 'ESP_REACT_DATA_' + str(progmemCounter)
        asset_mime = mimeLookup[asset_path.split('.')[-1]]

        progmem.write('// ' + str(asset_path) + '\n')
        progmem.write('const uint8_t ' + asset_var + '[] PROGMEM = {\n  ')
        progmemCounter += 1
        
        # Open path as binary file and read into byte array
        size = 0
        with open(path, "rb") as f:
            zipBuffer = gzip.compress(f.read()) 
            for byte in zipBuffer:
                if not (size % 16):
                    progmem.write('\n  ')
                
                progmem.write(f"0x{byte:02X}" + ',')
                size += 1

        progmem.write('\n};\n\n')
        assetMap[asset_path] = { "name": asset_var, "mime": asset_mime, "size": size }
    
    progmem.write('typedef std::function<void(const String& uri, const String& contentType, const uint8_t * content, size_t len)> RouteRegistrationHandler;\n\n')
    progmem.write('class WWWData {\n')
    progmem.write('  public:\n')
    progmem.write('    static void registerRoutes(RouteRegistrationHandler handler) {\n')

    for asset_path, asset in assetMap.items():
        progmem.write('      handler("' + str(asset_path) + '", "' + asset['mime'] + '", ' + asset['name'] + ', ' + str(asset['size']) + ');\n')

    progmem.write('    }\n')
    progmem.write('};\n')

    

def buildWeb():
    os.chdir("interface")
    print("Building interface with npm")
    try:
        env.Execute("npm install")
        env.Execute("npm run build")
        buildPath = Path("build")
        wwwPath = Path("../data/www")        
        if not flagExists("PROGMEM_WWW"):
            if wwwPath.exists() and wwwPath.is_dir():
                rmtree(wwwPath)
            print("Copying and compress interface to data directory")
            copytree(buildPath, wwwPath)
            for currentpath, folders, files in os.walk(wwwPath):
                for file in files:
                    gzipFile(os.path.join(currentpath, file))
        else:
            print("Converting assets to PROGMEM")
            buildProgMem()

    finally:
        os.chdir("..")
        if not flagExists("PROGMEM_WWW"):
            print("Build LittleFS file system image and upload to ESP32")
            env.Execute("pio run --target uploadfs")
    
if ("upload" in BUILD_TARGETS):
    print(BUILD_TARGETS)
    buildWeb()
else:
    print("Skipping build interface step for target(s): " + ", ".join(BUILD_TARGETS))
