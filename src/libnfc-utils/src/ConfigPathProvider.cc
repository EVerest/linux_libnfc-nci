/******************************************************************************
*
* Copyright 2020 NXP.
* NXP Confidential. This software is owned or controlled by NXP and may only be
* used strictly in accordance with the applicable license terms.  By expressly
* accepting such terms or by downloading, installing, activating and/or
* otherwise using the software, you are agreeing that you have read, and that
* you agree to comply with and are bound by, such license terms.  If you do not
* agree to be bound by the applicable license terms, then you may not retain,
* install, activate or otherwise use the software.
*
******************************************************************************/

/******************************************************************************
 *
 *  The original Work has been changed by PIONIX GmbH in 11-2024
 *
 ******************************************************************************/
#include <android-base/stringprintf.h>
#include <base/logging.h>
#include "configPathProvider.h"
#include <vector>
#include<sys/stat.h>
extern bool nfc_debug_enabled;
extern string nfc_storage_path;
using android::base::StringPrintf;
string ConfigPathProvider::s_configPath {CONFIG_PATH};
ConfigPathProvider::ConfigPathProvider() {}

/*******************************************************************************
**
** Function         getInstance
**
** Description      returns the static instance of ConfigPathProvider
**
** Returns          ConfigPathProvider instance
*******************************************************************************/
ConfigPathProvider &ConfigPathProvider::getInstance() {
static ConfigPathProvider mConfigPathProviderInstance;
return mConfigPathProviderInstance;
}

/*******************************************************************************
**
** Function         getFilePath
**
** Description      Returns file path of requested type of file
**
** Returns          file path
**
*******************************************************************************/
string ConfigPathProvider::getFilePath(FileType type) {
    DLOG_IF(INFO, nfc_debug_enabled)
        << StringPrintf("%s: enter FileType:0x%02x", __func__, type);
    switch (type) {
    case VENDOR_NFC_CONFIG: {
        string path = s_configPath + "libnfc-nxp.conf";
        return path;
    } break;
    case VENDOR_ESE_CONFIG: {
        string path = s_configPath + "libese-nxp.conf";
        return path;
    } break;
    case SYSTEM_CONFIG: {
        const vector<string> searchPath = { s_configPath };
        for (string path : searchPath) {
            path.append("libnfc-nci.conf");
            LOG(INFO) << "path: " << path;
            struct stat file_stat;
            if (stat(path.c_str(), &file_stat) != 0) continue;
            if (S_ISREG(file_stat.st_mode)) return path;
        }
        return "";
    } break;
    case RF_CONFIG: {
        string path = s_configPath + "etc//libnfc-nxp_RF.conf";
        return path;
    } break;
    case TRANSIT_CONFIG: {
        string path = s_configPath + "libnfc-nxpTransit.conf";
        return path;
    } break;
    case NFASTORAGE_BIN: {
        string path = ".\\data\\nfc";
        nfc_storage_path.assign(path);
        return nfc_storage_path;
    } break;
    case FIRMWARE_LIB: {
        string path = s_configPath + "libsn100u_fw.dll";
        return path;
    } break;
    case CONFIG_TIMESTAMP: {
        string path = s_configPath + "libnfc-nxpConfigState.bin";
        return path;
    } break;
    case RF_CONFIG_TIMESTAMP: {
        string path = s_configPath + "libnfc-nxpRFConfigState.bin";
        return path;
    } break;
    case TRANSIT_CONFIG_TIMESTAMP: {
        string path = s_configPath + "libnfc-nxpTransitConfigState.bin";
        return path;
    } break;

    default:
        DLOG_IF(INFO, nfc_debug_enabled)
            << StringPrintf("%s: Unnknown FileType", __func__);
        break;
    }
}

/*******************************************************************************
**
** Function         setConfigPath
**
** Description      set search path for config files
**
** Returns          None
**
*******************************************************************************/
void ConfigPathProvider::setConfigPath(const string &path) {
    if (!path.empty()) {
        ConfigPathProvider::s_configPath = path.back() == '/' ? path : path + "/";
    }
}
