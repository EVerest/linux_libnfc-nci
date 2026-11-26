#!/usr/bin/env python3
"""Hardware-free checks for a native build with LIBNFCNCI_BUILD_EXAMPLES=ON.

Usage: python3 tests/test_config_paths.py BUILD_DIR --sysconfdir /usr/local/etc
Requires a C/C++ compiler and strace. All fixtures and probes use a temporary dir.
"""
import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PARSER_PROBE = r'''
#include "config_options.h"
int main(int argc, char **argv) {
    const char *path;
    int first = parse_config_options(argc, argv, &path);
    if (first < 0) return 1;
    printf("%s\n%d\n", path ? path : "<default>", first);
    return 0;
}
'''


class ConfigPaths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="nfc-config-tests-")
        cls.work = Path(cls.temp.name)
        cls.fixture = cls.work / "config with spaces"
        cls.fixture.mkdir()
        (cls.fixture / "libnfc-nci.conf").write_text("CONFIG_PATH_TEST=42\n")
        (cls.fixture / "libnfc-nxp.conf").write_text("CONFIG_PATH_TEST=84\n")
        cls.missing = cls.work / "missing"
        cls.missing.mkdir()
        cls.probe = cls.work / "config-paths"
        subprocess.run([
            "c++", "-std=c++17", str(ROOT / "tests/config_paths.cpp"),
            "-I" + str(ROOT / "src/include"),
            "-I" + str(ROOT / "src/libnfc-utils/inc"),
            "-I" + str(ROOT / "src/nxp_nci_hal_libnfc-nci/src/include"),
            "-I" + str(ROOT / "src/nxp_nci_hal_libnfc-nci/utils/include"),
            "-I" + str(ROOT / "src/nfcandroid_nfc_hidlimpl/halimpl/utils"),
            "-L" + str(BUILD), "-Wl,-rpath," + str(BUILD), "-lnfc_nci",
            "-o", str(cls.probe),
        ], check=True)
        cls.demo_probe = cls.work / "demo-config.so"
        subprocess.run([
            "c++", "-std=c++17", "-shared", "-fPIC", str(ROOT / "tests/demo_config.cpp"),
            "-I" + str(ROOT / "src/libnfc-utils/inc"),
            "-L" + str(BUILD), "-Wl,-rpath," + str(BUILD), "-lnfc_nci",
            "-o", str(cls.demo_probe),
        ], check=True)
        source = cls.work / "parser.c"
        source.write_text(PARSER_PROBE)
        cls.parsers = []
        for compiler in ("cc", "c++"):
            binary = cls.work / ("parser-" + compiler)
            subprocess.run([compiler, "-Wall", "-Wextra", "-Werror", str(source),
                            "-I" + str(ROOT / "demoapp"), "-o", str(binary)], check=True)
            cls.parsers.append(binary)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_readers_and_api(self):
        for path in (str(self.fixture), str(self.fixture) + "/", self.fixture.name):
            with self.subTest(path=path):
                subprocess.run([self.probe, "override", path], cwd=self.work, check=True,
                               env={**os.environ, "MW_CONFIG_DIR": str(self.missing)})

    def test_no_fallback(self):
        trace = self.work / "files.trace"
        subprocess.run(["strace", "-e", "trace=%file", "-o", trace,
                        self.probe, "missing", self.missing], check=True)
        lines = [line for line in trace.read_text().splitlines() if ".conf\"" in line
                 and ("libnfc-nci.conf" in line or "libnfc-nxp.conf" in line)]
        self.assertTrue(any("libnfc-nci.conf" in line for line in lines))
        self.assertTrue(any("libnfc-nxp.conf" in line for line in lines))
        self.assertTrue(all(str(self.missing) in line for line in lines), lines)

    def test_compiled_default(self):
        trace = self.work / "default.trace"
        subprocess.run(["strace", "-e", "trace=%file", "-o", trace,
                        self.probe, "default", SYSCONFDIR], check=True)
        text = trace.read_text()
        self.assertIn(SYSCONFDIR.rstrip("/") + "/libnfc-nci.conf", text)
        self.assertIn(SYSCONFDIR.rstrip("/") + "/libnfc-nxp.conf", text)

    def test_parser_priority_and_arguments(self):
        cases = [([], "", "<default>", 1), ([], "/env", "/env", 1),
                 (["--config-dir", "/cli", "poll"], "/env", "/cli", 3),
                 (["--config-dir=/cli", "poll", "--type=Text"], "/env", "/cli", 2),
                 (["--config-dir", "relative path"], "", "relative path", 3),
                 (["--config-dir=/first", "--config-dir=/last"], "", "/last", 3)]
        for binary in self.parsers:
            for args, env, path, first in cases:
                result = subprocess.run([binary, *args], capture_output=True, text=True,
                                        env={**os.environ, "NFC_CONFIG_DIR": env}, check=True)
                self.assertEqual(result.stdout, f"{path}\n{first}\n")

    def test_demo_errors_and_help(self):
        for demo in ("nfc_demo", "nfc_cb_example"):
            binary = BUILD / demo
            for args in (["--config-dir"], ["--config-dir="], ["--config-dir", ""],
                         ["--config-dir", "--help"]):
                result = subprocess.run([binary, *args], capture_output=True)
                self.assertNotEqual(result.returncode, 0, (demo, args))
                self.assertIn(b"requires a non-empty directory", result.stderr)
            result = subprocess.run([binary, "--help"], capture_output=True, check=True)
            self.assertIn(b"NFC_CONFIG_DIR", result.stdout)
            self.assertNotIn(b"../../build/dist", binary.read_bytes())

    def test_demo_path_selection(self):
        for demo, command in (("nfc_demo", ["poll"]), ("nfc_cb_example", [])):
            cases = [([], "", SYSCONFDIR), ([], str(self.fixture), str(self.fixture)),
                     (["--config-dir", str(self.fixture)], str(self.missing), str(self.fixture)),
                     (["--config-dir=" + str(self.fixture)], str(self.missing), str(self.fixture))]
            for args, env, expected in cases:
                with self.subTest(demo=demo, args=args, env=env):
                    result = subprocess.run(
                        [BUILD / demo, *args, *command], capture_output=True, text=True,
                        timeout=5, check=True, env={**os.environ, "NFC_CONFIG_DIR": env,
                                                   "LD_PRELOAD": str(self.demo_probe)})
                    self.assertIn("DEMO_CONFIG=" + expected.rstrip("/") + "/libnfc-nxp.conf",
                                  result.stdout)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_dir", type=Path)
    parser.add_argument("--sysconfdir", required=True)
    args = parser.parse_args()
    BUILD = args.build_dir.resolve()
    SYSCONFDIR = args.sysconfdir
    unittest.main(argv=[__file__], verbosity=2)
