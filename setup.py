import os
import re
import subprocess
import glob
import setuptools
from distutils.command.build_py import build_py as build_py_orig
from packaging.version import Version

# This ensures that the generated package can be found by setuptools before the build has happened.
subprocess.run(["mkdir", "-p", "cartaproto/proto"])
subprocess.run(["touch", "cartaproto/proto/__init__.py"])

class BuildProto(setuptools.Command):
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        proto_files = glob.glob('carta-protobuf/*/*.proto')
        proto_dirs = set(os.path.dirname(f) for f in proto_files)
        includes = [f"-I{d}" for d in proto_dirs]
        outputs = ['--python_out=cartaproto/proto/']

        result = subprocess.run(['protoc', '--version'], capture_output=True, text=True)
        protoc_version = Version(re.search('libprotoc (.*)', result.stdout.strip()).group(1))
        if protoc_version >= Version("3.20.0"):
            # This is necessary to generate stubs since protobuf v3.20.0
            outputs.append('--pyi_out=cartaproto/proto/')

        subprocess.run(['protoc', *includes, *outputs, *proto_files])
        
        with open('cartaproto/proto/__init__.py', 'w') as initfile:
            all_submodules = []

            for pb2_file in glob.glob('cartaproto/proto/*_pb2.py'):
                # There seriously isn't a better way to fix this relative import as of time of writing
                # See https://github.com/protocolbuffers/protobuf/issues/1491
                with open(pb2_file) as f:
                    data = f.read()
                data = re.sub("^(import .*_pb2)", r"from . \1", data, flags=re.MULTILINE)
                with open(pb2_file, 'w') as f:
                    f.write(data)

                # We also automatically import all the submodules to allow discovery    
                submodule = os.path.splitext(os.path.basename(pb2_file))[0]
                initfile.write(f"from . import {submodule}\n")

                all_submodules.append(submodule)

            # This prevents linting tools from complaining about unused imports
            initfile.write(f"__all__ = {repr(all_submodules)}\n")
                
            # Automatically parse the version from the docs
            with open('carta-protobuf/docs/src/changelog.rst') as f:
                data = f.read()
            
            icd_version = re.findall(r'   \* - ``(\d+)\.\d+\.\d+``', data)[0]
            initfile.write(f"MAJOR_VERSION = {icd_version}\n")
        
class BuildPy (build_py_orig):
    def run(self):
        self.run_command('build_proto')
        super(BuildPy, self).run()

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cartaproto",
    version="0.0.2",
    author="Adrianna Pińska",
    author_email="adrianna.pinska@gmail.com",
    description="Python interface to the CARTA backend",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/idia-astro/carta-python-icd",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
    install_requires=[
        "websockets>=9.1",
    ],
    cmdclass={
        "build_py": BuildPy,
        "build_proto": BuildProto,
    },
)
