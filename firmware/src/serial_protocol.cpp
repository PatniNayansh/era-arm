#include "serial_protocol.h"

#include <Arduino.h>
#include <stdlib.h>

void SerialProtocol::begin(uint32_t baud) {
    Serial.begin(baud);
    bufLen_ = 0;
}

bool SerialProtocol::pollCommand(float targetsDeg[NUM_JOINTS]) {
    while (Serial.available() > 0) {
        char c = static_cast<char>(Serial.read());

        if (c == '\n') {
            buf_[bufLen_] = '\0';
            bufLen_ = 0;

            if (buf_[0] != 'P' || buf_[1] != ',') {
                return false;
            }

            char *cursor = buf_ + 2;
            for (uint8_t i = 0; i < NUM_JOINTS; i++) {
                char *end = nullptr;
                targetsDeg[i] = strtof(cursor, &end);
                if (end == cursor) {
                    return false; // malformed — missing field
                }
                cursor = (*end == ',') ? end + 1 : end;
            }
            return true;
        }

        if (bufLen_ < BUF_SIZE - 1) {
            buf_[bufLen_++] = c;
        } else {
            bufLen_ = 0; // overflow — drop the line
        }
    }
    return false;
}

void SerialProtocol::writeStatus(const float currentDeg[NUM_JOINTS], uint32_t timestampMs, bool watchdogTripped) {
    Serial.print('S');
    for (uint8_t i = 0; i < NUM_JOINTS; i++) {
        Serial.print(',');
        Serial.print(currentDeg[i], 2);
    }
    Serial.print(',');
    Serial.print(timestampMs);
    Serial.print(',');
    Serial.println(watchdogTripped ? 1 : 0);
}
