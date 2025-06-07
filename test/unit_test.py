import requests
from uuid import uuid4

base_url = "http://localhost:7860"
ingest_endpoint = "/ingest_files"
generator_endpoint = "/fetch_response"
get_metadata_endpoint = "/get_metadata"

collection_name = str(uuid4())
testcase_passed = 0
total_tests = 3


def test_ingest_files():
    global testcase_passed
    metadata = {"metadata": "legal,nda,confidential", "group_name": collection_name}
    with open("test/sample1.pdf", "rb") as f:
        files = [("files", ("sample1.pdf", f, "application/pdf"))]
        response = requests.post(base_url + ingest_endpoint, files=files, data=metadata)
    print("Testing:", ingest_endpoint)
    print("Status:", response.status_code)
    print("Response:", response.content)
    assert response.status_code == 200, "Ingest endpoint failed"
    testcase_passed += 1


def test_llm_generation():
    global testcase_passed
    params = {"query": "How was past year performance", "group_name": collection_name}
    response = requests.post(base_url + generator_endpoint, params=params)
    print("Testing:", generator_endpoint)
    print("Status:", response.status_code)
    print("Response:", response.content)
    assert response.status_code == 200, "LLM generation endpoint failed"
    testcase_passed += 1


def test_get_metadata():
    global testcase_passed
    response = requests.get(base_url + get_metadata_endpoint)
    print("Testing:", get_metadata_endpoint)
    print("Status:", response.status_code)
    print("Response:", response.content)
    assert response.status_code == 200, "Metadata endpoint failed"
    testcase_passed += 1


if __name__ == "__main__":
    try:
        test_ingest_files()
        test_llm_generation()
        test_get_metadata()
    except AssertionError as e:
        print("Test failed:", e)

    print(f"{testcase_passed}/{total_tests} tests passed")
