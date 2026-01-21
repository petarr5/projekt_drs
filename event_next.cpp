#include <iostream>
#include <cstdlib>
#include <ctime>

int main() {

    std::cout << " Dohvacam zadnji event...\n";

    system("aws dynamodb scan --table-name events --endpoint-url http://localhost:8000");

    int lastVersion;
    int lastClock;

    std::cout << "\nUpisi zadnju verziju koju vidis: ";
    std::cin >> lastVersion;

    std::cout << "Upisi zadnji Lamport clock: ";
    std::cin >> lastClock;

    int newVersion = lastVersion + 1;
    int newClock   = lastClock + 1;

    std::string status;
    if (newVersion == 2) status = "PROCESSING";
    else if (newVersion == 3) status = "DONE";
    else status = "UPDATED";

    std::string cmd =
        "aws dynamodb put-item "
        "--table-name events "
        "--item '{"
            "\"eventId\":{\"S\":\"e400\"},"
            "\"version\":{\"N\":\"" + std::to_string(newVersion) + "\"},"
            "\"userId\":{\"S\":\"user-1\"},"
            "\"timestamp\":{\"N\":\"1700000000000\"},"
            "\"lamportClock\":{\"N\":\"" + std::to_string(newClock) + "\"},"
            "\"status\":{\"S\":\"" + status + "\"}"
        "}' "
        "--endpoint-url http://localhost:8000";

    int result = system(cmd.c_str());

    if (result == 0) {
        std::cout << "\n Novi event spremljen!";
        std::cout << "\nVersion = " << newVersion;
        std::cout << "\nLamport = " << newClock;
        std::cout << "\nStatus = " << status << "\n";
    } else {
        std::cout << "\n Greska kod spremanja eventa\n";
    }

    return 0;
}