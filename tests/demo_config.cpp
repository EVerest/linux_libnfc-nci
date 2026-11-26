// SPDX-License-Identifier: Apache-2.0
#include "configPathProvider.h"
#include <cstdio>
#include <cstdlib>

// Stop each real demo immediately before NFC hardware would be initialized.
// Reading the provider here also checks that CLI/environment selection precedes
// the first configuration access.
extern "C" void InitializeLogLevel(void) {
    std::printf("DEMO_CONFIG=%s\n", cfgPathProvider.getFilePath(VENDOR_NFC_CONFIG).c_str());
    std::fflush(stdout);
    std::_Exit(0);
}
