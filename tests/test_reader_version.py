#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Hardware-free API/startup checks: python3 tests/test_reader_version.py BUILD_DIR."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILD = Path(sys.argv[1]).resolve()
STARTUP_PROBE = r'''
#include "linux_nfc_api.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

extern uint32_t wFwVerRsp;

/* Replace hardware initialization only; use the real getFwVersion(). */
void InitializeLogLevel(void) {}
int doInitialize(void) {
    wFwVerRsp = (uint32_t)strtoul(getenv("NFC_TEST_FW_VERSION"), NULL, 16);
    return getenv("NFC_TEST_INIT_FAILURE") != NULL ? 1 : 0;
}
void registerTagCallback(nfcTagCallback_t *callback) { (void)callback; }
int nfcSnep_registerClientCallback(nfcSnepClientCallback_t *callback) {
    (void)callback;
    return 0;
}
static void finish(void) { fflush(stdout); _Exit(0); }
void doEnableDiscovery(int masks, int reader, int routing, int restart) {
    (void)masks; (void)reader; (void)routing; (void)restart;
    finish();
}
void nfcSnep_stopServer(void) { finish(); }
'''


class ReaderVersion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="nfc-reader-version-")
        source = Path(cls.temp.name) / "startup.c"
        cls.probe = Path(cls.temp.name) / "startup.so"
        source.write_text(STARTUP_PROBE)
        subprocess.run(["cc", "-shared", "-fPIC", "-Wall", "-Wextra", "-Werror",
                        "-I" + str(ROOT / "src/include"), str(source),
                        "-o", str(cls.probe)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_api_returns_reader_cache(self):
        library = ctypes.CDLL(str(BUILD / "libnfc_nci.so"))
        version = ctypes.c_uint32.in_dll(library, "wFwVerRsp")
        previous = version.value
        try:
            for raw, expected in ((0, 0), (0x125009, 0x125009),
                                  (0x125011, 0x125011), (0xAB12500A, 0x12500A)):
                version.value = raw
                self.assertEqual(library.getFwVersion(), expected)
        finally:
            version.value = previous

    def startup(self, version, fail=False):
        env = {**os.environ, "LD_PRELOAD": str(self.probe), "NFC_TEST_FW_VERSION": version}
        env.pop("NFC_TEST_INIT_FAILURE", None)
        if fail:
            env["NFC_TEST_INIT_FAILURE"] = "1"
        return subprocess.run([BUILD / "nfc_demo", "poll"], env=env,
                              capture_output=True, text=True, timeout=5, check=True).stdout

    def test_startup_formats_hex_version(self):
        for raw, formatted in (("125009", "12.50.09"), ("125011", "12.50.11"),
                               ("12500a", "12.50.0A")):
            output = self.startup(raw)
            self.assertEqual(output.count("Reader firmware version:"), 1)
            self.assertIn("Reader firmware version: " + formatted, output)

    def test_unavailable_version(self):
        self.assertIn("Reader firmware version: unavailable", self.startup("0"))

    def test_failed_initialization(self):
        output = self.startup("125011", fail=True)
        self.assertIn("NfcService Init Failed", output)
        self.assertNotIn("Reader firmware version:", output)


if __name__ == "__main__":
    unittest.main(argv=[__file__], verbosity=2)
