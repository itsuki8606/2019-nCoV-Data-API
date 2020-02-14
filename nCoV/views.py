from django.shortcuts import render
from .prepocess import dataToJson,csvToJson
from django.http import JsonResponse
import request
import json
import logging
import datetime


def taiwan(sec, what):
    taiwan_time = datetime.datetime.now() + datetime.timedelta(hours=8)
    return taiwan_time.timetuple()

def create_logger():
    handler = logging.FileHandler('DEBUG.log', mode='a')
    logging.Formatter.converter = taiwan
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
logger = create_logger()

def query(request):
    try:
        logger.info("Time Query Start")
        if 'date' in request.GET:
            date = request.GET['date']
            logger.debug("Input Date: " + date)
            data = csvToJson(date)
            if data:
                data_json = json.loads(data)
                logger.info("Data of " + date)
                logger.debug(data_json)
                logger.info("Time Query Success")
                response = JsonResponse({
                    "status": True,
                    "data": data_json
                    }, status=200)
            else:
                logger.error("No data of " + date)
                logger.error("Time Query Failed")
                response = JsonResponse({
                    "status": False,
                    "message": "No data"
                    }, status=404)
        else:
            logger.error("Params invalid Error")
            logger.error("Time Query Failed")
            response = JsonResponse({
                "status": False,
                "message": "Params invalid Error"
                }, status=500)
    except Exception as e:
        logger.error(e, exc_info=True)
        logger.error("Time Query Failed")
        response = JsonResponse({
            "status": False,
            "message": "Error: " + str(e)
            }, status=500)
    return response


