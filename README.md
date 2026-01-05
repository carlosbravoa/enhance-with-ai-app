# enhance-with-ai-app
A ChatGPT GTK app for Ubuntu.
It will allow you to paste from clipboard a text and run typical tasks such as summarize, enhance, explain, proofread, etc.
You can also write your own prompt.

Clone this repo and run this app with the python script in the root of this repo:

```
./enhance-with-ai.py
```

or

```
python3 enhance-with-ai.py
```

## Requirements

- Python 3.10+
- The openai Python package `pip install openai` (If you are on Ubuntu 24.04 or later, `apt install python3-openai`
- A valid OpenAI API key

## Setting your OpenAI API key

The application reads the API key from `~/.config/enhance-with-ai/config`
But it will create it for you on the first run. After the config file has been created, feel free to
edit it with any text editor and add your own API Key there (sk-XXX)


