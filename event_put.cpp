#include <iostream>
#include <cstdlib>

int main() {

    std::string cmd =
        "aws dynamodb put-item "
        "--table-name events "
        "--item '{"
            ""eventId":{"S":"e400"},"
            ""version":{"N":"1"},"
            ""userId":{"S":"user-1"},"
            ""timestamp":{"N":"1700000000000"},"
            ""lamportClock":{"N":"1"},"
            ""status":{"S":"ACTIVE"}"
        "}' "
        "--endpoint-url http://localhost:8000/";

    int result = system(cmd.c_str());

    if (result == 0) {
        std::cout << " Event uspjesno upisan u DynamoDB Local\n";
    } else {
        std::cout << " Greska pri upisu eventa\n";
    }

    return 0;
}