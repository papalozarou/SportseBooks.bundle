################################################################################
# Python Imports
################################################################################
# This is only used to find the HLS video URL within the script on each channel
# page 
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

# URLs for sportsebooks.eu site
URL_BASE                        = REFERER
URL_LOGIN                       = "amember/login"
URL_MEMBERS                     = "membersarea/"
URL_CHANNELMENU                 = "channelmenuios.html"

# Global variable for channels
CHANNEL_LIST                    = []

# THIS IS ONLY USED FOR LOGGING – DELETE
STARS                           = "************"

################################################################################
# Initialise the channel
################################################################################
def Start():
    # Set title and art
    ObjectContainer.title1      = TITLE
    ObjectContainer.art         = R(ART)

    # Delete the dictionary that contains the login status
    ClearLoginStatus()
    
    # Set header for all HTTP requests
    #
    # N.B. We set referer as videos are hosted on another domain
    HTTP.Headers["User-agent"]  = USER_AGENT
    HTTP.Headers["Referer"]     = REFERER
    
################################################################################
# Clear the login status
################################################################################
def ClearLoginStatus():
    if "Login" in Dict:
        del Dict["Login"]

    return None
    
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

################################################################################
# Validate users preferences (username and password)
################################################################################
def ValidatePrefs():
    # Tests for username and password
    if Prefs["username"] and Prefs["password"]:
        # If both are present, authenticate the user
        AUTHENTICATE            = AuthenticateUser()
        
        # Shows message based on authentication attempt
        if AUTHENTICATE is True:
            # Successful login
            ALERT               = SuccessLoggedIn()
            
        else:
            # Incorrect username or password error
            ALERT               = ErrorIncorrectLogin()
    
    else:
        # Missing username or password
        ALERT                   = ErrorMissingLogin()
        
    return ALERT

################################################################################
#  Authenticate the user
################################################################################
def AuthenticateUser():
    # Construct login URL
    LOGIN_URL                   = URL_BASE + URL_LOGIN

    # Page titles when user is logged in (LOGIN_SUCCESS_TITLE) or at login page
    # (LOGIN_FAILURE_TITLE), regardless of errors
    LOGIN_SUCCESS_TITLE         = "Sportsebooks"
    LOGIN_FAILURE_TITLE         = "Please login"

    # Set the POST data to users login details
    POST_DATA                   = {
        "amember_login": Prefs["username"],
        "amember_pass": Prefs["password"]
    }

    # Grab the HTTP response to login attempt
    LOGIN_RESPONSE_CONTENT      = HTML.ElementFromURL(url = LOGIN_URL, values = POST_DATA)

    # Get the title string from the returned response
    LOGIN_RESPONSE_TITLE        = "".join(LOGIN_RESPONSE_CONTENT.xpath("//title/text()"))

    # Test to see if we've successfully logged in
    if LOGIN_RESPONSE_TITLE == LOGIN_SUCCESS_TITLE:
        Log(STARS + " LOGGED IN " + STARS)
        # If TITLE of returned page matches success title of pageset Dict["Login"] to True
        Dict["Login"]           = True

        # Save the dictionary immediately
        Dict.Save()

        return True
    else:
        Log(STARS + " NOT LOGGED IN " + STARS)
        # If we find the word errors within CONTENT, or CONTENT returns null, we
        # return false
        return False
 
################################################################################
# Gets a list of channels to iterate over
################################################################################
def GetChannelList():
    # Check to see if CHANNEL_LIST is already populated, if yes return it, if
    # no construct it.
    if CHANNEL_LIST:
        return CHANNEL_LIST
    else:
        # Construct CHANNEL_LIST_URL and grab HTML
        CHANNEL_LIST_URL        = URL_BASE + URL_MEMBERS + URL_CHANNELMENU        
        CHANNEL_LIST_SOURCE     = HTML.ElementFromURL(CHANNEL_LIST_URL)
        
        # Find the channel links in the HTML source with xPath
        CHANNELS                = CHANNEL_LIST_SOURCE.xpath("//p/a")
    
        # Remove the last link from the CHANNELS list (the 'Return
        # to desktop version' links)
        CHANNELS.pop()

        # Add each channel to CHANNEL_LIST
        for CHANNEL in CHANNELS:
            # Grab the link text and convert from list to string
            # N.B. xpath ALWAYS returns a list
            CHANNEL_TITLE       = "".join(CHANNEL.xpath(".//text()"))
            CHANNEL_URL         = URL_BASE + URL_MEMBERS + "".join(CHANNEL.xpath(".//@href"))
    
            # Gets the correct channel thumbnail
            CHANNEL_THUMB       = GetChannelThumb(CHANNEL_TITLE)
    
            # Appends the channel details to the CHANNEL_LIST
            CHANNEL_LIST.append([CHANNEL_TITLE,CHANNEL_URL,CHANNEL_THUMB])
            
            Log(CHANNEL_TITLE)
            Log(CHANNEL_URL)
        
        CHANNEL_LIST.sort()
        
        return CHANNEL_LIST

################################################################################
# Extracts the actual video URL for a channel
################################################################################
def GetChannelVideoStreamURL(URL):
    # # Log user in as we can't access stream URLs without doing this again
    AUTHENTICATE            = AuthenticateUser()

    if AUTHENTICATE is True:
        # Grab the source from the Channel's URL – done inside here so we
        # only do it once, not every time we hit the main menu
        CHANNEL_SOURCE          = HTML.ElementFromURL(URL)

        # Gets the relevant script that has the mediaplayer info in it, by using
        # xPath to search for a script containing the string 'mediaplayer'
        CHANNEL_SCRIPT          = CHANNEL_SOURCE.xpath("//script[contains(., 'mediaplayer')]//text()")[0]

        # Grabs the video URL via regex
        CHANNEL_VIDEO           = re.findall(r'(http:\/\/[\d].*)\'',CHANNEL_SCRIPT)[0]
    
        return CHANNEL_VIDEO
    else:
        # Incorrect username or password error
        ERROR_MESSAGE       = ErrorIncorrectLogin()

        return ERROR_MESSAGE

################################################################################
# Gets the correct thumb for the channel based on TITLE variable
################################################################################
def GetChannelThumb(TITLE):
    # check the TITLE variable and act accordingly
    if TITLE.startswith("At"):
        THUMB                   = "at-the-races.png"
        
    elif TITLE.startswith("BT"):
        THUMB                   = "bt-sport.png"
    
    elif TITLE.startswith("Racing"):
        THUMB                   = "racing-uk.png"
    
    elif TITLE.startswith("Sky"):
        THUMB                   = "sky-sports.png"
    
    elif TITLE.startswith("bein"):
        THUMB                   = "bein-sports.png"
        
    else:
        THUMB                   = ICON
    
    return THUMB    
    
################################################################################
# Return Episode Object for Channel
################################################################################ 
def CreateChannelEpisodeObject(TITLE,URL,THUMB,INCLUDE_CONTAINER=False): 
    # Creates a VideoClipObject, with the key being a callback, unsure why, but
    # this re-calling of the same function is necessary to get an object that
    # will play without a URL service.
    #
    # Using an @indirect for the video so that it's only asked for when the user
    # decides to play that particular channel.
    #
    # N.B. HTTPLiveStreamURL automatically sets video_codec, audio_codec and 
    # protocol. Adding them back in causes the stream not to work on other
    # devices that are not Chrome and PHT
    CHANNEL_OBJECT              = VideoClipObject(
        key                     = Callback(
            CreateChannelEpisodeObject,
            TITLE               = TITLE,
            URL                 = URL,
            THUMB               = THUMB,
            INCLUDE_CONTAINER   = True
        ),
        rating_key              = TITLE,
        title                   = TITLE,
        thumb                   = R(THUMB),
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
                            Callback(
                                PlayChannelVideo,
                                URL     = URL
                            ) 
                        )
                    )
                ]
            )
        ]
    )
    
    if INCLUDE_CONTAINER:
        return ObjectContainer(
            objects             = [CHANNEL_OBJECT]
        )
    else:
        return CHANNEL_OBJECT 

################################################################################
# Gets the actual HLS stream URL and plays the media – used so that we only
# ask for the URL when the user is ready to play the video
################################################################################
@indirect
def PlayChannelVideo(URL):
    CHANNEL_VIDEO_URL           = GetChannelVideoStreamURL(URL)
    
    return IndirectResponse(
        VideoClipObject,
        key = HTTPLiveStreamURL(
            url                 = CHANNEL_VIDEO_URL
        )
    )   
    
################################################################################
# Build the main menu
################################################################################ 
@handler(PREFIX, TITLE, thumb = ICON, art = ART)

def MainMenu():
    # Check to see if the user is logged in or not, if they are build the main
    # menu options, if not try to authenticate or show an error
    if "Login" in Dict:
        # Open an ObjectContainer for the main menu
        MAIN_MENU               = ObjectContainer()
    
        # Gets the channel list
        CHANNELS                = GetChannelList()

        # Loop through each channel to produce an EpisodeObject
        for CHANNEL in CHANNELS:
            # Creates an EpisodeObject and adds it to the Main Menu
            MAIN_MENU.add(
                CreateChannelEpisodeObject(
                    TITLE       = CHANNEL[0],
                    URL         = CHANNEL[1],
                    THUMB       = CHANNEL[2]
                )
            )
        
        # Add the preferences object
        MAIN_MENU.add(
            PrefsObject(
                title           = "Preferences",
                thumb           = R("icon-preferences.png"),
                summary         = "Enter your username and password\r\nThe plugin will not work without them"
            )
        )
        
        return MAIN_MENU
        
    else:
        # Log the user in initially
        AUTHENTICATE            = AuthenticateUser()
        
        if AUTHENTICATE is True:
            # Return the main menu
            MENU                = MainMenu()
            
            return MENU
        else:
            # Incorrect username or password error
            ERROR_MESSAGE       = ErrorIncorrectLogin()
            
            return ERROR_MESSAGE