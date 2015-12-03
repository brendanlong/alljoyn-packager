#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys

from subprocess import call


class Package:
    def __init__(self, name, repo_name, scons_extra, dist, files, deps=None):
        self.name = name
        self.repo_name = repo_name
        self.scons_extra = scons_extra
        self.dist = dist
        self.files = files
        if deps:
            self.deps = deps
        else:
            self.deps = []


class Packager:
    def __init__(self, platform, package_type, variant, build_dir="build"):
        self.platform = platform
        self.package_type = package_type
        self.variant = variant
        self.build_dir = build_dir

    def checkout(self, package, version):
        git_url = "https://git.allseenalliance.org/gerrit/core/%s.git" % (package.repo_name)
        call(["mkdir", "-p", self.build_dir])
        path = os.path.join(self.build_dir, package.repo_name)
        if not os.path.exists(path):
            call(["git", "clone", git_url, package.repo_name], cwd=self.build_dir)
        call(["git", "checkout", "v%s" % (version)], cwd=path)

    def build(self, package, version):
        self.checkout(package, version)

        path = os.path.join(self.build_dir, package.repo_name)

        # Remove -Werror
        try:
            output = subprocess.check_output(["git", "grep", "--name-only", "--", "-Werror"],
                cwd=path)
            werror_files = [line
                            for line in output.decode("UTF-8").split("\n")
                            if line]
            for file_name in werror_files:
                full_name = os.path.join(path, file_name)
                with open(full_name, "r+") as f:
                    output = [line
                              for line in f
                              if "-Werror" not in line]
                    f.seek(0)
                    f.write("".join(output))
                    f.truncate()
        except subprocess.CalledProcessError:
            # git-grep returns non-zero when there's no match
            # This means we don't need to fix anything
            pass

        ret = call(["scons", package.scons_extra, "OS=linux",
            "CPU=%s" % self.platform, "VARIANT=%s" % (self.variant),
            "BUILD_SERVICES_SAMPLES=off", "POLICYDB=on",
            "WS=off"],
            cwd=path)
        if ret:
            raise Error()

    def package(self, package, version):
        self.build(package, version)

        out_dir = os.path.join(self.build_dir, package.repo_name,
            "build/linux", self.platform, self.variant, "dist", package.dist)
        call(["rm", "-rf", "include", "lib64"], cwd=out_dir)

        # Rename inc -> include
        call(["cp", "-r", "inc", "include"], cwd=out_dir)

        # Rename lib -> lib64 for 64-bit builds
        files = package.files
        if self.platform == "x86_64":
            call(["cp", "-r", "lib", "lib64"], cwd=out_dir)
            files = ["lib64" if file == "lib" else file
                     for file in files]

        args = ["fpm",
            "-a", self.platform,
            "-C", out_dir,
            "-f",
            "-n", package.name,
            "--prefix", "/usr",
            "-s", "dir",
            "-t", self.package_type,
            "-v", version]
        for dep in package.deps:
            args.extend(["-d", dep])
        args.extend(files)
        call(args)


PACKAGES = [
    Package("alljoyn", "alljoyn", "BINDINGS=cpp", "cpp", ["lib"]),
    Package("alljoyn-devel", "alljoyn", "BINDINGS=cpp", "cpp", ["include"], ["alljoyn"]),
    Package("alljoyn-daemon", "alljoyn", "BINDINGS=cpp", "cpp", ["bin/alljoyn-daemon"], ["alljoyn"]),

    Package("alljoyn-c", "alljoyn", "BINDINGS=c", "c", ["lib"]),
    Package("alljoyn-c-devel", "alljoyn", "BINDINGS=c", "c", ["include"], ["alljoyn-c"]),
]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", "-d", dest="variant", action="store_const",
        default="release", const="debug")
    parser.add_argument("--bindings", default="c,cpp",
        help="Comma-separated list of bindings to build. Options are c,cpp,java,js")
    parser.add_argument("--platform", default=platform.machine())
    parser.add_argument("--type", "-t", dest="package_type", default="rpm",
        help="The kind of package to build. See fpm's documentation. You probably want deb or rpm.")
    parser.add_argument("--version", default="15.09a")
    args = parser.parse_args()

    packager = Packager(args.platform, args.package_type, args.variant)
    for package in PACKAGES:
        packager.package(package, args.version)
