#include <iostream>
#include <cstdlib>

int main() {

    std::string cmd =
        "aws dynamodb scan "
        "--table-name events "
        "--endpoint-url http://localhost:8000";

    std::cout << " Dohvacam eventove iz baze...\n\n";

    system(cmd.c_str());

    return 0;
}