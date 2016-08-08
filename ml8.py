"""
This program is a Seattle parks address finder. It is to be used for Amazon Alexa
products. The user invokes the skill through an Alexa product and asks for the
address of a Seattle park. The program will search through a current list of parks
from data.gov.seattle website API:
https://data.seattle.gov/Parks-and-Recreation/Seattle-Parks-And-Recreation-Park-Addresses/v5tj-kqhc
If the user desired park is contained in the list, the address for the park ia returned to
the user. Otherwise the user is notified that their park cannot be found.
"""

from __future__ import print_function
import urllib2
import json
url = "https://data.seattle.gov/resource/ajyh-m2d3.json"
data = json.load(urllib2.urlopen(url))
park_list =[]


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])


def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "SetPark":
        return set_park_in_session(intent, session)
    elif intent_name == "GetAddress":
        return get_address_from_desired_park(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.NoIntent":
        session['attributes'] = None
        return get_address_from_desired_park(intent, session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])

# --------------- Functions that control the skill's behavior ------------------


def get_welcome_response():
    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the park address finder. " \
                    "Please tell me the name of the park you wish to locate. " \
                    "For example say where is Green lake park. "

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "Please tell me the name of the park you wish to locate. " \
                    "For example say where is Green lake. "
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Thank you for using the park address finder. " \
                    "Good bye! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def set_park_in_session(intent, session):
    """ Sets the desired park in the session and prepares the speech to reply to the
    user.
    """
    card_title = intent['name']
    session_attributes = {}
    should_end_session = False
    park_list[:] =[]
    for row in data:
        name = row['name']
        if intent['slots']['Park']['value'].lower() in name.lower():
            park_list.append(row)


    if ('Park' in intent['slots']) and len(park_list) > 0:
        desired_park = intent['slots']['Park']['value']
        session_attributes = create_desired_park(desired_park)
        speech_output = "Are you looking for the address of " + park_list[0]['name']
        reprompt_text = "Are you looking for the address of " + park_list[0]['name']
    else:
        speech_output = "I'm not sure which park you are trying to locate. " \
                        "Please try again."
        reprompt_text = "Please tell me the name of the park you wish to locate. " \
                        "For example say where is Green lake park. "

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def create_desired_park(desired_park):
    return{"desiredPark": desired_park}


def get_address_from_desired_park(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "desiredPark" in session.get('attributes', {}) and len(park_list) > 0:
        desired_park = session['attributes']['desiredPark']
        speech_output = "The address for " + park_list[0]['name'] + " is located at " \
                        + park_list[0]['address']
        should_end_session = True
    else:
        speech_output = "I'm sorry I could not get the address of your desired park"
        should_end_session = False

    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))

# --------------- Helpers that build all of the responses ----------------------


def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': 'SessionSpeechlet - ' + title,
            'content': 'SessionSpeechlet - ' + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }