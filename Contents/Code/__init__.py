################################################################################
# Python Imports
################################################################################
import re

################################################################################
# Global variables for channel
################################################################################
TITLE                           = "SportseBooks"
PREFIX                          = "/video/sportsebooks"

ART                             = "art-default.png"
ICON                            = "icon-default.png"

# Below values lifted from FilmOn plugin
USER_AGENT                      = 'Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5376e Safari/8536.25'
REFERER                         = "http://www.sportsebooks.eu/"
CUSTOM_HEADERS                  = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                                    'Accept-Encoding': 'gzip,deflate,sdch',
                                    'Accept-Language': 'en-US,en;q=0.8,es;q=0.6',
                                    'Cache-Control': 'max-age=0',
                                    'Connection': 'keep-alive'}

URL_BASE                        = "http://www.sportsebooks.eu/"
URL_LOGIN                       = "amember/login"
URL_MEMBERS                     = "membersarea/"
URL_CHANNELMENU                 = "channelmenuios.html"

# Global variable for channels
CHANNEL_LIST                    = []

################################################################################
# Initialise the channel
################################################################################
def Start(): 
    # Set header and referer
    HTTP.Headers["User-agent"]  = USER_AGENT
    HTTP.Headers["Referer"]     = REFERER
       
    # Set title and art
    ObjectContainer.title1      = TITLE
    ObjectContainer.art         = R(ART)
    
################################################################################
# Build the main menu
################################################################################  
@handler(PREFIX, TITLE, thumb = ICON, art = ART)

def MainMenu():    
    # Log the user in initially
    AuthenticateUser()
    
    # Test to see if user is logged in
    if "Login" in Dict:
        # Open and ObjectContainer for the main menu
        MAIN_MENU                   = ObjectContainer()

        # Get Channel list
        CHANNEL_LIST                = GetChannelList()
    
        # Loop through each channel to produce an EpisodeObject
        for CHANNEL in CHANNEL_LIST:
            TITLE                   = CHANNEL[0]
            URL                = CHANNEL[1]

            # Passes off to URL service to get channel episode object to add to menu
            MAIN_MENU.add(
                CreateChannelEpisodeObject(
                    TITLE,
                    URL
                )
            )

        # Add the preferences object
        MAIN_MENU.add(
            PrefsObject(
                title               = "Preferences",
                thumb               = R("icon-preferences.png"),
                summary             = "Enter your username and password\r\nThe plugin will not work without them"
            )
        )
    
        return MAIN_MENU
    else:
        # Get not logged in alert
        ERROR_MESSAGE           = ErrorNotLoggedIn()
        
        return ERROR_MESSAGE
 
################################################################################
# Validate users preferences (username and password)
################################################################################  
def ValidatePrefs(): 
    # Reset the dictionary that contains the login status
    Dict.Reset()
       
    # Test for username AND password
    if Prefs["username"] and Prefs["password"]:
        # If both are present, authenticate the user
        AuthenticateUser()
        
        # Shows message based on authentication attempt
        if "Login" in Dict:
            # Successful login
            ALERT               = SuccessLoggedIn()
        else:
            # Incorrect username or password error
            ALERT               = ErrorIncorrectLogin()
    else:
        # Missing username or password error
        ALERT                   = ErrorMissingLogin()
    
    return ALERT
 
################################################################################
# Gets a list of channels to iterate over
################################################################################   
def GetChannelList():
    # Check to see if CHANNEL_LIST is already populated, if yes return it, if
    # no construct it.
    if CHANNEL_LIST:
        return CHANNEL_LIST
    else:
        # Gets the HTML source from the iOS Channel Menu
        HTML_URL                    = URL_BASE + URL_MEMBERS + URL_CHANNELMENU
    
        HTML_SOURCE                 = HTML.ElementFromURL(HTML_URL, headers = CUSTOM_HEADERS)  
    
        # Find the channel links in the HTML source with xpath
        CHANNELS                    = HTML_SOURCE.xpath("//a")
    
        # Remove the last element from the list
        CHANNELS.pop()
    
        # Add each channel's text to CHANNEL_LIST
        for CHANNEL in CHANNELS:
            # Grab the link text, and convert from list to string
            # N.B. xpath ALWAYS returns a list
            CHANNEL_NAME            = "".join(CHANNEL.xpath(".//text()"))
            CHANNEL_URL             = URL_BASE + URL_MEMBERS + "".join(CHANNEL.xpath(".//@href"))
            
            # Grab the source from the Channel's URL – done inside here so we
            # only do it once, not every time we hit the main menu
            CHANNEL_SOURCE          = HTML.ElementFromURL(CHANNEL_URL, headers = CUSTOM_HEADERS)
        
            # Gets the relevant script that has the mediaplayer info in it, by using
            # xPath to search for a script containing the string 'mediaplayer'
            CHANNEL_SCRIPT            = CHANNEL_SOURCE.xpath("//script[contains(., 'mediaplayer')]//text()")[0]
    
            # Grabs the video URL via regex
            CHANNEL_VIDEO           = re.findall(r'(http:\/\/[\d].*)\'',CHANNEL_SCRIPT)[0]
        
            # Appends the channel details to the CHANNEL_LIST
            CHANNEL_LIST.append([CHANNEL_NAME,CHANNEL_VIDEO])        
    
        return CHANNEL_LIST
 
 
 
################################################################################
# Return Episode Object for Channel
################################################################################ 
def CreateChannelEpisodeObject(TITLE,URL,INCLUDE_CONTAINER=False): 
    # Creates a VideoClipObject, with the key being a callback, unsure why, but
    # this re-calling of the same function is necessary to get an object that
    # will play without a URL service.
    #
    # N.B. HTTPLiveStreamURL automatically sets video_codec, audio_codec and 
    # protocol. Adding them back in causes the stream not to work on other
    # devices that are not Chrome and PHT
    CHANNEL_OBJECT              = VideoClipObject(
        key                     = Callback(
            CreateChannelEpisodeObject,
            TITLE               = TITLE,
            URL                 = URL,
            INCLUDE_CONTAINER   = True
        ),
        rating_key              = TITLE,
        title                   = TITLE,
        items                   = [
            MediaObject(
                video_resolution        = 360,
                audio_channels          = 2,
                optimized_for_streaming = True,
                height                  = 360,
                width                   = 640,
                parts                   =   [
                    PartObject(
                        key             = HTTPLiveStreamURL(
                            url         = URL  
                        )
                    )
                ]
            )
        ]
    )
    
    if INCLUDE_CONTAINER:
        return ObjectContainer(
            objects               = [CHANNEL_OBJECT]
        )
    else:
        return CHANNEL_OBJECT 
   
################################################################################
# Authenticate the user
################################################################################        
def AuthenticateUser():
    # Create the login URL
    LOGIN_URL                   = URL_BASE + URL_LOGIN
    
    # Set the post data
    POST_DATA                   = {
        "amember_login": Prefs["username"],
        "amember_pass": Prefs["password"]
    }
    
    # Grab the HTTP response to login attempt
    CONTENT                     = HTTP.Request(url = LOGIN_URL, values = POST_DATA).content
    
    # Test to see if there's a login error message
    if 'am-login-errors' in CONTENT:
        # Sets Dict["Login"] to False on unsuccessful login attempt
        Dict["Login"]           = False
        
        return False
    else:
        # Sets Dict["Login"] to True on successful login attempt
        Dict["Login"]           = True
        
        return True
    
################################################################################
# Alerts and error messages
################################################################################ 
# If successful login
def SuccessLoggedIn():
    return ObjectContainer(
        header                  = "Success",
        message                 = "You're now logged in"
    )

# If user tries to access submenus without logging in
def ErrorNotLoggedIn():
    return ObjectContainer(
         header                 = "You're not logged in",
         message                = "You need to be logged in to view streams"       
    )
    
# If login error
def ErrorIncorrectLogin():
    return ObjectContainer(
        header                  = "Something went wrong",
        message                 = "Your username and/or password are incorrect"
    )

# If one or both of username or password are missing
def ErrorMissingLogin():
    return ObjectContainer(
        header                  = "Something's missing",
        message                 = "Your username and/or password is missing"
    )