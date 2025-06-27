from clight.system.importer import *


class main:
    ####################################################################################// Load
    def __init__(self):
        self.catalog = os.path.join(self.__userDir(), ".clight")
        os.makedirs(self.catalog, exist_ok=True)

        self.exit = None
        self.called = {}
        self.args = sys.argv[1:]
        self.project = self.__projectDir()
        self.frame = self.__loadEnvironment()
        self.config = os.path.join(self.project, ".system/sources/clight.json")
        self.params = self.__loadProject()

        signal.signal(signal.SIGINT, self.__shutDown)
        signal.signal(signal.SIGTERM, self.__shutDown)

        self.__annotations()
        self.__loadCommand(__file__, self, self.args)
        self.__annotations(True)
        pass

    ####################################################################################// Main
    def new(self):  # Create new project
        if os.path.exists(self.config):
            return "Project already exists!"

        config = {}
        inputs = self.__inputs()
        for item in inputs:
            if not item:
                continue
            value = ""
            if item[0] == "!":
                item = item[1:]
                value = self.__input(item, inputs["!" + item], True)
            else:
                value = self.__input(item, inputs[item])
            config[item] = value
        print()

        config["CMD"] = config["CMD"].replace("-", "_")

        os.makedirs(os.path.dirname(self.config), exist_ok=True)
        open(self.config, "w").write(json.dumps(config, indent=4))

        config["index"] = os.path.join(self.project, ".system/index.py")

        if not self.__renderTemplate("{{CMD}}.bat", config, self.catalog):
            return "Failed to register CMD!"

        index = os.path.join(self.frame, "skeleton/.system/index.py")
        config["Commands"] = self.__help(index, config, False)
        folder = os.path.join(self.frame, "skeleton")

        self.__cloneSkeleton(folder, self.project)
        self.__renderTemplate("README.md", config, self.project)

        if "License" in config and config["License"]:
            item = config["License"]
            self.__addLicense(item, config)

        if "Repository Type" in config and config["Repository Type"]:
            Rtype = config["Repository Type"]
            self.__addRepositoryType(Rtype)

        return "Project created"

    def add(self):  # Add existing project to catalog
        if not os.path.exists(self.project):
            return "Invalid project folder!"

        index = os.path.join(self.project, ".system/index.py")
        if not os.path.exists(index):
            return "Invalid index file!"

        config = f"{self.project}/.system/sources/clight.json"
        if not os.path.exists(config):
            return "Invalid config!"

        params = json.loads(cli.read(config))
        if not params:
            return "Invalid config params!"

        batfile = f"{self.catalog}/" + params["CMD"] + ".bat"
        if os.path.exists(self.config) and os.path.exists(batfile):
            return "Project already exists!"

        params["index"] = index
        params["CMD"] = params["CMD"].replace("-", "_")

        self.__renderTemplate("{{CMD}}.bat", params, self.catalog)

        return "Project added"

    def module(self, name=""):  # (name) - Create new module
        if not os.path.exists(self.config):
            return "Invalid project directory!"
        if not name:
            return "Specify module name!"

        hint = name[0].lower() + name[1:]
        file = os.path.join(self.project, f".system/modules/{hint}.py")
        if os.path.exists(file):
            return "Module already exists!"

        template = cli.read(os.path.join(self.frame, "system/sources/{{module}}.py"))
        if not template.strip():
            return "Invalid template!"

        cli.write(file, cli.template(template, {"module": name}))

        return "Module created"

    def reform(self, update=""):  # (-t) - Edit project params, (-t) to skip templates
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        oldlicense = self.params["License"]
        inputs = self.__inputs()
        for name in inputs:
            item = name.replace("!", "")
            if item in ["CMD", "Project Type"]:
                continue
            options = inputs[name]
            if item == "License":
                options = ["Remove"] + inputs[name]
            value = self.__input(item, options)
            if value:
                if value == "_" or value == "Remove":
                    value = ""
                self.params[item] = value

        print()
        open(self.config, "w").write(json.dumps(self.params, indent=4))

        index = os.path.join(self.project, ".system/index.py")
        if update != "-t":
            self.params["Commands"] = self.__help(index, self.params, False)
            self.__renderTemplate("README.md", self.params, self.project)

            newlicense = self.params["License"]
            licensefile = os.path.join(self.project, "LICENSE")
            if not newlicense and os.path.exists(licensefile):
                os.remove(licensefile)
            elif newlicense != oldlicense:
                self.__addLicense(newlicense, self.params)

            self.__addRepositoryType(self.params["Repository Type"])

            return "Params and templates updated"

        return "Params updated"

    def version(self, number=""):  # Upgrade semantic version number of the project
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        config = json.loads(cli.read(self.config))
        if "Version" not in config:
            return "Could not detect current version!"

        number = number.strip()
        if number and not SemVer.valid(number):
            return "Invalid semantic version number!"

        current = cli.value("Version", config, "0.0.0")
        if number and number == current:
            return f'Version "{number}" is the current version!'

        new = number if number else SemVer.bump(current)
        config["Version"] = new
        cli.write(self.config, json.dumps(config, indent=4))

        readme = cli.read(self.project + "/README.md").strip()
        if readme:
            readme = readme.replace(f"v{current}", f"v{new}").replace(
                f"**Version**: {current}", f"**Version**: {new}"
            )
            cli.write(self.project + "/README.md", readme)

        return f"Upgraded to version: {new}"

    def all(self):  # List existing projects
        collect = []
        for item in os.listdir(self.catalog):
            if item and item != ".placeholder":
                collect.append(item[:-4].strip())
        return "\n".join(collect)

    def install(self):  # Test the installation process locally
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        package = os.path.join(self.frame, "package")
        project = os.path.join(package, self.params["CMD"])
        rtype = self.params["Repository Type"]

        self.__clearFolder(package)
        os.makedirs(project, exist_ok=True)
        self.__cloneSkeleton(self.project, project, ["\\.github\\", "\\.gitlab-ci.yml"])
        self.__rebasePackage(package)
        self.__preparePackage(package)

        os.chdir(package)
        subprocess.run("pip install .", shell=True, check=True)
        self.__clearFolder(package)

        return "Project installed"

    def update(self):  # Update local installation test
        self.uninstall()
        time.sleep(5)
        self.install()

        return "Project updated"

    def uninstall(self):  # Test the uninstallation process locally
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        cmd = self.params["CMD"]
        subprocess.run(f"pip uninstall -y {cmd}", shell=True, check=True)

        return "Project uninstalled"

    def publish(self, test=""):  # (-t) - Publish project on PyPI, (-t) to test locally
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        package = os.path.join(self.frame, "package")
        project = os.path.join(package, self.params["CMD"])
        rtype = self.params["Repository Type"]

        self.__clearFolder(package)
        os.makedirs(project, exist_ok=True)
        self.__cloneSkeleton(self.project, project, ["\\.github\\", "\\.gitlab-ci.yml"])
        self.__rebasePackage(package)
        self.__preparePackage(package)

        os.chdir(package)
        if test == "-t":
            subprocess.run("pip install .", shell=True, check=True)
        elif rtype != "Local":
            return f"Project will be published when changes are pushed to {rtype}!"
        else:
            credentials = self.__getCredentials()
            subprocess.run("pip install setuptools wheel twine", shell=True, check=True)
            subprocess.run("python setup.py sdist bdist_wheel", shell=True, check=True)
            subprocess.run(
                f'twine upload dist/* -u "{credentials["username"]}" -p "{credentials["token"]}" --verbose',
                shell=True,
            )
            pass

        self.__clearFolder(package)

        return "Project published"

    def remove(self, item=""):  # (project) - Remove project
        if item not in self.all().splitlines():
            return "Invalid project name!"

        bat = os.path.join(self.catalog, f"{item}.bat")
        index = self.__detectIndex(item)
        config = os.path.join(os.path.dirname(index), "sources/clight.json")

        if os.path.exists(bat):
            os.remove(bat)
        if os.path.exists(config):
            os.remove(config)

        return "Project removed"

    def pypidel(self):  # Delete PyPI credentials
        pypi = os.path.join(self.frame, "system/sources/.pypi")
        if not os.path.exists(pypi):
            return "There is no saved credentials!"

        os.remove(pypi)

        return "Credentials deleted"

    def execute(self, *args):
        if len(args) < 1:
            return "Invalid project index!"

        index = args[0]
        self.project = os.path.dirname(os.path.dirname(index))

        if not os.path.exists(index):
            return "Invalid project index file!"

        config = os.path.join(os.path.dirname(index), "sources/clight.json")
        if not os.path.exists(config):
            return "Invalid project config file!"

        self.called = json.loads(open(config, "r").read())
        imports = os.path.join(self.project, ".system/imports.py")
        if not os.path.exists(imports):
            return "Invalid project imports!"

        modules = os.path.join(self.project, ".system/modules")
        if not os.path.exists(modules):
            return "Invalid project modules folder!"

        sys.path.append(os.path.dirname(modules))
        self.__importModule("imports", imports)

        module = self.__importModule("index", index)
        target = getattr(module, "index")
        instance = target(self.project, os.getcwd().replace("\\", "/"), args[2:])
        if self.called["Project Type"] == "Module":
            return "Modules should be imported into the project!"

        self.__loadCommand(index, instance, args[1:])
        pass

    def deploy(self, username="", token=""):
        if not username or not token:
            return "Invalid credentials!"
        if not os.path.exists(self.config):
            return "Invalid project directory!"

        package = os.path.join(self.frame, "package")
        project = os.path.join(package, self.params["CMD"])
        rtype = self.params["Repository Type"]

        self.__clearFolder(package)
        os.makedirs(project, exist_ok=True)
        self.__cloneSkeleton(self.project, project, ["\\.github\\", "\\.gitlab-ci.yml"])
        self.__rebasePackage(package)
        self.__preparePackage(package)

        os.chdir(package)
        subprocess.run("pip install setuptools wheel twine", shell=True, check=True)
        subprocess.run("python setup.py sdist bdist_wheel", shell=True, check=True)
        subprocess.run(
            f'twine upload dist/* -u "{username}" -p "{token}" --verbose',
            shell=True,
        )

        self.__clearFolder(package)

        return "Project published"

    ####################################################################################// Helpers
    def __userDir(self):
        if platform.system() == "Windows":
            return os.getenv("USERPROFILE")

        return os.getenv("HOME")

    def __getCredentials(self):
        pypi = os.path.join(self.frame, "system/sources/.pypi")
        if os.path.exists(pypi):
            encrypted = open(pypi, "r", encoding="utf-8").read()
            password = self.__input("Password Key", [], True)
            content = cli.decrypt(encrypted, password)
            return json.loads(content)

        secrets = {
            "username": self.__input("PYPI_USERNAME", [], True),
            "token": self.__input("PYPI_API_TOKEN", [], True),
        }

        save = self.__input("Do you want to save credentials", ["No", "Yes"], True)
        if save == "Yes":
            password = self.__input("Password Key", [], True)
            encrypted = cli.encrypt(json.dumps(secrets), password)
            open(pypi, "w", encoding="utf-8").write(encrypted)

        return secrets

    def __addRepositoryType(self, rtype=""):
        github = os.path.join(self.project, ".github")
        if os.path.exists(github):
            self.__clearFolder(github, True)

        gitlab = os.path.join(self.project, ".gitlab-ci.yml")
        if os.path.exists(gitlab):
            os.remove(gitlab)

        if rtype == "Local":
            return True
        elif rtype == "GitHub":
            github_src = os.path.join(self.frame, "system/sources/.github")
            os.makedirs(github, exist_ok=True)
            self.__cloneSkeleton(github_src, github)
        elif rtype == "GitLab":
            gitlab_scr = os.path.join(self.frame, "system/sources/.gitlab-ci.yml")
            shutil.copy(gitlab_scr, gitlab)

        return True

    def __addLicense(self, name="", params={}):
        if not name:
            return False

        file = os.path.join(self.frame, "licenses", name)
        if not os.path.exists(file):
            return False

        params["year"] = datetime.datetime.now().strftime("%Y")
        content = open(file, "r", encoding="utf-8").read()
        new_content = self.__replaceItems(content, params)
        new_file = os.path.join(self.project, "LICENSE")

        open(new_file, "w", encoding="utf-8").write(new_content)

        return True

    def __preparePackage(self, package=""):
        project = os.path.join(package, self.params["CMD"])
        if not os.path.exists(project):
            return False

        self.__renderTemplate("__init__.py", self.params, project)
        self.__renderTemplate("main.py", self.params, project)

        self.params["install"] = self.__collectModules(project)
        self.params["files"] = self.__collectFiles(project)
        self.params["readme"] = self.__detectReadme(package)
        self.params["license"] = self.__detectLicense(package)
        self.params["system"] = self.__detectSystem(project)

        self.__renderTemplate("setup.py", self.params, package)

        if "Project Type" in self.params and self.params["Project Type"] == "Module":
            self.__renderModule(project)

        return True

    def __renderModule(self, package=""):
        donor = os.path.join(self.frame, "system/sources/init.py")
        open(f"{package}/__init__.py", "w").write(open(donor, "r").read())

        cmd = self.params["CMD"]
        origin = f"{package}/.system"
        index = f"{origin}/index.py"
        content1 = (
            open(index, "r")
            .read()
            .replace("from imports import *", f"from {cmd}.__system__.imports import *")
        )
        open(index, "w").write(content1)

        imports = f"{origin}/imports.py"
        content2 = (
            open(imports, "r")
            .read()
            .replace("from modules.", "from .modules.")
            .replace("import modules.", "import .modules.")
            .replace("#from> ", "from ")
            .replace("#import>", "import")
        )
        open(imports, "w").write(content2)

        modules = f"{origin}/modules"
        if os.path.exists(modules):
            for module in os.listdir(modules):
                module = f"{modules}/{module}"
                content3 = (
                    open(module, "r")
                    .read()
                    .replace(
                        "from imports import *",
                        f"from {cmd}.__system__.imports import *",
                    )
                )
                open(module, "w").write(content3)

        new = f"{package}/__system__"
        os.rename(origin, new)

    def __firstLine(self, content=""):
        if not content:
            return content

        lines = content.splitlines()
        for line in lines:
            if line.strip():
                return line

        return ""

    def __detectSystem(self, package=""):
        if not os.path.exists(package):
            return ""

        ostype = self.params["Operating System"].replace("/", "::")

        return f'"Operating System :: {ostype}",'

    def __detectLicense(self, package=""):
        file = os.path.join(package, "LICENSE")
        if not os.path.exists(file):
            return ""

        types = self.__licenses()
        content = open(file, "r", encoding="utf-8").read().lower().strip()
        first = self.__firstLine(content)

        result = "Undefined"
        for item in types:
            if item.lower() in first.lower():
                result = f"OSI Approved :: {item}"
                break

        return f'"License :: {result}",'

    def __detectReadme(self, package=""):
        if not os.path.exists(os.path.join(package, "README.md")):
            return ""

        collect = [
            '    long_description=open("README.md").read()',
            '    long_description_content_type="text/markdown",',
        ]

        return ",\n".join(collect).strip()

    def __collectFiles(self, project=""):
        if not os.path.exists(project):
            return ""

        collect = []
        for root, dirs, files in os.walk(project):
            for file in files:
                file = os.path.join(root, file)
                item = file.replace(project + "\\", "").replace("\\", "/")
                hint = f'            "{item}"'
                if hint in collect:
                    continue
                if (
                    "Project Type" in self.params
                    and self.params["Project Type"] == "Module"
                ):
                    hint = hint.replace(".system/", "__system__/")
                collect.append(hint)

        return ",\n".join(collect).strip()

    def __collectModules(self, project=""):
        if not os.path.exists(project):
            return ""

        imports = os.path.join(project, ".system/imports.py")
        if not os.path.exists(imports):
            cli.error("Invalid imports file")
            return ""

        content = open(imports, "r", encoding="utf-8").read()
        py = "\n".join([line for line in content.splitlines() if "!install" not in line])
        find = re.findall(r"import\s+(\S+)(?:\s+as\s+\S+)?|from\s+(\S+)\s+import", py)
        modules = [module for match in find for module in match if module]
        defaults = self.__defaultModules()

        collect = []
        for item in modules:
            item = item.split(".")[0].strip().replace(":", ".")
            if "clight" in item:
                continue
            path = os.path.join(project, ".system", item)
            if os.path.exists(path):
                continue
            if item in defaults:
                continue
            if item in ["yaml"]:
                continue
            hint = f'        "{item}"'
            if hint in collect:
                continue
            collect.append(hint)

        return ",\n".join(collect).strip()

    def __defaultModules(self):
        standard_lib_path = sysconfig.get_paths()["stdlib"]
        modules = set()
        modules.update(builtins.__dict__.keys())

        for module in pkgutil.iter_modules([standard_lib_path]):
            modules.add(module.name)

        modules.update(sys.builtin_module_names)

        return sorted(modules)

    def __rebasePackage(self, package=""):
        project = os.path.join(package, self.params["CMD"])
        if not os.path.exists(project):
            return False

        gitignore = os.path.join(project, ".gitignore")
        if os.path.exists(gitignore):
            lines = open(gitignore, "r", encoding="utf-8").read().strip().splitlines()
            newlines = [f'{self.params["CMD"]}/{line}' for line in lines]
            open(gitignore, "w", encoding="utf-8").writelines(newlines)
            shutil.move(gitignore, package)

        License = os.path.join(project, "LICENSE")
        if os.path.exists(License):
            shutil.move(License, package)

        readme = os.path.join(project, "README.md")
        if os.path.exists(readme):
            shutil.move(readme, package)

        return True

    def __clearFolder(self, folder="", itself=False):
        if not os.path.exists(folder):
            return False

        for filename in os.listdir(folder):
            if filename == ".placeholder":
                continue
            file_path = os.path.join(folder, filename)
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)

        if itself:
            shutil.rmtree(folder)

        return True

    def __detectIndex(self, cmd=""):
        if not cmd:
            cli.error("Invalid index cmd")
            return ""

        bat = os.path.join(self.catalog, f"{cmd}.bat")
        if not os.path.exists(bat):
            cli.error("Invalid catalog file")
            return ""

        content = open(bat, "r").read()
        index = re.search(r'clight execute "(.*?)" %\*', content).group(1).strip()
        if not os.path.exists(index):
            cli.error("Invalid index file")
            return ""

        return index

    def __projectDir(self):
        config = os.path.join(os.getcwd(), ".system/sources/clight.json")
        if os.path.exists(config):
            self.params = {}
            return os.getcwd()

        if len(self.args) == 0 or self.args[0] != "execute":
            self.params = {
                "Name": "CLight",
                "Version": "2.3.3",
                "CMD": "clight",
                "Author": "Irakli Gzirishvili",
                "Mail": "gziraklirex@gmail.com",
            }
            return os.getcwd()

        index = self.args[1]
        project = os.path.dirname(os.path.dirname(index))
        config = os.path.join(project, ".system/sources/clight.json")
        if ".system/index.py" not in index or not os.path.exists(config):
            cli.error("Invalid execution index")
            sys.exit()

        self.params = {}
        return project

    def __cloneSkeleton(self, folder="", destination="", skip=[]):
        if not os.path.exists(folder) or not os.path.exists(destination):
            cli.error("Failed to clone skeleton!")
            return False

        for root, dirs, files in os.walk(folder):
            for file in files:
                file = os.path.join(root, file)
                if "\\.git\\" in file:
                    continue
                if "\\vendor\\" in file:
                    continue
                if "\\__pycache__\\" in file:
                    continue
                if file[-5:] == ".TODO" or "\\desktop.ini" in file:
                    continue
                skipthis = False
                for item in skip:
                    if item in file:
                        skipthis = True
                        break
                if skipthis:
                    continue

                new = file.replace(folder, destination)
                os.makedirs(os.path.dirname(new), exist_ok=True)
                shutil.copy(file, new)

        return True

    def __importModule(self, name="", file=""):
        if not name or not os.path.exists(file):
            cli.error("Invalid module name or file")
            return None

        spec = importlib.util.spec_from_file_location(name, file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)

        return module

    def __help(self, file="", params={}, prints=True):
        if not os.path.exists(file) or not params:
            return ""

        content = open(file, "r").read().replace(".*? #", "")
        methods = re.findall(r" def (.*?)\(", content)
        hints = re.findall(r"  def .*? # (.*?)\n", content)
        cmd = params["CMD"]

        n = 0
        collect = ""
        for method in methods:
            if method[:1] == "_":
                continue
            if len(hints) < n + 1:
                continue
            desc = hints[n]
            if " - " not in desc:
                desc = "- " + desc
            if prints:
                cli.hint(method + " " + attr("reset") + desc)
            collect += f"- `{cmd} {method} {desc}\n".replace(" - ", "` - ")
            n += 1

        return collect.strip()

    def __annotations(self, close=False):
        if close:
            print("\n===============================================\n")
            return True
        print(
            "\n===============================================\n",
            f"\nProject: {self.params['Name']} v{self.params['Version']} ",
            f"\nAuthor: {self.params['Author']}",
            f"\nMail: {self.params['Mail']}",
            "\n\n-----------------------------------------------\n",
        )
        return True

    def __loadEnvironment(self):
        frame = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        if not os.path.exists(self.catalog):
            cli.error("Invalid catalog path")
            return frame

        if platform.system() == "Windows":
            import winreg as reg

            key = r"Environment"
            system = reg.OpenKey(
                reg.HKEY_CURRENT_USER, key, 0, reg.KEY_READ | reg.KEY_WRITE
            )
            current, _ = reg.QueryValueEx(system, "PATH")
            existing = current.split(";")

            if self.catalog in existing:
                return frame

            current += os.pathsep + self.catalog
            reg.SetValueEx(system, "PATH", 0, reg.REG_EXPAND_SZ, current)

            cli.info("Environment setup ...")
            cli.done("Please restart your CMD!")
            sys.exit()

        return frame

    def __loadCommand(self, index="", object=None, args=[]):
        if len(args) == 0:
            self.__help(index, self.params)
            return True

        cmd = args[0]
        if not hasattr(object, cmd) or cmd == "help":
            self.__help(index, self.params)
            return True

        args = args[1:]
        method = getattr(object, cmd)
        result = ""
        try:
            self.exit = (
                getattr(object, "__exit__") if hasattr(object, "__exit__") else None
            )
            result = method(*args)
            sys.stderr = open(os.devnull, "w")
        except TypeError as e:
            if " positional argument" in str(e):
                cli.error(f"Argument mismatch: passed {len(args)}")
            else:
                print(e)

        if "Project Type" in self.called and self.called["Project Type"] == "Module":
            cli.error("Modules should be imported into the project")
            return True
        elif result and result[-1:] == "!":
            cli.error(result[:-1])
        elif result:
            cli.done(result)

        return True

    def __renderTemplate(self, name="", params={}, location=""):
        if not name or not os.path.exists(location):
            return False

        file = os.path.join(self.frame, "system/sources", name)
        if not os.path.exists(file):
            return False

        content = open(file, "r", encoding="utf-8", errors="replace").read()
        rendered = self.__replaceItems(content, params)
        new = os.path.join(location, self.__replaceItems(name, params))

        os.makedirs(os.path.dirname(new), exist_ok=True)
        open(new, "w", encoding="utf-8").write(rendered)

        return True

    def __replaceItems(self, content="", params={}):
        if not content or not params:
            return ""
        for param in params:
            content = content.replace("{{" + param + "}}", params[param])
        return content

    def __loadProject(self):
        if self.params:
            return self.params
        if os.path.exists(self.config):
            content = open(self.config, "r").read()
            return json.loads(content)
        return {}

    def __shutDown(self, signal, frame):
        cli.done("\n\nCLI is shutting down ...")
        if self.exit is not None:
            self.exit()
        sys.exit()

    def __licenses(self):
        folder = os.path.join(self.frame, "licenses")
        if not os.path.exists(folder):
            return []

        return os.listdir(folder)

    def __option(self, hint="", options=[], must=False):
        if not must:
            options = ["Skip"] + options
        questions = [
            inquirer.List(
                "option",
                message=hint,
                choices=options,
            ),
        ]
        answers = inquirer.prompt(questions)["option"]
        if answers == "Skip":
            return ""
        return answers

    def __input(self, hint="", options=[], must=False):
        value = ""
        if len(options) == 0:
            if must:
                while not value:
                    value = input(f"{hint}: ")
            else:
                value = input(f"{hint}: ")
        else:
            value = self.__option(hint, options, must)
        return value

    def __inputs(self):
        return {
            "!Name": [],
            "!Version": [],
            "!Description": [],
            "Link": [],
            "!CMD": [],
            "!Author": [],
            "!Mail": [],
            "!Project Type": [
                "App",
                "Module",
            ],
            "!Repository Type": [
                "Local",
                "GitHub",
                "GitLab",
            ],
            "License": self.__licenses(),
            "!Operating System": [
                "OS Independent",
                "Microsoft / Windows",
                "POSIX / Linux",
                "MacOS",
            ],
        }


if __name__ == "__main__":
    app = main()
