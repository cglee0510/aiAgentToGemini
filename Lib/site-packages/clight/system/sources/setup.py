from setuptools import setup, find_packages

setup(
    name="{{CMD}}",
    version="{{Version}}",
    packages=find_packages(),
    install_requires=[
        "clight",
        {{install}}
    ],
    entry_points={
        "console_scripts": [
            "{{CMD}}={{CMD}}.main:main",  # Entry point of the app
        ],
    },
    package_data={
        "{{CMD}}": [
            {{files}}
        ],
    },
    include_package_data=True,
    author="{{Author}}",
    author_email="{{Mail}}",
    description="{{Description}}",
    {{readme}}
    url="{{Link}}",
    classifiers=[
        "Programming Language :: Python :: 3",
        {{license}}
        {{system}}
    ],
)
