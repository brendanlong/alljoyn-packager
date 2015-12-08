#!/usr/bin/env python3
import argparse
import os
import platform
import subprocess
import sys

from subprocess import call


class Repo:
    def __init__(self, repo, name):
        self.repo = repo
        self.name = name
        self.checked_out = False

    def checkout(self, build_dir, version):
        path = os.path.join(build_dir, self.name)
        if self.checked_out:
            return path

        call(["mkdir", "-p", build_dir])
        if not os.path.exists(path):
            call(["git", "clone", self.repo, self.name], cwd=build_dir)
        if call(["git", "checkout", "v%s" % (version)], cwd=path):
            raise Error("Failed to checkout git repo")
        self.checked_out = True
        return path


class Build:
    def __init__(self, repo, scons_extra, dist):
        self.repo = repo
        self.scons_extra = scons_extra
        self.dist = dist
        self.built = False

    def build(self, build_dir, version, variant, platform):
        if self.built:
            return

        path = self.repo.checkout(build_dir, version)

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

        ret = call(["scons", self.scons_extra, "OS=linux",
            "CPU=%s" % (platform), "VARIANT=%s" % (variant),
            "BUILD_SERVICES_SAMPLES=off", "POLICYDB=on",
            "WS=off"],
            cwd=path)
        if ret:
            raise Error("Failed to build")
        self.built = True


class Package:
    def __init__(self, name, build, files, deps=None):
        self.name = name
        self.build = build
        self.files = files
        if deps:
            self.deps = deps
        else:
            self.deps = []

    def package(self, build_dir, version, variant, platform, package_type):
        self.build.build(build_dir, version, variant, platform)

        out_dir = os.path.join(build_dir, self.build.repo.name,
            "build/linux", platform, variant, "dist", self.build.dist)
        call(["rm", "-rf", "include", "lib64"], cwd=out_dir)

        files = package.files

        # Rename inc -> include
        if "include" in files:
            call(["cp", "-r", "inc", "include"], cwd=out_dir)

        # Rename lib -> lib64 for 64-bit builds
        if platform == "x86_64" and "lib" in files:
            call(["cp", "-r", "lib", "lib64"], cwd=out_dir)
            files.remove("lib")
            files.append("lib64")

        if "jar" in files:
            files.remove("jar")
            jar_folder = os.path.join(out_dir, "jar")
            for name in os.listdir(jar_folder):
                if name.startswith("alljoyn") and name.endswith(".jar"):
                    files.append("jar/%s=share/java/%s" % (name, name))

        args = ["fpm",
            "-a", platform,
            "-C", out_dir,
            "-f",
            "-n", self.name,
            "--prefix", "/usr",
            "-s", "dir",
            "-t", package_type,
            "-v", version]
        for dep in package.deps:
            args.extend(["-d", dep])
        args.extend(files)
        call(args)


ALLJOYN_REPO = Repo("https://git.allseenalliance.org/gerrit/core/alljoyn.git", "alljoyn")

ALLJOYN_C = Build(ALLJOYN_REPO, "BINDINGS=c", "c")
ALLJOYN_CPP = Build(ALLJOYN_REPO, "BINDINGS=cpp", "cpp")
ALLJOYN_JAVA = Build(ALLJOYN_REPO, "BINDINGS=java", "java")

PACKAGES = [
    Package("alljoyn", ALLJOYN_CPP, ["lib"]),
    Package("alljoyn-devel", ALLJOYN_CPP, ["include"], ["alljoyn"]),
    Package("alljoyn-daemon", ALLJOYN_CPP, ["bin/alljoyn-daemon"], ["alljoyn"]),

    Package("alljoyn-c", ALLJOYN_C, ["lib"]),
    Package("alljoyn-c-devel", ALLJOYN_C, ["include"], ["alljoyn-c"]),
]

if "JAVA_HOME" in os.environ:
    PACKAGES.append(Package("alljoyn-java", ALLJOYN_JAVA, ["jar", "lib"]))

DISTRO_TO_PACKAGE_TYPE = {
    "Debian": "deb",
    "Fedora": "rpm",
    "Ubuntu": "deb"
}


if __name__ == "__main__":
    distro, _, _ = platform.linux_distribution()
    distro_package_type = DISTRO_TO_PACKAGE_TYPE.get(distro, None)

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--build-dir", default="build")
    parser.add_argument("--debug", "-d", dest="variant", action="store_const",
        default="release", const="debug", help="Pass this option to build debug packages")
    parser.add_argument("--platform", default=platform.machine(),
        help="AllJoyn's CPU. Should be detected automatically.")
    parser.add_argument("--type", "-t", dest="package_type",
        default=distro_package_type, required=(distro_package_type == None),
        help="The kind of package to build. See fpm's documentation. You probably want deb or rpm.")
    parser.add_argument("--version", default="15.09a", help="AllJoyn version to build. Will be used to pick git tag, and for package version.")
    args = parser.parse_args()

    for package in PACKAGES:
        package.package(args.build_dir, args.version, args.variant,
            args.platform, args.package_type)
