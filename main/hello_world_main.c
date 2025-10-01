/*
 * SPDX-FileCopyrightText: 2010-2022 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: CC0-1.0
 */

#include <stdio.h>
#include <inttypes.h>
#include <string.h>
#include <stdlib.h>
#include "sdkconfig.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_chip_info.h"
#include "esp_flash.h"
#include "esp_system.h"
#include "driver/uart.h"
#include "driver/gpio.h"

// Function to convert binary string to integer
int binary_string_to_int(const char* binary_str, int length) {
    int result = 0;
    for (int i = 0; i < length; i++) {
        if (binary_str[i] == '1') {
            result = (result << 1) + 1;
        } else if (binary_str[i] == '0') {
            result = result << 1;
        } else {
            return -1; // Invalid character
        }
    }
    return result;
}

// Function to process the 6-character message
void process_message(const char* message) {
    if (strlen(message) != 7) {
        printf("Invalid message length: %d (expected 6)\n", (int)strlen(message));
        return;
    }
    
    // Extract value (first 3 characters) and pin (last 3 characters)
    char operation[2] = {0};
    char value_str[4] = {0};
    char pin_str[4] = {0};
    
    strncpy(operation, message, 1);
    strncpy(value_str, message + 1, 3);
    strncpy(pin_str, message + 4, 3);

    // Convert binary strings to integers
    int op = binary_string_to_int(operation, 1);
    int value = binary_string_to_int(value_str, 3);
    int pin = binary_string_to_int(pin_str, 3);
    
    // Validate pin range (ESP32 has GPIO 0-39, but we'll limit to commonly used ones)
    if (pin < 0 || pin > 39) {
        printf("Invalid pin number: %d (valid range: 0-39)\n", pin);
        return;
    }

    if (op) {
        if (value < 0 || pin < 0) {
            printf("Invalid binary format in message: %s\n", message);
            return;
        }
        // Set GPIO pin as output if not already configured
        gpio_set_direction(pin, GPIO_MODE_OUTPUT);
        
        // Set the pin value (0 or any non-zero value)
        int gpio_level = (value > 0) ? 1 : 0;
        gpio_set_level(pin, gpio_level);
        
        printf("Set GPIO pin %d to %s (value: %d)\n", pin, gpio_level ? "HIGH" : "LOW", value);
    } else {
        // Read the pin value
        gpio_set_direction(pin, GPIO_MODE_INPUT);
        int pin_value = gpio_get_level(pin);
        printf("Read GPIO pin %d: %s (value: %d)\n", pin, pin_value ? "HIGH" : "LOW", pin_value);
    }
}

void app_main(void)
{
    printf("Hello world!\n");

    /* Print chip information */
    esp_chip_info_t chip_info;
    uint32_t flash_size;
    esp_chip_info(&chip_info);
    printf("This is %s chip with %d CPU core(s), %s%s%s%s, ",
           CONFIG_IDF_TARGET,
           chip_info.cores,
           (chip_info.features & CHIP_FEATURE_WIFI_BGN) ? "WiFi/" : "",
           (chip_info.features & CHIP_FEATURE_BT) ? "BT" : "",
           (chip_info.features & CHIP_FEATURE_BLE) ? "BLE" : "",
           (chip_info.features & CHIP_FEATURE_IEEE802154) ? ", 802.15.4 (Zigbee/Thread)" : "");

    unsigned major_rev = chip_info.revision / 100;
    unsigned minor_rev = chip_info.revision % 100;
    printf("silicon revision v%d.%d, ", major_rev, minor_rev);
    if(esp_flash_get_size(NULL, &flash_size) != ESP_OK) {
        printf("Get flash size failed");
        return;
    }

    printf("%" PRIu32 "MB %s flash\n", flash_size / (uint32_t)(1024 * 1024),
           (chip_info.features & CHIP_FEATURE_EMB_FLASH) ? "embedded" : "external");

    printf("Minimum free heap size: %" PRIu32 " bytes\n", esp_get_minimum_free_heap_size());

    printf("Waiting for serial data...\n");
    printf("Message format: VVVPPP (3-bit binary value + 3-bit binary pin)\n");
    printf("Example: 001100 = value=1, pin=4\n");

    // Configure UART
    const uart_config_t uart_config = {
        .baud_rate = 115200,
        .data_bits = UART_DATA_8_BITS,
        .parity = UART_PARITY_DISABLE,
        .stop_bits = UART_STOP_BITS_1,
        .flow_ctrl = UART_HW_FLOWCTRL_DISABLE,
        .source_clk = UART_SCLK_APB,
    };
    
    // We use UART_NUM_0 (USB/Serial)
    uart_driver_install(UART_NUM_0, 1024 * 2, 0, 0, NULL, 0);
    uart_param_config(UART_NUM_0, &uart_config);

    char *data = (char *) malloc(1024);
    
    // Main loop to read serial data
    while (1) {
        // Read data from UART
        int len = uart_read_bytes(UART_NUM_0, data, 1024, 100 / portTICK_PERIOD_MS);
        
        if (len > 0) {
            data[len] = '\0'; // Null terminate
            // Remove newline characters for cleaner output
            char *newline = strchr(data, '\n');
            if (newline) *newline = '\0';
            char *carriage = strchr(data, '\r');
            if (carriage) *carriage = '\0';
            
            if (strlen(data) > 0) {
                printf("Received message: %s\n", data);
                process_message(data);
            }
        }
        
        vTaskDelay(10 / portTICK_PERIOD_MS);
    }
}
