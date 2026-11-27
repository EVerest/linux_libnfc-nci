// SPDX-License-Identifier: Apache-2.0
#ifndef NFC_DEMO_CONFIG_OPTIONS_H
#define NFC_DEMO_CONFIG_OPTIONS_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Parse global options only; leave the command and its arguments untouched.
 * Return the first unconsumed argument, or -1 on invalid input. */
static inline int parse_config_options(int argc, char **argv, const char **path)
{
    int index = 1;
    *path = getenv("NFC_CONFIG_DIR");
    if (*path != NULL && (*path)[0] == '\0') {
        *path = NULL;
    }
    while (index < argc) {
        const char *value;
        if (strcmp(argv[index], "--config-dir") == 0) {
            if (++index == argc || strncmp(argv[index], "--", 2) == 0) {
                fprintf(stderr, "--config-dir requires a non-empty directory\n");
                return -1;
            }
            value = argv[index++];
        } else if (strncmp(argv[index], "--config-dir=", 13) == 0) {
            value = argv[index++] + 13;
        } else {
            break;
        }
        if (value[0] == '\0') {
            fprintf(stderr, "--config-dir requires a non-empty directory\n");
            return -1;
        }
        *path = value;
    }
    return index;
}

static inline void print_config_options(void)
{
    printf("Global options (before the command):\n");
    printf("  --config-dir PATH, --config-dir=PATH  Configuration directory\n");
    printf("  NFC_CONFIG_DIR supplies the directory if --config-dir is absent.\n");
    printf("  Otherwise the library uses its compiled sysconfdir.\n");
}

#endif
