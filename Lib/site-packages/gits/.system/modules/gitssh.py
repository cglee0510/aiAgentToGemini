from imports import *


class GitSSH:
    ####################################################################################// Load
    def __init__(self, cliname="", sources=""):
        self.config = self.__setupDir()
        self.cliname = cliname
        self.sources = sources
        self.storage = self.__storage()
        self.catalog = self.__catalog()
        self.ssh_key = ""
        self.ssh_rsa = ""
        pass

    ####################################################################################// Main
    def newUser(cliname="", sources=""):
        if not cliname or not os.path.exists(sources):
            return False

        obj = GitSSH(cliname, sources)
        obj.__newUser()

        return obj.ssh_rsa

    def dropUser(cliname=""):
        if not cliname:
            return False

        obj = GitSSH(cliname, "")
        user = obj.__selectUser()

        return obj.__dropUser(user)

    def cloneProject(current="", link="", connection=""):
        if not os.path.exists(current) or not link:
            return False

        obj = GitSSH("", "")

        return obj.__cloneProject(current, link, connection)

    def printConnections():
        obj = GitSSH("", "")

        exists = False
        for item in os.listdir(obj.storage):
            if not item or item in ["__pycache__", "gits.json"]:
                continue
            mail = obj.catalog[item]["mail"] if item in obj.catalog else "..."
            cli.hint(f"{item}: " + attr("reset") + mail)
            exists = True

        if not exists:
            cli.error("No connections")
        pass

    ####################################################################################// Helpers
    def __setupDir(self):
        username = os.environ.get("USERNAME")
        folder = f"C:/Users/{username}/.ssh"

        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

        return f"{folder}/config"

    def __newUser(self):
        sshdir = os.path.dirname(self.config)
        if not os.path.exists(sshdir):
            cli.error("Invalid ssh dir")
            return False

        info = self.__form(True)
        hint = info["service"] + "-" + info["user"]
        key_file = os.path.join(self.storage, hint)
        if os.path.exists(key_file):
            cli.error("User already exists")
            return False

        content = ""
        if os.path.exists(self.config):
            content = cli.read(self.config).strip()

        template_file = os.path.join(self.sources, "sshconfig")
        if not os.path.exists(template_file):
            cli.error("Invalid template")
            return False

        ssh = self.__sshKeys(key_file)
        if not ssh:
            cli.error("Invalid ssh keys")
            return False

        self.ssh_key = ssh["key"]
        self.ssh_rsa = ssh["rsa"]

        data = info
        data["domain"] = info["service"].lower()
        template = cli.template(cli.read(template_file), info)
        merged = f"{content}\n\n{template}"

        cli.write(self.config, merged.strip())
        self.__addToCatalog(hint, info)

        return True

    def __dropUser(self, user=""):
        if not self.catalog:
            cli.error("No connections detected")
            return False

        items = os.listdir(self.storage)
        if user not in items or user in ["pycache", "gits.json"]:
            cli.error("User not found")
            return False

        if not os.path.exists(self.config):
            cli.error("Config not found")
            return False

        # Remove from config
        key_file = os.path.join(self.storage, user)
        content = cli.read(self.config)
        pattern = rf"# {self.cliname}-start: {user}(.*?)# {self.cliname}-end: {user}"
        matches = re.findall(pattern, content, re.DOTALL)

        if not matches:
            # Remove from storage
            os.remove(key_file)
            self.__removeFromCatalog(user)
            return True
        for match in matches:
            content = content.replace(
                f"\n\n# {self.cliname}-start: {user}{match}# {self.cliname}-end: {user}",
                "",
            )
            content = content.replace(
                f"\n# {self.cliname}-start: {user}{match}# {self.cliname}-end: {user}",
                "",
            )
            content = content.replace(
                f"# {self.cliname}-start: {user}{match}# {self.cliname}-end: {user}",
                "",
            )

        if not cli.write(self.config, content.strip()):
            cli.error("Failed: config")
            return False

        # Remove from storage
        os.remove(key_file)
        self.__removeFromCatalog(user)

        return True

    def __sshKeys(self, key_file=""):
        passphrase = input("Passphrase: ")
        print()

        try:
            command = f'ssh-keygen -o -t rsa -b 4096 -f "{key_file}" -N "{passphrase}" -C "{self.cliname}"'
            subprocess.run(command, shell=True, check=True)

            pub = f"{key_file}.pub"
            if not os.path.exists(key_file) or not os.path.exists(pub):
                return False

            rsa = open(pub, "r").read()
            os.remove(pub)

            return {
                "key": open(key_file, "r").read(),
                "rsa": rsa,
            }
        except subprocess.CalledProcessError as e:
            print(f"ssh-keygen error: {e}")

        return False

    def __cloneProject(self, current="", link="", connection=""):
        if not self.catalog:
            cli.error("No connections detected")
            return False

        hint = connection.strip()
        if not hint:
            hint = self.__selectUser()
        if hint not in self.catalog:
            cli.error("Invalid connection")
            return False

        user = self.catalog[hint]["user"]
        mail = self.catalog[hint]["mail"]

        link = link.replace(":", f"-{user}:")
        name = link.split("/").pop().split(".")[0].strip()
        self.__execute(f"git clone {link}", "git clone")

        source_folder = os.path.join(current, name)
        if not os.path.exists(source_folder):
            cli.error("Project not found")
            return False

        for item_name in os.listdir(source_folder):
            source_item = os.path.join(source_folder, item_name)
            destination_item = os.path.join(current, item_name)
            shutil.move(source_item, destination_item)
        os.rmdir(source_folder)

        current = current.replace("\\", "/")
        self.__execute(
            f'git config --global --add safe.directory "{current}"', "git config safe"
        )
        self.__execute(f'git config user.name "{user}"', "git config user")
        self.__execute(f'git config user.email "{mail}"', "git config mail")

        return True

    def __execute(self, line="", message="", background=False):
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

    def __storage(self):
        osuser = os.environ.get("USERNAME")
        if not osuser.strip():
            cli.error("Could not read OS username")
            sys.exit()

        folder = f"C:/Users/{osuser}/.gits"
        os.makedirs(folder, exist_ok=True)

        return folder

    def __catalog(self):
        file = f"{self.storage}/gits.json"
        if not os.path.exists(file):
            cli.write(file, "{}")
            return {}

        content = cli.read(file)
        if not content.strip():
            return {}

        return json.loads(content)

    def __addToCatalog(self, name="", info={}):
        if not name or not info:
            cli.error("Invalid catalog name or info")
            return False

        self.catalog[name] = info
        cli.write(f"{self.storage}/gits.json", json.dumps(self.catalog))

        return True

    def __removeFromCatalog(self, name=""):
        if not name:
            cli.error("Invalid catalog name")
            return False

        if name in self.catalog:
            del self.catalog[name]
            cli.write(f"{self.storage}/gits.json", json.dumps(self.catalog))

        return True

    def __selectUser(self):
        items = os.listdir(self.storage)
        if "gits.json" in items:
            items.remove("gits.json")

        return cli.selection("Select connection", items, True)

    def __form(self, must=False):
        return {
            "service": cli.selection("Select service", ["GitHub", "GitLab"], must),
            "user": cli.input("User name", must),
            "mail": cli.input("User mail", must),
            "cliname": self.cliname,
            "storage": self.storage.replace("\\", "/"),
        }
