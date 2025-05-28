import requests
import json
import webbrowser

BASE_URL="https://api.cli.qodo.ai"
QM_CMD_ENDPOINT_KEY_NAME="qm_cmd_endpoint"

def get_api_key():
    try:
        url = f"{BASE_URL}/v1/auth/cli-auth?key_name={QM_CMD_ENDPOINT_KEY_NAME}"
        # Make HTTP request
        response = requests.get(url, stream=True,  # For SSE (Server-Sent Events)
                                headers={'Accept': 'text/event-stream'})

        # Parse Server-Sent Events format
        # Look for line:
        # data: {"auth_url":"https:\/\/auth.qodo.ai\/?extensionId=Codium.codium&extensionQuery=<SOME UUID>&uriScheme=cli"}
        opened_auth_url = False
        for line in response.iter_lines(decode_unicode=True):
            if line and line.startswith('data:'):
                data_json = line.replace('data: ', '', 1)
                try:
                    data = json.loads(data_json)
                    if not opened_auth_url:
                        if 'auth_url' not in data:
                            print(f"Expected an auth_url, but couldn't find one.")
                            return None
                        print(f"Got url: {data['auth_url']}.")
                        # Unescape the URL
                        auth_url = data['auth_url'].replace('\\/', '/')
                        webbrowser.open(auth_url)
                        opened_auth_url = True
                    else:
                        api_key = data.get('api_key', None)
                        print(f"Got api key: {api_key}.")
                        if not api_key:
                            print(f"Expected an api_key, but couldn't find one.")
                        return api_key
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    return None

        print("No data line found in response")
        return None

    except requests.exceptions.RequestException as e:
        print(f"Error making HTTP request: {e}")
        return None

def run():
    """This is the function serving as this file's entry point, as defined in pyproject.toml"""
    print("Attempting to generate an API Key...")

    api_key = get_api_key()
    if api_key:
        print(f"Please use the following API Key: {api_key} when invoking QM endpoint.")
        print(f"For example: curl -i --header \"Authorization: ApiKey {api_key}\" -X POST https://<QM ENDPOINT SERVER ADDR>/api/v1/qodo_merge_cmd")

if __name__ == "__main__":
    run()
