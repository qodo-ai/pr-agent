curl -s --no-buffer "https://api.cli.qodo.ai/v1/auth/cli-auth" | while read line; do
  [[ $line == data:*auth_url* ]] && open "$(echo "$line" | sed 's/.*"auth_url":"\([^"]*\)".*/\1/' | sed 's/\\//g')"
  [[ $line == data:*api_key* ]] && echo "$line" && break
done
