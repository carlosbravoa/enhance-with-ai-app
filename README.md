# Enhance With AI — A ChatGPT python application

A ChatGPT GTK app for Ubuntu.
It will allow you to paste from clipboard a text and run typical tasks such as summarize, enhance, explain, proofread, etc.
You can also write your own prompt.

Clone this repo and install the python package:

```
pip install .
```

You can also create your own snap if you want it packaged as an app, using snapcraft.

```
snapcraft pack
```

## Requirements
Requirements are handled now by pip, but here they are if you need to manage them manually.

- Python 3.10+
- The openai Python package `pip install openai` (If you are on Ubuntu 24.04 or later, `apt install python3-openai`
- A valid OpenAI API key

## Setting your OpenAI API key

The application saves the API key on your Gnome Keyring



