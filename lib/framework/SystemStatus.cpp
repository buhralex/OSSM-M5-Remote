#include <SystemStatus.h>

SystemStatus::SystemStatus(AsyncWebServer *server, SecurityManager *securityManager)
{
    server->on(SYSTEM_STATUS_SERVICE_PATH,
               HTTP_GET,
               securityManager->wrapRequest(std::bind(&SystemStatus::systemStatus, this, std::placeholders::_1),
                                            AuthenticationPredicates::IS_AUTHENTICATED));
}

void SystemStatus::systemStatus(AsyncWebServerRequest *request)
{
    AsyncJsonResponse *response = new AsyncJsonResponse(false, MAX_ESP_STATUS_SIZE);
    JsonObject root = response->getRoot();
    root["esp_platform"] = "esp32";
    root["max_alloc_heap"] = ESP.getMaxAllocHeap();
    root["psram_size"] = ESP.getPsramSize();
    root["free_psram"] = ESP.getFreePsram();
    root["cpu_freq_mhz"] = ESP.getCpuFreqMHz();
    root["free_heap"] = ESP.getFreeHeap();
    root["sketch_size"] = ESP.getSketchSize();
    root["free_sketch_space"] = ESP.getFreeSketchSpace();
    root["sdk_version"] = ESP.getSdkVersion();
    root["flash_chip_size"] = ESP.getFlashChipSize();
    root["flash_chip_speed"] = ESP.getFlashChipSpeed();
    root["fs_total"] = ESPFS.totalBytes();
    root["fs_used"] = ESPFS.usedBytes();

    response->setLength();
    request->send(response);
}
