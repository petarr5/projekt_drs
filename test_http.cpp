#include <iostream>
#include <string>
#include <curl/curl.h>

size_t write_callback(void* contents, size_t size, size_t nmemb, void* userp) {
    ((std::string)userp)->append((char)contents, size * nmemb);
    return size * nmemb;
}

int main() {
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Ne mogu inicijalizirati curl\n";
        return 1;
    }

    std::string json =
        "{"
        ""TableName": "events","
        ""Item": {"
        ""eventId": {"S": "e101"},"
        ""version": {"N": "1"},"
        ""userId": {"S": "user-1"},"
        ""timestamp": {"N": "1700000000001"},"
        ""lamportClock": {"N": "1"},"
        ""status": {"S": "ACTIVE"}"
        "}"
        "}";

    struct curl_slist* headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/x-amz-json-1.0");
    headers = curl_slist_append(headers, "X-Amz-Target: DynamoDB_20120810.PutItem");
    headers = curl_slist_append(headers, "Authorization: fake");

    std::string response;

    curl_easy_setopt(curl, CURLOPT_URL, "http://localhost:8000/");
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json.c_str());
    curl_easy_setopt(curl, CURLOPT_POSTFIELDSIZE, json.size());
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);

    CURLcode res = curl_easy_perform(curl);

    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    if (res != CURLE_OK) {
        std::cerr << "Curl error: " << curl_easy_strerror(res) << std::endl;
    } else {
        std::cout << "HTTP status: " << http_code << std::endl;
        std::cout << "Odgovor servera: " << response << std::endl;
    }

    curl_easy_cleanup(curl);
    curl_slist_free_all(headers);
    return 0;
}