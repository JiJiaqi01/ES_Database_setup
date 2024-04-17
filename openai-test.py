from openai import OpenAI

client = OpenAI(
    base_url = 'https://api.chatanywhere.com.cn/v1',
    api_key = 'sk-AUnJk0FMih4MJp32GAyNzEQRi5KtVeiZlvRU6tROmaOAFvD9',
    # http_client=httpx.Client(
    #   base_url= config.OpenAI.host,
    #   follow_redirects = True,
    # ),
)

completion = client.chat.completions.create(
  model="gpt-3.5-turbo",
  messages=[
    {"role": "system", "content": "You are a poetic assistant, skilled in explaining complex programming concepts with creative flair."},
    {"role": "user", "content": "Compose a poem that explains the concept of recursion in programming."}
  ]
)

print(completion.choices[0].message)
