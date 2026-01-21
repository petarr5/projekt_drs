#include "httplib.h"
#include <iostream>
#include <cstdlib>
#include <ctime>

int lamportClock = 0;

std::string run_cmd(const std::string& cmd) {
    return std::to_string(system(cmd.c_str()));
}

int main() {
    srand(time(nullptr));
    httplib::Server server;

    server.Get("/ping", [](const httplib::Request&, httplib::Response& res) {
        res.set_content("Server radi \n", "text/plain");
    });

    server.Post("/event", [](const httplib::Request& req, httplib::Response& res) {
        lamportClock++;

        std::string eventId = "e" + std::to_string(rand() % 10000);
        int version = 1;

        std::string cmd =
            "aws dynamodb put-item "
            "--table-name events "
            "--endpoint-url http://localhost:8000 "
            "--item '{"
            "\"eventId\": {\"S\": \"" + eventId + "\"},"
            "\"version\": {\"N\": \"" + std::to_string(version) + "\"},"
            "\"userId\": {\"S\": \"user-1\"},"
            "\"timestamp\": {\"N\": \"" + std::to_string(time(nullptr)) + "\"},"
            "\"payload\": {\"S\": \"" + req.body + "\"},"
            "\"lamportClock\": {\"N\": \"" + std::to_string(lamportClock) + "\"},"
            "\"status\": {\"S\": \"ACTIVE\"}"
            "}'";

        std::cout << "Upisujem event u DynamoDB...\n";
        system(cmd.c_str());

        res.set_content("Event spremljen \n", "text/plain");
    });

    std::cout << "Server pokrenut na portu 8080...\n";
    server.listen("0.0.0.0", 8080);
}