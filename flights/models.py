# from django.db import models


# class Airport(models.Model):
#     iata_code = models.CharField(max_length=3, unique=True)
#     name = models.CharField(max_length=255)
#     city = models.CharField(max_length=255)
#     country = models.CharField(max_length=255)

#     def __str__(self):
#         return f"{self.iata_code} - {self.city}, {self.country}"

# class Airline(models.Model):
#     iata_code = models.CharField(max_length=3, unique=True)
#     name = models.CharField(max_length=250)

#     def __str__(self):
#         return f"{self.iata_code} - {self.name}"