from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from flights.serializers import FlightSearchSerializer, AirportSerializer
from flights.services.duffel_service import search_flights, get_offer, search_airports

import logging

logger = logging.getLogger(__name__)

class FlightSearchView(APIView):
    #Search for available flights via Duffel API

    @method_decorator(ratelimit(key='user', rate='20/m', method='GET', block=True))
    def get(self, request):
        serializer = FlightSearchSerializer(data=request.query_params)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data

        result = search_flights(
            origin=data['origin'],
            destination=data['destination'],
            departure_date=data['departure_date'],
            adults=data['adults'],
            cabin_class=data['cabin_class'],
            return_date=data.get('return_date'),     
        )

        if not result['success']:
            return Response({
                "error": result['error']}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            "count": result['count'],
            "origin": data['origin'],
            "destination": data['destination'],
            "departure_date": data['departure_date'],
            "cabin_class": data['cabin_class'],
            "flights": result['data']}, 
            status=status.HTTP_200_OK
        )


class FlightOfferDetailView(APIView):
    #Get full details of a specific flight offer

    @method_decorator(ratelimit(key='user', rate='60/m', method='GET', block=True))
    def get(self, request, offer_id):
        if not offer_id:
            return Response({
                "error": "Offer ID is required."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = get_offer(offer_id)

        if not result['success']:
            return Response({
                "error": result['error']}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(result['data'], status=status.HTTP_200_OK)


class AirportSearchView(APIView):
    #Search for airports by name or IATA code

    @method_decorator(ratelimit(key='user', rate='30/m', method='GET', block=True))
    def get(self, request):
        serializer = AirportSerializer(data=request.query_params)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['q']
        result = search_airports(query)

        if not result['success']:
            return Response({
                "error": result['error']}, 
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        return Response({
            "count": result['count'],
            "airports": result['data']}, 
            status=status.HTTP_200_OK
        )