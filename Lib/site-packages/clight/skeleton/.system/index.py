from imports import *


class index:
    ####################################################################################// Load
    def __init__(self, app="", cwd="", args=[]):
        self.app, self.cwd, self.args = app, cwd, args
        # ...
        pass

    def __exit__(self):
        # ...
        pass

    ####################################################################################// Main
    def demo(self, param=""):  # (param) - Test demo method with param
        if not param:
            return "Invalid param!"

        cli.hint(param)
        # cli.info(param)
        # cli.done(param)
        # cli.error(param)

        # text = cli.input("Enter Text", True)
        # option = cli.selection("Select Option", ["Option 1", "Option 2"])
        # action = cli.confirmation("Would you like to confirm this action?")
        # ...
        # Check the 'cli' class for more methods or take a look at the README of 'CLight' - https://github.com/IG-onGit/CLight

        return self.__helper()

    ####################################################################################// Helpers
    def __helper(self):
        return jobs.test()
