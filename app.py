from tweepy import API, OAuthHandler, Stream, StreamListener
from googletrans import Translator
import json
from time import sleep
import requests
import urllib3
import os
from dotenv import load_dotenv

load_dotenv('.env')
# Go to http://apps.twitter.com and create an app.
# The consumer key and secret will be generated for you after
consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')
mention = os.getenv('mention')

LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
    'fil': 'Filipino',
    'he': 'Hebrew'
}

LANGCODES = dict(map(reversed, LANGUAGES.items()))


class StdOutListener(StreamListener):
    """ A listener handles tweets that are received from the stream.
    This is a basic listener that just prints received tweets to stdout.
    """
    def on_data(self, data):
        global api, LANGUAGES, LANGCODES, mention
        decoded = json.loads(data)

        tweet = decoded['text']
        tweet_id = decoded['id_str']
        handle = decoded['user']['screen_name']

        if decoded['in_reply_to_status_id']:
            original_tweet = api.get_status(decoded['in_reply_to_status_id'], tweet_mode="extended")
            original = original_tweet.full_text
            split = tweet.split(mention)
            dest = None
            src = None

            if split[0]:
                source = split[0].lower().strip()
                if source in LANGCODES:
                    src = LANGCODES[source]
                elif source in LANGUAGES:
                    src = LANGUAGES[source]

            if len(split) > 1 and split[1]:
                destination = split[1].lower().strip()
                if destination in LANGCODES:
                    dest = LANGCODES[destination]
                elif destination in LANGUAGES:
                    dest = LANGUAGES[destination]

            if dest and src:
                translated = Translator().translate(original, dest=dest, src=src)
            elif dest:
                translated = Translator().translate(original, dest=dest)
            elif src:
                translated = Translator().translate(original, src=src)
            else:
                translated = Translator().translate(original)
            pre_text = "Hello @"+handle+", here's the translation you requested\n"
            translated_text = pre_text + translated.text
        else:
            translated_text = "Hello @"+handle+", you summoned me but didn't quote any tweet for me to translate."

        # print(translated_text)
        if len(translated_text) > 140:
            wrapped = word_wrap(translated_text, 140)
            split_wrap = wrapped.split("\n")
            first = split_wrap[0]
            # print("First: ", first)
            remaining = wrapped.replace(first, '').replace("\n", '')
            # print("Remaining: ", remaining)
            tweeted = api.update_status(first.replace('<br>', ''), tweet_id)
            if len(remaining) > 140:
                wrapped = word_wrap(remaining, 140)
                split_wrap = wrapped.split("\n")
                first = split_wrap[0]
                # print("S First: ", first)
                remaining = wrapped.replace(first, '').replace("\n", '')
                # print("S Remaining: ", remaining)
                tweeted = api.update_status(first.replace('<br>', ''), tweeted.id)
        else:
            api.update_status(translated_text, tweet_id)

        return True

    def on_error(self, status):
        print(status)


def word_wrap(string, width=80, ind1=0, ind2=0, prefix='<br>'):
    """ word wrapping function.
        string: the string to wrap
        width: the column number to wrap at
        prefix: prefix each line with this string (goes before any indentation)
        ind1: number of characters to indent the first line
        ind2: number of characters to indent the rest of the lines
    """
    string = prefix + ind1 * " " + string
    newstring = ""
    while len(string) > width:
        # find position of nearest whitespace char to the left of "width"
        marker = width - 1
        while not string[marker].isspace():
            marker = marker - 1

        # remove line from original string and add it to the new string
        newline = string[0:marker] + "\n"
        newstring = newstring + newline
        string = prefix + ind2 * " " + string[marker + 1:]

    return newstring + string


def print_error(_error):
    print(
        f"---------Error---------\n"
        f"Known error. Ignore. Nothing you can do.\n"
        f"{_error}\n"
        f"Sleeping for 1 minute then continuing.\n"
        f"-----------------------"
    )
    sleep(600)


if __name__ == '__main__':
    l = StdOutListener()
    auth = OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = API(auth)
    print('API created...')
    stream = Stream(auth, l)

    print('Streaming started...')
    while True:
        try:
            stream.filter(track=[mention])
        except urllib3.exceptions.ProtocolError as error:
            print_error(_error=error)
        except ConnectionResetError as error:
            print_error(_error=error)
        except ConnectionError as error:
            print_error(_error=error)
        except requests.exceptions.ConnectionError as error:
            print_error(_error=error)
        except Exception as error:
            print(
                f"---------Error---------\n"
                f"unknown error\n",
                error,
                f"Sleeping for 5 minute then continuing.\n"
                f"Twitter streaming continues.\n"
                f"-----------------------"
            )
            sleep(3000)