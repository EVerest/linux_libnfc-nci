cmake_minimum_required(VERSION 3.15)

# Stand-alone CMakeLists.txt for testing of the libnfc-nci

project(libnfcnci_demo
    VERSION 1.0.0
    DESCRIPTION "NFC NCI library demo app"
    LANGUAGES C CXX)

find_package(libnfc-nci REQUIRED)

get_target_property(LIBNFCNCI_CONFIG_INSTALL_PATH libnfc_nci::libnfc_nci LIBNFCNCI_CONFIG_INSTALL_PATH)

message(STATUS "${LIBNFCNCI_CONFIG_INSTALL_PATH}")

install(FILES
        ../conf/libnfc-nxp.conf
        ../conf/libnfc-nci.conf
    DESTINATION
	    "${LIBNFCNCI_CONFIG_INSTALL_PATH}")

add_executable(nfc_cb_example)
target_sources(nfc_cb_example
    PRIVATE
        nfc_cb_example.cpp
)
target_link_libraries(nfc_cb_example
    PRIVATE
        libnfc_nci::libnfc_nci
)

add_executable(nfc_demo)
target_sources(nfc_demo
    PRIVATE
        main.c
        tools.c
)
target_link_libraries(nfc_demo
    PRIVATE
        libnfc_nci::libnfc_nci
)
