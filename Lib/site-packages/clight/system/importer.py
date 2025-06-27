import os
import sys

__path__ = os.path.dirname(os.path.realpath(__file__))
sys.pycache_prefix = __path__ + "/__pycache__"

import re
import time
import json
import yaml
import types
import string
import random

sys.stdout = open(os.devnull, "w")
sys.stderr = open(os.devnull, "w")
import pygame

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

import signal
import shutil
import base64
import ctypes
import pyttsx3
import hashlib
import pkgutil
import builtins
import inquirer
import datetime
import platform
import sysconfig
import importlib
import subprocess
import unicodedata
from textwrap import dedent
from colored import fg, bg, attr
import speech_recognition as speech
from cryptography.fernet import Fernet
from typing import List, Tuple, Optional
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from clight.system.modules.cli import cli
from clight.system.modules.semver import SemVer
