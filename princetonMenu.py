#!/usr/bin/env python
# -*- coding:utf-8 -*-
from html.parser import HTMLParser
import urllib.request
import urllib.parse
from fuzzywuzzy import fuzz
import re
baseURL = r"https://menus.princeton.edu/dining/_Foodpro/online-menu/"
detailURL = baseURL + r"menuDetails.asp?locationNum=%s"


def getDiningHall():
    """Get Dining Hall information from baseURL"""
    pattern = re.compile(r"""href="menuDetails\.asp\?sName=[^&]+"""
                         + r"""&locationNum=(\d+)&locationName=([^&]+)&naFlag=.""")
    PUDining = urllib.request.urlopen(baseURL)
    diningDict = {}
    for num, loc in pattern.findall(PUDining.read().decode()):
        diningDict[num] = urllib.parse.unquote_plus(loc).strip()
    return diningDict


class MenuParser(HTMLParser):
    """Parse menu infos from a menuDetails page"""
    def __init__(self):
        super(MenuParser, self).__init__()
        self.inMealCard = False
        self.currentItem = ""
        self.currentMeal = {}
        self.currentGroup = {}
        self.menu = {}
        self.divLevel = 0

    def handle_starttag(self, tag, attrs):
        if not self.inMealCard:
            # Looking for mealCard
            if tag == "div" and ("class", "card mealCard") in attrs:
                self.inMealCard = True
        elif tag == "div":
            # Counting div level within a mealcard
            self.divLevel += 1
        elif tag == "h5" and ("class", "mealName") in attrs:
            # get mealName
            self.currentItem = "meal"
        elif tag == "li" and ("class", "list-group-item") in attrs:
            self.currentItem = "group"
        elif tag == "li" and ("class", "recipe") in attrs: 
            self.currentItem = "recipe"

    def handle_endtag(self, tag):
        if self.inMealCard:
            if tag == "div":
                if self.divLevel == 0:
                    # Exiting mealCard
                    self.inMealCard = False
                else: 
                    self.divLevel -= 1
            elif tag == "h5" and self.currentItem == "meal":
                self.currentItem = ""
            elif tag == "li":
                if self.currentItem == "recipe":
                    self.currentItem = "group"

    def setMeal(self, mealName):
        if not mealName in self.menu:
            self.menu[mealName] = {}
        self.currentMeal = self.menu[mealName]

    def setGroup(self, groupName):
        groupName = re.match(r"\s*-- (.*) --", groupName)
        if groupName:
            groupName = groupName.group(1)
            if not groupName in self.currentMeal:
                self.currentMeal[groupName] = []
            self.currentGroup = self.currentMeal[groupName]

    def setRecipe(self, recipeName): 
        self.currentGroup.append(recipeName)

    def handle_data(self, data):
        handler = {"meal": self.setMeal, "group": self.setGroup,
                   "recipe": self.setRecipe}
        if self.currentItem in handler:
            handler[self.currentItem](data)

def AllPUDining():
    totalMenu = {}

    for num, loc in getDiningHall().items():
        url = detailURL % num
        # print(url, loc)
        menu = urllib.request.urlopen(url)
        menuparser = MenuParser()
        menuparser.feed(menu.read().decode("ISO-8859-1"))
        totalMenu[loc] = menuparser.menu

    return totalMenu

def GetInterest(hallMenu, interestList):
    if isinstance(interestList, str):
        interestList = [interestList]
    matchRes = []
    for meal in hallMenu:
        for group in hallMenu[meal]:
            for items in hallMenu[meal][group]:
                for interest in interestList:
                    # print("compare", items, interest, fuzz.partial_ratio(items.lower(), interest.lower()))
                    if fuzz.partial_ratio(items.lower(), interest.lower()) > 85:
                        matchRes.append(meal)
                        break
                if matchRes and matchRes[-1] == meal:
                    break
            if matchRes and matchRes[-1] == meal:
                break
    return matchRes


if __name__ == '__main__':
    import pprint
    pp = pprint.PrettyPrinter(indent=2, width=200, compact=True)
    totalMenu = AllPUDining()
    pp.pprint(totalMenu)
    print(GetInterest(totalMenu["EQuad Cafe"], "lobster"))

# vim: ts=4 sw=4 sts=4 expandtab