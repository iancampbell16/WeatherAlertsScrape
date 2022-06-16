from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
# import time
import sys


def ScrapeAlerts(driver, action, state, county=''):

    def findState():
        """
        returns list of 2 elements, the first is the element containing the name
        of the state, and the second is the container of the first element which
        may be used to find the County List element for the state
        """
        StatesTags = driver.find_elements(
            By.XPATH, '/html/body/table[4]/tbody/tr[1]/td[2]/table/tbody/tr[3]/td/table[2]/tbody[2]/tr')
        for stateTag in StatesTags:
            stateNameTag = stateTag.find_element(
                By.XPATH, './td[1]/a[not(@id)]')
            if stateNameTag.text == state:
                StateTagToClick = stateTag.find_element(By.XPATH, './td[1]')
                break
        return [stateNameTag, StateTagToClick]

    def ScrollandClick(element):
        """
        used to scroll the screen to an element and then click on it
        """
        driver.execute_script(
            "arguments[0].scrollIntoView()", element)
        action.move_to_element(element).click().perform()

    def makeWarningList():
        """
        find the table of warnings and return a list of its elements.
        used repeatedly when retrieving information about warnings in CA
        """
        warningTable = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, '/html/body/table/tbody/tr/td[2]/table[1]/tbody/tr/td[2]/table[2]/tbody'))
        )
        return warningTable.find_elements(By.TAG_NAME, 'a')

    try:
        # Find the td tag representing the correct state
        stateNameTag, StateTagToClick = findState()

        # navigate to item that links to warning page (warnClick)
        if county:
            # find out if there is a 'County List' link
            countyListBool = False
            lastATag = StateTagToClick.find_elements(By.XPATH, './a')[-1]
            if lastATag.text == 'County List':
                countyListBool = True

            # if countyListBool is false set warnClick (click which will lead to warning page) to stateNameTag
            if not countyListBool:
                warnClick = stateNameTag

            # if countyListBool is true click on the tag and look for county
            if countyListBool:
                ScrollandClick(lastATag)

                # find tbody in which the counties are contained and make list of rows
                countiesList = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '/html/body/table[4]/tbody/tr/td[2]/table/tbody/tr[1]/td/table/tbody'))
                )
                countiesListRows = countiesList.find_elements(
                    By.XPATH, './tr')[2:]   # remove first 2 rows for the header

                # check if input county matches any county on the list
                countyMatch = False
                for countyListRow in countiesListRows:
                    countyNameElement = countyListRow.find_elements(
                        By.TAG_NAME, 'td')[-1]
                    if countyNameElement.text == county:
                        countyMatch = True
                        break

                # if county is in list then set warnClick to countyNameElement
                if countyMatch:
                    countyCodeElement = countyListRow.find_elements(
                        By.TAG_NAME, 'a')[-1]
                    warnClick = countyCodeElement

                # if county not on list return to previous page and set warnClick to stateNameTag
                else:
                    driver.back()
                    warnClick = findState()[0]

        # In case with no county then stateNameTag is what we want to click
        else:
            warnClick = stateNameTag

        # scroll down to and click on warnClick
        ScrollandClick(warnClick)

        # get info from each warning in the table and make list of warnings
        warningList = makeWarningList()
        warnings = []

        # # This only works for the format in CA
        # for index in range(len(warningList)):
        #     ScrollandClick(warningList[index])
        #     description = WebDriverWait(driver, 10).until(
        #         EC.presence_of_element_located(
        #             (By.XPATH, '/html/body/div[3]/table[1]/tbody/tr/td[2]/table/tbody/tr[5]/td/table/tbody/tr[2]/td[2]/pre'))
        #     )
        #     descriptionText = description.text.split('* ')[1:]
        #     warninginfo = {}
        #     for element in descriptionText:
        #         key, value = element.split('...')
        #         warninginfo[key] = value.replace('\n', '')
        #     warnings.append(warninginfo)
        #     driver.back()
        #     warningList = makeWarningList()

        for warning in warningList:
            warningDict = {}
            warningInfo = warning.text.split('\n')
            warningDict['Reason'] = warningInfo[0]
            warningDict['Issued'] = warningInfo[1].split(': ')[1]
            if len(warningInfo) > 2:
                warningDict['Expiring'] = warningInfo[2].split(': ')[1]
            warnings.append(warningDict)

        return warnings

    except Exception:
        print('Error: ', *sys.exc_info(), sep='\n')


if __name__ == '__main__':

    PATH = "/Users/iancampbell/Documents/WebDriver/chromedriver"
    s = Service(PATH)
    options = Options()
    options.headless = True
    driver = webdriver.Chrome(service=s, options=options)

    url = "https://alerts.weather.gov/"
    driver.get(url)

    action = ActionChains(driver)

    # to allow you to run from terminal in form `python3 WeatherAlertsScrape.py state county` (if either input is multiple words put in quotes)
    if len(sys.argv) == 1:
        state = 'California'
        county = 'Mono'
    elif len(sys.argv) == 2:
        state = sys.argv[1]
        county = ''
    elif len(sys.argv) == 3:
        state, county = sys.argv[1:]

    print(*ScrapeAlerts(driver, action, state, county), sep='\n\n')

    driver.quit()
