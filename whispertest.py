import whisper
from pydub import AudioSegment
import sounddevice as sd
from scipy.io.wavfile import write
import os
import re
from language_tool_python import LanguageTool
import phonetic
import requests
from bs4 import BeautifulSoup
from metar import Metar
from gtts import gTTS
from playsound import playsound
from gtts import gTTS
from io import BytesIO
import pygame
import os
import sys
import getopt
import string
import re
import traceback
try:
    from urllib2 import urlopen
except:
    from urllib.request import urlopen

SUPPORTED_AIRPORTS = ['BIKF', 'BIRK', 'LHBP', 'BIAR', 'BIEG', 'BIEG', 'EPMO']

def get_metar(airport_code):
    # Retrieve the METAR data for the given airport
    BASE_URL = "http://tgftp.nws.noaa.gov/data/observations/metar/stations/" 
    url = "%s/%s.TXT" % (BASE_URL, airport_code)
    obs = ""
    try:
        urlh = urlopen(url)
        report = ""
        for line in urlh:
            if not isinstance(line, str):
                line = line.decode()  # convert Python3 bytes buffer to string
            if line.startswith(airport_code):
                report = line.strip()
                obs = Metar.Metar(line)
                print(obs.string())
                break
        if not report:
            print("No data for ", airport_code, "\n\n")
    except Metar.ParserError as exc:
        print("METAR code: ", line)
        print(string.join(exc.args, ", "), "\n")
    except:
        
        print(traceback.format_exc())
        print("Error retrieving", name, "data", "\n")
    # Return the METAR data as a string
    
    return obs

def create_acronymOfFourWords(string):

    acronym = [word[0] for word in string]
    # Join the list of first letters into a single string
    result = ''.join(acronym)

    return result

def getQNH(airports_data, icaoAirport):
    # Parse the METAR string using the python-metar library

    obs = airports_data[icaoAirport]
    
    # Extract the QNH from the parsed METAR data
    qnh = obs.press.value()

    return qnh

def getRunwayVisualRange(airports_data, icaoAirport):
    # Parse the METAR string using the python-metar library
    obs = airports_data[icaoAirport]
    # Extract the QNH from the parsed METAR data
    return str(obs.runway)
    

def getWeather(airports_data, icaoAirport):
    # Parse the METAR string using the python-metar library
    obs = airports_data[icaoAirport]
    # Extract the QNH from the parsed METAR data
    print("weather information for " + icaoAirport + " " + obs.present_weather())
    return obs.weather.value()


def getVisibility(airports_data, icaoAirport):
    # Parse the METAR string using the python-metar library
    obs = airports_data[icaoAirport]
    # Extract the QNH from the parsed METAR data
    if obs:
        return obs.visibility()
    else:
        return None


# look for a four word nato identifier of an airport at the end of a string
def find_nato(text):
    # Use a regular expression to search for four consecutive occurrences of NATO phonetic letters at the end of the string
    text = text.lower()
    pattern = r'\b(?:alfa|bravo|charlie|delta|echo|foxtrot|foxt\w*|golf|hotel|india|juliet|kilo|lima|mike|november|oscar|papa|quebec|romeo|sierra|tango|uniform|victor|whiskey|xray|yankee|zulu)\b'
    result = re.findall(pattern, text)
    # If the regular expression found a match, return the matched string
    if result:
        return result
    # If the regular expression did not find a match, return None
    else:
        return None


# look for keyword in the middle of string
def check_string(string, keyword):
    # CHeck for the presence of METAR and QNH and NATO phonetic letters
    string = string.lower()
    keyword = keyword.lower()

    result = re.search(keyword, string)
    if result:
        return result.group()
    # If the regular expression did not find a match, return None
    else:
        return None


def find_last_four_words(text):
    # Use a regular expression to find the last four words of the string
    pattern = r'\b\w+\b\s*\b\w+\b\s*\b\w+\b\s*\b\w+\b$'
    result = re.search(pattern, text)

    # If the regular expression found a match, return the matched string
    if result:
        return result.group()
    # If the regular expression did not find a match, return None
    else:
        return None

# extract from the start towards the first four numbers of i.e callsign.
def extractCallsign(string):
    # Use a regular expression to match the start of the sentence and the first four numbers
    match = re.search(r'^[^\d]*(\d{1,4})', string)
    retval = ""
    if match:
        # Get the first group from the match (the first four numbers)
        numbers = match.group(1)
    
        # Get the start of the sentence (everything before the first four numbers)
        start = string[:match.start(1)]
        retval = str( start + numbers)
    else:
        print("")
    
    return retval

def loadDataModel(printTxt=False):

    airports_data = {}
    for element in SUPPORTED_AIRPORTS:        
        airports_data[element.lower()] = get_metar(str(element))

    return airports_data

def speak(text, language='en'):
        mp3_fo = BytesIO()
        tts = gTTS(text, lang=language)
        tts.write_to_fp(mp3_fo)
        pygame.mixer.music.load(mp3_fo, 'mp3')
        pygame.mixer.music.play()
        # return mp3_fo

# Load data for airports
airports_data = loadDataModel(True)
print("----New Metar data loaded-----")

# Load model and read "pilot" speech 
model = whisper.load_model("base")
fs = 44100  # this is the frequency sampling; also: 4999, 64000
pygame.init()
pygame.mixer.init()
while True:
    response = "Say again please, i did not understand well enough"
    pilotUtterance = ""

    seconds = 13  # Duration of recording
    input("Welcome: Please press Enter to start recording a pilot request (max 13 seconds.) ")
    print("recording....")
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    print("record finished")
    write('output.wav', fs, myrecording)  # Save as WAV file
    #os.startfile("output.wav")
    sound = AudioSegment.from_wav('output.wav')
    #transform to mp3
    sound.export('myfile.mp3', format='mp3')

    #result = model.transcribe("KBNA-App-Dep-West-Final-Oct-18-2022-1230Z.mp3")
    result = model.transcribe("myfile.mp3", fp16=False, language='English')
    pilotUtterance = result["text"]
    pilotUtterance = pilotUtterance.strip(",")
    
    # check if the utterance holds keywords

    qnhCommand = 0
    metarCommand = 0
    runwayVisualCommand = 0
    weatherCommand = 0
    visabilityCommand = 0
    locationFound = 0
    surecommand = 0
    lastWords = 0
    

    # first check if we identify a command and then check if we understand the location
    if check_string(pilotUtterance, "Q&H") or check_string(pilotUtterance, "Q and H") or check_string(pilotUtterance, "QNH") or check_string(pilotUtterance, "Q&A"):

        qnhCommand = 1
    
    if check_string(pilotUtterance, "metar") or check_string(pilotUtterance, "medar") or  check_string(pilotUtterance, "meter") or check_string(pilotUtterance, "meta"):
        metarCommand = 1

    if check_string(pilotUtterance,"runway") and check_string(pilotUtterance,"visual"):
        runwayVisualCommand = 1

    if check_string(pilotUtterance,"visibility"):
        visabilityCommand = 1
    
    if check_string(pilotUtterance,"weather"):
        weatherCommand = 1

    if check_string(pilotUtterance,"last words"):
        lastWords = 1
    if check_string(pilotUtterance,"not sure"):
        surecommand = 1
    
    # we have identified a command so lets find the location
    if qnhCommand or metarCommand or runwayVisualCommand or weatherCommand or visabilityCommand:
    
        if find_nato(pilotUtterance):
            icaoAirport = create_acronymOfFourWords(find_nato(pilotUtterance))
            callsign = extractCallsign(pilotUtterance)
            if icaoAirport in airports_data:
                natoAirport = ' '.join(find_nato(pilotUtterance))
                
                if qnhCommand:
                    qnhValue = getQNH(airports_data,icaoAirport)
                    response = str(callsign + ", QNH at " + str(natoAirport) + " is ," + str(qnhValue) + " hectopascal")
                elif metarCommand:
                    response = str(callsign + ", Metar at " + natoAirport + " is " + (airports_data[icaoAirport].string()))

                elif weatherCommand:
                    weather_description = getWeather(airports_data,icaoAirport)
                    response = str(callsign + ", Weather at " + natoAirport + " is " + str(weather_description))
                elif visabilityCommand:
                    weather = getVisibility(airports_data,icaoAirport)
                    response = str(callsign + ", Weather at " + natoAirport + " is " + (airports_data[icaoAirport].string()))
                elif runwayVisualCommand:
                    runwayVisual = getRunwayVisualRange(airports_data,icaoAirport)
                    response = str(callsign + ", runway visual range " + natoAirport + " is " + str(runwayVisual))
                else:
                    response = "Say again please"

            
            else:
                print("")
    if lastWords:
        response = "YesThank you Birgir and Pawel, its also been a lovely experience working with you. I was nervous that this demo would be all fucked up... it wasnt ... anyway... you are probably the nicest people i have ever had the pleasure to work with... the smartest. you are a prime example of humans...i hope that we can meet one day and really have a good time.... maybe have some wine and cheese maybe ?... what do you think?"
    if surecommand:
        response = "Well cheese and wine later... until next time... All the best to the great innovative developers at Tern Systems.... We used Google text to speech for voice synthesis... the OpenAI whisper speech recognition library... and a bunch of other python libraries, ho ho ho ho ho ho ho ho ho ho ho ho hoMerry Christmas"
    
    print("================================")    
    print("Transcribed speech: " + pilotUtterance)
    print("Response: " + response)
    speak(response)
    print("================================")    
    
    # Create a gTTS object with the text to synthesize
    #tts = gTTS(response)
    #print(pilotUtterance)
    # Save the synthesized audio to a file
    #tts.save("response.mp3")
    #playsound("response.mp3")
    




    
