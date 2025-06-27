from clight.system.importer import *


class cli:
    mode = "text"
    speed = 150
    voice = 1
    dev = False

    ####################################################################################// Load
    def __init__(self):
        pass

    ####################################################################################// Main
    def hint(message="", update=False):
        end = "\n"
        if update and not cli.dev:
            end = "\r"
            message += " " * 100
        print(fg("yellow") + message + attr("reset"), end=end)

    def done(message="", update=False):
        end = "\n"
        if update and not cli.dev:
            end = "\r"
            message += " " * 100
        print(fg("green") + message + attr("reset"), end=end)

    def info(message="", update=False):
        end = "\n"
        if update and not cli.dev:
            end = "\r"
            message += " " * 100
        print(fg("cyan") + message + attr("reset"), end=end)

    def error(message="", update=False):
        end = "\n"
        if update and not cli.dev:
            end = "\r"
            message += " " * 100
        print(fg("red") + message + "!" + attr("reset"), end=end)

    def trace(message=""):
        if cli.dev:
            print("● " + message)

    def input(hint="", must=False):
        if not hint:
            hint = "Enter"

        if cli.mode == "voice":
            cli.sound("ask")
        value = input(fg("light_yellow") + hint + attr("reset") + ": ")
        while must and not value:
            value = input(fg("light_yellow") + hint + attr("reset") + ": ")

        return value

    def selection(hint="", options=[], must=False):
        if not hint:
            hint = "Select"
        if not options:
            return ""

        if not must:
            options = ["Skip"] + options

        if cli.mode == "voice":
            cli.speak(hint)
        cli.sound("ask")
        questions = [
            inquirer.List(
                "option",
                message=fg("light_yellow") + hint + attr("reset"),
                choices=options,
            ),
        ]

        answers = inquirer.prompt(questions)["option"]
        if answers == "Skip":
            return ""

        return answers

    def selections(hint="", options=[], must=False):
        if not hint:
            hint = "Select"
        if not options:
            return ""

        if cli.mode == "voice":
            cli.speak(hint)
        cli.sound("ask")
        questions = [
            inquirer.Checkbox(
                "choices",
                message=fg("light_yellow") + hint + attr("reset"),
                choices=options,
            ),
        ]

        answers = inquirer.prompt(questions)["choices"]
        if not answers and must:
            return cli.selections(hint, options, must)

        return answers

    def confirmation(hint="", must=False):
        if not hint:
            hint = "Confirm"

        if cli.mode == "voice":
            cli.speak(hint)
        cli.sound("ask")

        options = "y" if must else "y/n"
        hint = fg("light_yellow") + hint + attr("reset")
        value = input(f"{hint} ({options}): ")
        while must and (not value or value not in ["Y", "y"]):
            value = input(f"{hint} ({options}): ")

        return True if value in ["Y", "y"] else False

    def value(key="", data=None, default=""):
        if key is not None and isinstance(key, int) and 0 <= key < len(data):
            return data[key]
        elif key in data:
            return data[key]
        else:
            return default

    def sound(name=""):
        dir = os.path.dirname(os.path.dirname(__file__))
        path = os.path.join(dir, "sources", str(name) + ".wav")
        if not os.path.exists(path):
            return False

        pygame.init()
        pygame.mixer.init()

        try:
            sound = pygame.mixer.Sound(path)
            sound.play()
            pygame.time.wait(int(sound.get_length() * 1000))
        except Exception as e:
            print(e)
            sys.exit()
        finally:
            pygame.quit()

    def speak(text="", speed=None, voice=None):
        speed = cli.speed if speed == None else speed
        voice = cli.voice if voice == None else voice

        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[voice].id)
        engine.setProperty("rate", speed)
        engine.say(str(text))
        engine.runAndWait()
        return "Reading Done"

    def listen():
        rec = speech.Recognizer()
        with speech.Microphone() as source:
            rec.adjust_for_ambient_noise(source)
            cli.sound("start")
            audio = rec.listen(source)
            try:
                text = rec.recognize_google(audio)
                cli.sound("done")
                return text
            except Exception as error:
                cli.sound("error")
                if len(str(error)) == 0:
                    return False
                else:
                    time.sleep(2)
                    return False

    def read(file=""):
        if not os.path.exists(file) or not os.path.isfile(file):
            return ""

        return open(file, "r", encoding="utf-8", errors="replace").read()

    def write(file="", content=""):
        if not file:
            return False
        with open(file, "w", encoding="utf-8") as f:
            f.write(content)
        return file

    def append(file="", content="", newline=True):
        if not content.strip():
            return False

        content = "\n" + content if newline and os.path.exists(file) else content
        open(file, "a").write(content)

        return True

    def yaml(file=""):
        if not os.path.exists(file):
            return {}

        yml = {}
        with open(file, "r") as yaml_file:
            yml = yaml.safe_load(yaml_file)

        if not yml:
            return {}

        return yml

    def template(content="", replacers={}):
        if not content or not replacers:
            return ""

        for replacer in replacers:
            content = content.replace("{{" + replacer + "}}", str(replacers[replacer]))

        return content

    def chars(length=50):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    def isValue(value):
        if value:
            return True
        return False

    def isPath(path=""):
        if path and os.path.exists(path):
            return True
        return False

    def isFile(path=""):
        if path and os.path.exists(path) and os.path.isfile(path):
            return True
        return False

    def isFolder(path=""):
        if path and os.path.exists(path) and os.path.isdir(path):
            return True
        return False

    def execute(line="", message="", background=False):
        if not line:
            cli.error("Invalid CMD line")
            return False

        try:
            if background:
                subprocess.Popen(line, shell=True)
            else:
                subprocess.run(line, check=True)
            cli.done(message)
            return True
        except subprocess.CalledProcessError:
            cli.error(f"CMD Failed: {message}")
            return False

        return False

    def command(line="", wait=True, hide=False, location=".", get=False):
        if not line:
            return ""

        if location == ".":
            location = os.getcwd()

        if get:
            return subprocess.run(line, cwd=location, text=True, capture_output=True, shell=True).stdout
        elif wait and hide:
            subprocess.run(line, cwd=location, text=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif wait and not hide:
            subprocess.run(line, cwd=location, text=True, shell=True)
        elif not wait and hide:
            subprocess.Popen(line, cwd=location, text=True, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif not wait and not hide:
            subprocess.Popen(line, cwd=location, text=True, shell=True)

        return ""

    def encrypt(text="", key=""):
        try:
            salt = os.urandom(16)
            derived_key = cli.__derive_key(key, salt)
            fernet = Fernet(derived_key)
            encrypted = fernet.encrypt(text.encode())
            return base64.urlsafe_b64encode(salt + encrypted).decode("utf-8")
        except Exception as e:
            e = f": {e}" if str(e).strip() else ""
            cli.trace(f"Could not encrypt{e}!")
        return ""

    def decrypt(encrypted="", key=""):
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
            salt = encrypted_bytes[:16]
            encrypted_text = encrypted_bytes[16:]
            derived_key = cli.__derive_key(key, salt)
            fernet = Fernet(derived_key)
            return fernet.decrypt(encrypted_text).decode("utf-8")
        except Exception as e:
            e = f": {e}" if str(e).strip() else ""
            cli.trace(f"Could not decrypt{e}!")
        return ""

    def filter(text="", length=1_000):
        folder = os.path.dirname(os.path.dirname(__file__))
        file = os.path.join(folder, "sources/ansi_escape")
        if not os.path.exists(file):
            return ""

        external_pattern = open(file, "r").read()
        ansi_re = re.compile(dedent(external_pattern), re.VERBOSE | re.DOTALL)

        allowed = set(
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "0123456789"
            " .,;:!?'-_()[]{}<>/\\\"\n\t"
        )

        bidi_chars = {
            "\u202a",  # LRE, RLE, PDF, LRO, RLO
            "\u202b",
            "\u202c",
            "\u202d",
            "\u202e",
            "\u2066",  # LRI, RLI, FSI, PDI
            "\u2067",
            "\u2068",
            "\u2069",
        }

        allow_bidi = [
            "\u0040",  # @
            "\u0026",  # &
        ]

        text = text[:length]  # 0. Enforce max length
        text = ansi_re.sub("", text)  # 1. Strip ANSI/OSC
        text = unicodedata.normalize("NFC", text)  # 2. Normalize

        out = []
        for ch in text:
            cat = unicodedata.category(ch)
            if ch in ("\n", "\t"):
                out.append(ch)
            elif ch in bidi_chars:
                continue
            elif cat.startswith("C") or cat == "Cf":
                continue
            elif ch == "\r":
                continue
            elif ch not in allowed and ch not in allow_bidi:
                continue
            else:
                out.append(ch)

        return "".join(out)

    ####################################################################################// Helpers
    def __derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100_000,
            backend=default_backend(),
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))
