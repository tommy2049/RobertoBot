import json
import sys
import requests
# from requests_toolbelt.adapters import appengine
import os 
from flask import Flask, request, render_template, redirect, session
# from  __builtin__ import any as b_any


app = Flask(__name__)


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

introduction = "Hello! My name is Roberto, I'm trying to be a comedian but I need some help. See I'm a machine so I don't know what jokes are funny, can you help me? I'm going to tell you a joke, send me a selfie of your reaction and I'll remember which jokes are funny :)."
greetings = ["hi", "hello", "hey", "how are you"]
joke = ["joke", "jokes"]
yes = ["yes","sure","ok","yea","ya"]
confused_message = "I'm sorry I don't know if you liked the joke or not, can you reply with a selfie?"


# remove everything after Name
def split_string(joke):
    result = ''.join(i for i in joke if not i.isdigit())
    sep = "Name"
    result = result.split(sep,1)[0]
    return result


# process user input and customize your message here, by default it echoes whatever you say to it
def process_text(sender_id, message_text):
    message_text = message_text.lower()
    confused = True
    for greet in greetings: 
        if greet in message_text:
            send_message(sender_id, introduction)
            confused = False
            break
    for j in joke:
        if j in message_text:
            r = requests.post('https://nahanni.cs.mcgill.ca/getJoke')
            result = split_string(r.text)
            send_message(sender_id, result)
            confused = False
            break
    if "yes" in message_text:
        r = requests.post('https://nahanni.cs.mcgill.ca/getJoke')
        result = split_string(r.text)
        send_message(sender_id, result)
        confused = False
    if "no" in message_text:
        send_message(sender_id, "you're no fun boohoo :(")
        confused = False
    if confused:
        send_message(sender_id, confused_message)


# does something with the image the user sends
def process_img(sender_id, message_img):
    data={'url': message_img}
    r = requests.post('https://nahanni.cs.mcgill.ca/index', json=data)
    emotion = r.content
    if "Happy" in emotion:
        data={'feedback':'Happy'}
        r = requests.post('https://nahanni.cs.mcgill.ca/giveFeedback', json=data)
        send_message(sender_id, "I'm glad you liked the joke! do you want another one?")
    elif "Sad" in emotion or "Neutral" in emotion:
        if emotion is "Sad":
            data={'feedback':'Sad'}
            r = requests.post('https://nahanni.cs.mcgill.ca/giveFeedback', json=data)
        elif emotion is "Neutral":
            data={'feedback':'Neutral'}
            r = requests.post('https://nahanni.cs.mcgill.ca/giveFeedback', json=data)
        send_message(sender_id, "Sucks you didn't like the joke, let me tell you another one if you like")
    else:
        send_message("woah, you're a mysterious person, I can't tell from your pokerface")


@app.route('/', methods=['GET'])
def verify_fb():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
    	if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
    		return "Verification token mismatch", 403
    	return request.args["hub.challenge"], 200
    return "This is great :))))", 200

@app.route('/', methods=['GET'])
def spitText():
    return ""

@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    if messaging_event["message"].get("text"):
                        message_text = messaging_event["message"]["text"]  # the message's text
                        process_text(sender_id, message_text)
                    if "attachments" in messaging_event["message"]:
                        message_img = messaging_event["message"]["attachments"][0]["type"]
                        if messaging_event["message"]["attachments"][0].get("payload"):
                            process_img(sender_id, messaging_event["message"]["attachments"][0]["payload"]["url"] )


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200

@app.errorhandler(500)
def server_error(e):
    return 'An internal error occurred.', 500

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()
