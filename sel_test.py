import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotVisibleException, NoSuchElementException

# from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib import parse

import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.concurrent

from threading import Thread
from functools import wraps

urlparse = parse

PORT = 777

# async wrapper
def run_async(func):

    @wraps(func)
    def async_func(*args, **kwargs):
        func_h1 = Thread(target = func, args = args, kwargs = kwargs)
        func_h1.start()
        return func_h1

    return async_func

# make custom Handler
class requestHandler(tornado.web.RequestHandler):

    # GET
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):

        #headers
        self.add_header('Content-type','application/json')

        # get GET params
        departure = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('dep', ["BDO"])[0]
        arrival = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('arr', ["DPS"])[0]
        depDate = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('date', ["19-07-2017"])[0]
        retDate = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('return', ["NA"])[0]
        adults = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('adults', [1])[0]
        children = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('children', [0])[0]
        infant = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('infant', [0])[0]
        fclass = urlparse.parse_qs(urlparse.urlparse(self.request.uri).query).get('class', ["ECONOMY"])[0]

        # send message
        # message = yield tornado.gen.Task( lookup(driver, departure, arrival, depDate, "NA", adults, children, infant, fclass) )
        message = yield tornado.gen.Task( lookup, departure, arrival, depDate, "NA", adults, children, infant, fclass )
        self.write(bytes(message, "utf8"))

        return

def init_driver():
    driver = webdriver.Chrome()
    driver.wait = WebDriverWait(driver, 0)
    return driver
 



@run_async
def lookup(dep, arr, dd, rd, ad, ch, inf, fcls, callback):
        
    driver = init_driver()
    theURL = "https://www.traveloka.com/fullsearch?ap=" + str(dep) + "." + str(arr) + "&dt=" + str(dd) + "." + str(rd) + "&ps=" + str(ad) + "." + str(ch) + "." + str(inf) + "&sc=" + str(fcls) + ""
    print("Fetching from: ", theURL)
    driver.get(theURL)

    stillLoading = True

    while stillLoading:
        try:
            loadingInfo = driver.find_element_by_id("loadingInfo")
            time.sleep(5)

        except NoSuchElementException:
            stillLoading = False

    print("Result gathered!")
    # driver.find_elements_by_css_selector
    results = driver.find_elements_by_class_name("SearchResultOneWayTop")

    flights = []

    # print(results)
    for result in results:
        airlineName = result.find_elements_by_class_name("AirlineName")[0].text
        airlineLogo = []
        logos = result.find_elements_by_class_name("AirlineLogoResultInfo")

        # departure and arrival
        dep = result.find_elements_by_class_name("Departure")[0]
        depTime = dep.find_elements_by_class_name("TimeBlockTop")[0].text
        depPlace = dep.find_elements_by_class_name("TimeBlockBottom")[0].text

        arr = result.find_elements_by_class_name("Arrival")[0]
        arrTime = arr.find_elements_by_class_name("TimeBlockTop")[0].text
        arrPlace = arr.find_elements_by_class_name("TimeBlockBottom")[0].text

        # transit info and facilities
        dur = result.find_elements_by_class_name("Duration")[0]
        duration = dur.find_elements_by_class_name("TimeBlockTop")[0].text
        transit = dur.find_elements_by_class_name("TimeBlockBottom")[0].text

        fac = result.find_elements_by_class_name("Facility")[0]
        baggage = fac.find_elements_by_class_name("WeightNumber")[0].text

        # price and buy link
        pr = result.find_elements_by_class_name("PricingBlock")[0]
        price = pr.find_elements_by_class_name("PriceNew")[0].text

        for logo in logos:
            logo = logo.get_attribute("src")
            airlineLogo.append( logo )
        
        flights.append({
            "airlineName": airlineName,
            "airlineLogo": airlineLogo,
            "departureTime": depTime,
            "departurePlace": depPlace,
            "arrivalTime": arrTime,
            "arrivalPlace": arrPlace,
            "duration": duration,
            "transit": transit,
            "baggageCapacity": baggage,
            "price": price

        })

    # print( flights )
    # with open('flights.json', 'w') as outfile:
    #     json.dump(flights, outfile)
    driver.quit()

    callback(json.dumps(flights))
 
 
if __name__ == "__main__":

    app = tornado.web.Application([
        (r"/", requestHandler),
    ])

    app.listen(PORT)
    print("Serving at port", PORT)
    tornado.ioloop.IOLoop.current().start()

    # httpd = HTTPServer(("127.0.0.1", PORT), requestHandler)
    # httpd.serve_forever()