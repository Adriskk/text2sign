
# text2sign

An application for translating sentence to it's representation in sign language.

<img width="512" alt="image" src="https://github.com/user-attachments/assets/10b7ada0-dd90-4b7b-b0ea-60500cc40b2d">

## Uses:
* Uses web scraping to retrievie single word videos
* OpenAI for generating ASL translated sentence
* Machine Learning Model for picking correct videos that matches given ASL word
* Video concatenator for merging single word videos into one
* Custom logging system
* Loading config from .ini file



## Install & Run

To install all dependencies of this project run 

```cmd
  pip install -r requirements.txt
```

or

```cmd
  pip3 install -r requirements.txt
```
When installing ffmpeg, it needs to be added to PATH in order to work correctly.


Then run using

```cmd
  python main.py
```

After that create .env file in the base folder of the project

The program will then start to download all word videos
from the internet using selenium module.

Est. download time is ~ **3h**.

After that time the program will train the ML model based on scraped data.
When training finishes, a window is being opened - enter your sentence.

<img width="1036" alt="image" src="https://github.com/user-attachments/assets/af5efc5c-4f62-462d-bb29-1b9cedcb0331">

## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`OPENAI_API_KEY` - OpenAI api key

## Videos source
All videos program uses are being scraped from [SigningSavvy](https://www.signingsavvy.com/)
