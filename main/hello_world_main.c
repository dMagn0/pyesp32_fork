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
#include "esp_adc/adc_oneshot.h"

/*
 * New Protocol Format:
 * Position 1: Operation (r=read, w=write)
 * Position 2: Type (a=analog, d=digital)
 * Position 3-4: Address (2 digits: 00-99)
 * Position 5-11: Value (7 digits: 0000000-9999999)
 *
 * Example: ra040000000 = read analog from GPIO4
 * Example: wd050000001 = write digital to GPIO5, value 1
 */

// Structure to hold parsed message
typedef struct {
    char operation;  // 'r' or 'w'
    char type;       // 'a' or 'd'
    int address;     // GPIO number (0-99)
    int value;       // Value (0-9999999)
} protocol_message_t;

// Function to build protocol message
void build_message(char* buffer, char operation, char type, int address, int value) {
    snprintf(buffer, 12, "%c%c%02d%07d", operation, type, address, value);
}

// Function to parse protocol message
int parse_message(const char* message, protocol_message_t* parsed) {
    if (strlen(message) < 11) {
        printf("Invalid message length: %d (expected 11)\n", (int)strlen(message));
        return 0;
    }

    parsed->operation = message[0];
    parsed->type = message[1];

    // Parse address (2 digits)
    char addr_str[3] = {0};
    strncpy(addr_str, message + 2, 2);
    parsed->address = atoi(addr_str);

    // Parse value (7 digits)
    char value_str[8] = {0};
    strncpy(value_str, message + 4, 7);
    parsed->value = atoi(value_str);

    // Validate operation
    if (parsed->operation != 'r' && parsed->operation != 'w') {
        printf("Invalid operation: %c (expected 'r' or 'w')\n", parsed->operation);
        return 0;
    }

    // Validate type
    if (parsed->type != 'a' && parsed->type != 'd') {
        printf("Invalid type: %c (expected 'a' or 'd')\n", parsed->type);
        return 0;
    }

    // Validate address range
    if (parsed->address < 0 || parsed->address > 39) {
        printf("Invalid GPIO address: %d (valid range: 0-39)\n", parsed->address);
        return 0;
    }

    return 1;
}

// Map GPIO number to ADC channel (for analog operations)
// Note: Only certain GPIOs support ADC on ESP32
adc_channel_t gpio_to_adc_channel(int gpio) {
    // ADC1 channels (GPIO 32-39)
    switch(gpio) {
        case 36: return ADC_CHANNEL_0;  // GPIO36
        case 37: return ADC_CHANNEL_1;  // GPIO37
        case 38: return ADC_CHANNEL_2;  // GPIO38
        case 39: return ADC_CHANNEL_3;  // GPIO39
        case 32: return ADC_CHANNEL_4;  // GPIO32
        case 33: return ADC_CHANNEL_5;  // GPIO33
        case 34: return ADC_CHANNEL_6;  // GPIO34
        case 35: return ADC_CHANNEL_7;  // GPIO35
        // ADC2 channels (GPIO 0, 2, 4, 12-15, 25-27)
        case 4:  return ADC_CHANNEL_0;  // GPIO4 (ADC2)
        case 0:  return ADC_CHANNEL_1;  // GPIO0 (ADC2)
        case 2:  return ADC_CHANNEL_2;  // GPIO2 (ADC2)
        case 15: return ADC_CHANNEL_3;  // GPIO15 (ADC2)
        case 13: return ADC_CHANNEL_4;  // GPIO13 (ADC2)
        case 12: return ADC_CHANNEL_5;  // GPIO12 (ADC2)
        case 14: return ADC_CHANNEL_6;  // GPIO14 (ADC2)
        case 27: return ADC_CHANNEL_7;  // GPIO27 (ADC2)
        case 25: return ADC_CHANNEL_8;  // GPIO25 (ADC2)
        case 26: return ADC_CHANNEL_9;  // GPIO26 (ADC2)
        default: return -1;
    }
}

// Check if GPIO uses ADC1 or ADC2
int gpio_to_adc_unit(int gpio) {
    if (gpio >= 32 && gpio <= 39) {
        return ADC_UNIT_1;
    } else if (gpio == 0 || gpio == 2 || gpio == 4 ||
               (gpio >= 12 && gpio <= 15) ||
               (gpio >= 25 && gpio <= 27)) {
        return ADC_UNIT_2;
    }
    return -1;  // Not an ADC pin
}

// Function to process the protocol message and generate response
void process_message(const char* message, adc_oneshot_unit_handle_t adc1_handle,
                     adc_oneshot_unit_handle_t adc2_handle) {
    protocol_message_t parsed;

    if (!parse_message(message, &parsed)) {
        return;
    }

    char response[12] = {0};
    int result_value = 0;

    if (parsed.operation == 'r') {
        // READ operation
        if (parsed.type == 'a') {
            // Analog read
            int adc_unit = gpio_to_adc_unit(parsed.address);
            adc_channel_t channel = gpio_to_adc_channel(parsed.address);

            if (adc_unit == -1 || channel == -1) {
                printf("GPIO%d does not support ADC\n", parsed.address);
                return;
            }

            adc_oneshot_unit_handle_t handle = (adc_unit == ADC_UNIT_1) ? adc1_handle : adc2_handle;

            if (adc_oneshot_read(handle, channel, &result_value) == ESP_OK) {
                build_message(response, 'r', 'a', parsed.address, result_value);
                uart_write_bytes(UART_NUM_0, response, 11);
                uart_write_bytes(UART_NUM_0, "\n", 1);
            } else {
                printf("Failed to read ADC on GPIO%d\n", parsed.address);
            }
        } else {
            // Digital read
            gpio_set_direction(parsed.address, GPIO_MODE_INPUT);
            result_value = gpio_get_level(parsed.address);

            build_message(response, 'r', 'd', parsed.address, result_value);
            uart_write_bytes(UART_NUM_0, response, 11);
            uart_write_bytes(UART_NUM_0, "\n", 1);
        }
    } else if (parsed.operation == 'w') {
        // WRITE operation
        if (parsed.type == 'd') {
            // Digital write
            gpio_set_direction(parsed.address, GPIO_MODE_OUTPUT);
            int gpio_level = (parsed.value > 0) ? 1 : 0;
            gpio_set_level(parsed.address, gpio_level);

            // Send confirmation
            build_message(response, 'w', 'd', parsed.address, gpio_level);
            uart_write_bytes(UART_NUM_0, response, 11);
            uart_write_bytes(UART_NUM_0, "\n", 1);
        } else {
            // Analog write not supported (would need DAC or PWM)
            printf("Analog write not supported\n");
        }
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
    printf("New Protocol Format:\n");
    printf("  Position 1: Operation (r=read, w=write)\n");
    printf("  Position 2: Type (a=analog, d=digital)\n");
    printf("  Position 3-4: Address (2 digits GPIO number)\n");
    printf("  Position 5-11: Value (7 digits)\n");
    printf("Example: ra040000000 = read analog from GPIO4\n");
    printf("Example: wd050000001 = write digital HIGH to GPIO5\n\n");

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

    // Configure ADC1 (GPIO 32-39)
    adc_oneshot_unit_handle_t adc1_handle;
    adc_oneshot_unit_init_cfg_t adc1_init_config = {
        .unit_id = ADC_UNIT_1,
    };
    adc_oneshot_new_unit(&adc1_init_config, &adc1_handle);

    // Configure ADC2 (GPIO 0, 2, 4, 12-15, 25-27)
    adc_oneshot_unit_handle_t adc2_handle;
    adc_oneshot_unit_init_cfg_t adc2_init_config = {
        .unit_id = ADC_UNIT_2,
    };
    adc_oneshot_new_unit(&adc2_init_config, &adc2_handle);

    // Configure ADC channels with 12-bit resolution and full-scale voltage
    adc_oneshot_chan_cfg_t adc_config = {
        .bitwidth = ADC_BITWIDTH_12,
        .atten = ADC_ATTEN_DB_12,
    };

    // Pre-configure commonly used ADC channels
    // ADC1 channels
    adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_0, &adc_config);  // GPIO36
    adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_4, &adc_config);  // GPIO32
    adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_5, &adc_config);  // GPIO33
    adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_6, &adc_config);  // GPIO34
    adc_oneshot_config_channel(adc1_handle, ADC_CHANNEL_7, &adc_config);  // GPIO35

    // ADC2 channels
    adc_oneshot_config_channel(adc2_handle, ADC_CHANNEL_0, &adc_config);  // GPIO4

    printf("ADC initialized for analog reads (12-bit, 0-4095 range)\n");

    char *data = (char *) malloc(1024);

    // Main loop to read serial data and process protocol messages
    while (1) {
        // Read data from UART
        int len = uart_read_bytes(UART_NUM_0, data, 1024, 20 / portTICK_PERIOD_MS);

        if (len > 0) {
            data[len] = '\0'; // Null terminate
            // Remove newline characters for cleaner output
            char *newline = strchr(data, '\n');
            if (newline) *newline = '\0';
            char *carriage = strchr(data, '\r');
            if (carriage) *carriage = '\0';

            if (strlen(data) > 0) {
                process_message(data, adc1_handle, adc2_handle);
            }
        }

        vTaskDelay(20 / portTICK_PERIOD_MS);
    }
}
