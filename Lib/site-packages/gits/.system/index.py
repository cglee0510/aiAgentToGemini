from imports import *


class index:
    ####################################################################################// Load
    def __init__(self, app="", cwd="", args=[]):
        self.app, self.cwd, self.args = app, cwd, args

        if platform.system() != "Windows":
            cli.error("Gits is currently available only for Windows users")
            sys.exit()

        self.sources = f"{self.app}/.system/sources"
        pass

    def __exit__(self):
        # ...
        pass

    ####################################################################################// Main
    def connect(self):  # Setup new ssh connection
        key = GitSSH.newUser("gits", self.sources)
        if not key:
            return "SSH key generation failed!"

        print()
        cli.done("Add this SSH key to your service:\n\n" + attr("reset") + key)

    def clone(self, url="", connection=""):  # (ssh-url) - Clone project from GitHub / GitLab
        if not url.strip() or url[-4:] != ".git":
            return "Invalid ssh-url!"

        if cli.isFolder(f"{self.cwd}/.git"):
            return "Folder is already taken!"

        if not GitSSH.cloneProject(self.cwd, url, connection):
            return "Cloning failed!"

        return "Project clonned successfully"

    def show(self):  # Show existing connections
        GitSSH.printConnections()
        pass

    def drop(self):  # Select connection and drop it
        if not GitSSH.dropUser("gits"):
            return "Failed to drop the connection!"

        return "Connection dropped successfully"

    ####################################################################################// Helpers
