#!/usr/bin/env python
#a telegram bot that gets the luas times for a given stop
#makes use of the api at https://github.com/ncremins/luas-api

import logging
import telegram
from time import sleep
import urllib2
import json
try:
    from urllib.error import URLError
except ImportError:
    from urllib2 import URLError  # python 2

station_names_green = {}

def main():
    # Telegram Bot Authorization Token
    BOT_TOKEN = open('../luas_bot_token.txt').read()
    bot = telegram.Bot(BOT_TOKEN)

  
    #populate a list with all the station names
    global station_names_green    
    json_response = urllib2.urlopen("http://luas.neilcremins.com/index.php?action=stations").read()
    parsed_json = json.loads(json_response)
    for station in parsed_json['stations']:
        if station['line'] == 'Green':
            station_names_green[(str(station['displayName'])).upper().replace(" ", "").replace(".","").replace("'","")] = [(str(station['displayName'])),(str(station['shortName']))]
    
    # get the first pending update_id, this is so we can skip over it in case
    # we get an "Unauthorized" exception.
    try:
        update_id = bot.getUpdates()[0].update_id
    except IndexError:
        update_id = None

    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    while True:
        try:
            update_id = getTimes(bot, update_id)
        except telegram.TelegramError as e:
            # These are network problems with Telegram.
            if e.message in ("Bad Gateway", "Timed out"):
                sleep(1)
            elif e.message == "Unauthorized":
                # The user has removed or blocked the bot.
                update_id += 1
            else:
                raise e
        except URLError as e:
            # These are network problems on our end.
            sleep(1)


def getTimes(bot, update_id):
    # Request updates after the last update_id
    global station_names_green

    for update in bot.getUpdates(offset=update_id, timeout=10):
        # chat_id is required to reply to any message
        chat_id = update.message.chat_id
        update_id = update.update_id + 1
        message = update.message

        if message and message != "":
            if message.text:
                if message.text == "/listGreen":
                    reply = ''
                    for station in station_names_green:
                        reply+= '{}\n'.format(str(station).title())
                    bot.sendMessage(chat_id=chat_id, text=reply)
                
                elif message.text[1:len(message.text)].upper().replace(" ","").replace(".","").replace("'","") in station_names_green:
                    short_name = station_names_green[message.text[1:len(message.text)].upper().replace(" ","")][1]
                    try:
                        url = "http://luas.neilcremins.com/index.php?action=times&station={}".format(short_name)
                        json_response = urllib2.urlopen(url).read() #get full list of stations and info
                        parsed_json = json.loads(json_response)
                        reply = ''
                        if parsed_json['message'] == 'All services operating normally': #check the api is working correctly
                            if parsed_json['trams']:
                                destination_times = {"St. Stephen's Green":[],'Brides Glen':[],'Sandyford':[]}
                                for times in parsed_json['trams']:
                                    destination_times[times['destination']].append(times['dueMinutes'])
                                print destination_times
                                for destination in destination_times:
                                    if destination_times[destination]:
                                        reply += "\n\n{0}:\n".format(destination)
                                        for time in destination_times[destination]:
                                            if time == "DUE":
                                                reply += "{0}\n".format(time)
                                            else:
                                                reply += "{0} Mins\n".format(time)
                            else : 
                                reply = 'Sorry there was an error please try again'
                        else:
                            reply = parsed_json['message']
                        bot.sendMessage(chat_id=chat_id, text=reply)
                    except URLError as e:
                        print "error: {}".format(e)


    return update_id

if __name__ == '__main__':
    main()
