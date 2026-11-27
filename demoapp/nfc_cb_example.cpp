// SPDX-License-Identifier: Apache-2.0
// Copyright Pionix GmbH and Contributors to EVerest
#include <chrono>
#include <csignal>
#include <iostream>
#include <stdexcept>
#include <thread>


#include "linux_nfc_api.h"
#include "config_options.h"

// class declaration
class NfcHandler {
public:
    NfcHandler();
    void start();

private:
    void on_tag_arrival(nfc_tag_info_t*);
    void on_tag_departure();

    nfcTagCallback_t callbacks;
};

// signal handling 
bool stop = false;

void handleSigInt(int sig) {
    std::cout << "Caught signal " << sig << " (Ctrl+C)" << std::endl;
    stop = true;
}

// global instance variable (used for dispatching to the correct instance)
static NfcHandler* global_handler_instance{nullptr};

// definitions
NfcHandler::NfcHandler() {
    // we could have also used a singleton instance,
    if (global_handler_instance) {
        throw std::runtime_error("Only one global nfc handler instance allowed");
    }

    InitializeLogLevel();

    if (doInitialize() != 0) {
        throw std::runtime_error("Failed to initialize libnfc_nci library");
    }

    this->callbacks.onTagArrival = [](nfc_tag_info_t* tag_info) { global_handler_instance->on_tag_arrival(tag_info); };

    this->callbacks.onTagDeparture = []() { global_handler_instance->on_tag_departure(); };

    global_handler_instance = this;
}

void NfcHandler::start() {
    nfcManager_registerTagCallback(&this->callbacks);
    nfcManager_enableDiscovery(DEFAULT_NFA_TECH_MASK, 0x01, 0, 0x1);
}

void NfcHandler::on_tag_arrival(nfc_tag_info_t*) {
    // handle tag arrival
    std::cout << "Detected Tag Arrival" << std::endl;
}

void NfcHandler::on_tag_departure() {
    // handle tag departure
    std::cout << "Detected Tag Departure" << std::endl;
}

int main(int argc, char* argv[]) {
    const char* config_path;
    int first_arg = parse_config_options(argc, argv, &config_path);
    if (first_arg < 0) {
        return EXIT_FAILURE;
    }
    if (first_arg < argc) {
        if (first_arg == argc - 1 &&
            (strcmp(argv[first_arg], "--help") == 0 || strcmp(argv[first_arg], "-h") == 0)) {
            print_config_options();
            return EXIT_SUCCESS;
        }
        std::cerr << "Unexpected argument: " << argv[first_arg] << std::endl;
        print_config_options();
        return EXIT_FAILURE;
    }
    if (config_path != nullptr) {
        setConfigPath(config_path);
    }
    std::signal(SIGINT, handleSigInt);

    NfcHandler handler;

    handler.start();

    std::cout << "Wating for a tag ..." << std::endl;

    while (!stop) {
        std::this_thread::sleep_for(std::chrono::milliseconds(200));
    }

    return 0;
}
