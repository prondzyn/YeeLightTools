#!/usr/bin/env python3

import argparse, sys
import requests
from bs4 import BeautifulSoup
import tempfile
import os
from yeelight import Bulb, BulbException, PowerMode

WEBSITE_URL_TEMPLATE = "https://www.bankier.pl/inwestowanie/profile/quote.html?symbol=%s"
DB_FILE_NAME_TEMPLATE = "YeeLightGPW.%s.data"

def main(args):
  bulb = Bulb(args.BULB_IP)
  stockSymbol = args.STOCK_SYMBOL
  lighterModeFactor = 50 if args.lighter_mode else 0
  previousPrice = getPreviousPrice(stockSymbol)
  currentPrice = getCurrentPrice(stockSymbol)
  if previousPrice != currentPrice:
    setBulbColor(bulb, previousPrice, currentPrice, lighterModeFactor)
    storeCurrentPrice(stockSymbol, currentPrice)
  else:
    bulb.set_power_mode(PowerMode.NORMAL)

def getDb(stockSymbol):
  tempDir = tempfile.gettempdir()
  return os.path.join(tempDir, DB_FILE_NAME_TEMPLATE % stockSymbol)

def getPreviousPrice(stockSymbol):
  db = getDb(stockSymbol)
  if os.path.exists(db):
    dbContent = open(db, "r")
    return float(dbContent.readlines()[-1])
  else:
    return 0.0

def getCurrentPrice(stockSymbol):
  response = requests.get(WEBSITE_URL_TEMPLATE % stockSymbol)
  response.encoding = "utf-8"
  if response.status_code != 200:
    sys.exit("error: cannot find current price of %s" % stockSymbol)
  soup = BeautifulSoup(response.text, "html.parser")
  return float(soup.findAll("div", attrs={"class": "profilLast"})[0].string.rstrip(" zł").replace(",", "."))

def setBulbColor(bulb, previousPrice, currentPrice, lighterModeFactor):
  goingUp = previousPrice < currentPrice
  try:
    if goingUp:
      bulb.set_rgb(lighterModeFactor, 255, lighterModeFactor)
    else:
      bulb.set_rgb(255, lighterModeFactor, lighterModeFactor)
  except BulbException as ex:
    print(ex)
    pass

def storeCurrentPrice(stockSymbol, currentPrice):
  dbContent = open(getDb(stockSymbol), "a")
  dbContent.write(str(currentPrice) + "\n")
  dbContent.close()

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Sets YeeLight bulb color based on GPW stock value change.")
  parser.add_argument("BULB_IP", help="a bulb IP address")
  parser.add_argument("STOCK_SYMBOL", help="a GPW stock symbol name")
  parser.add_argument("-l", "--lighter-mode", help="a lighter mode of the colors", action="store_true")
  args = parser.parse_args()
  main(args)
