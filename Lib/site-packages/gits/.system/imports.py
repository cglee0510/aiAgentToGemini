from clight.system.importer import cli  # DON'T REMOVE THIS LINE

import os
import re
import sys
import json
import shutil
import platform
import subprocess
from colored import fg, bg, attr
from modules.gitssh import GitSSH
