// SPDX-License-Identifier: Apache-2.0
#include "linux_nfc_api.h"
#include "configPathProvider.h"
#include "nfc_config.h"
#include "phNxpConfig.h"

#include <cassert>
#include <string>

extern "C" int GetNumValue(const char*, void*, unsigned long);

int main(int argc, char** argv) {
    assert(argc == 3);
    const std::string mode = argv[1];
    const std::string base = argv[2];
    if (mode != "default") {
        setConfigPath("unused-directory");
        setConfigPath(base.c_str());
    }
    setConfigPath(nullptr);
    setConfigPath("");
    const auto directory = base.back() == '/' ? base : base + "/";
    assert(cfgPathProvider.getFilePath(VENDOR_NFC_CONFIG) == directory + "libnfc-nxp.conf");

    unsigned long value = 0;
    if (mode == "missing" || mode == "default") {
        // No NFC initialization: exercise the file readers directly.
        assert(!GetNumValue("CONFIG_PATH_TEST", &value, sizeof(value)));
        assert(!GetNxpNumValue("CONFIG_PATH_TEST", &value, sizeof(value)));
        if (mode == "missing") {
            assert(cfgPathProvider.getFilePath(SYSTEM_CONFIG).empty());
        }
    } else {
        assert(GetNumValue("CONFIG_PATH_TEST", &value, sizeof(value)) && value == 42);
        assert(GetNxpNumValue("CONFIG_PATH_TEST", &value, sizeof(value)) && value == 84);
        assert(NfcConfig::getUnsigned("CONFIG_PATH_TEST") == 42);
    }
}
