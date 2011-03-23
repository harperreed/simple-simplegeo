import oauth2 as oauth
import time
import urllib

try:
  import simplejson
except:
  from django.utils import simplejson

try:
    from urlparse import parse_qs, parse_qsl
except ImportError:
    from cgi import parse_qs, parse_qsl

#https://github.com/simplegeo/python-simplegeo/blob/master/simplegeo/__init__.py
class Record(object):
    def __init__(self, layer, id, lat, lon, created=None, **kwargs):
        self.layer = layer
        self.id = id
        self.lon = lon
        self.lat = lat
        if created is None:
            self.created = int(time.time())
        else:
            self.created = created
        self.__dict__.update(kwargs)

    @classmethod
    def from_dict(cls, data):
        if not data:
            return None
        try:
            coord = data['geometry']['coordinates']
        except KeyError:
            pass
        record = cls(data['properties']['layer'], data['id'], lat=coord[1], lon=coord[0])
        record.created = data.get('created', record.created)
        record.__dict__.update(dict((k, v) for k, v in data['properties'].iteritems()
                                    if k not in ('layer', 'created')))
        return record

    def to_dict(self):
        return {
            'type': 'Feature',
            'id': self.id,
            'created': self.created,
            'geometry': {
                'type': 'Point',
                'coordinates': [self.lon, self.lat],
            },
            'properties': dict((k, v) for k, v in self.__dict__.iteritems() 
                                        if k not in ('lon', 'lat', 'id', 'created')),
        }

    def to_json(self):
        return simplejson.dumps(self.to_dict())

    def __str__(self):
        return self.to_json()

    def __repr__(self):
        return "Record(layer=%s, id=%s, lat=%s, lon=%s)" % (self.layer, self.id, self.lat, self.lon)

    def __hash__(self):
        return hash((self.layer, self.id))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id == other.id



# Set the API endpoint 

class simple_simplegeo:

    consumer_key = ''
    consumer_secret= ''
    token_key = ''
    token_secret= ''
    debug = False

    #seriously. wtf @ 2 different api versions. but i understand. records is
    #beta. 
    api_version = '1.0'
    record_api_version = '0.1'
    api_base_url = 'http://api.simplegeo.com:80/'+api_version
    record_api_base_url = 'http://api.simplegeo.com:80/'+record_api_version

    def __init__(self, consumer_key, consumer_secret, token_key=None, token_secret=None):
      self.consumer_key = consumer_key
      self.consumer_secret = consumer_secret
      self.consumer = oauth.Consumer(key=self.consumer_key, secret= self.consumer_secret)
      self.client = oauth.Client(self.consumer)

    def make_request(self, url,method,data=None):
      body = None

      if method == "GET" and isinstance(data, dict):
        url = url + '?' + urllib.urlencode(data)
      else:
        if isinstance(data, dict):
          body = urllib.urlencode(data)
        else:
          body = data
      if self.debug:
        print url

      resp, content = self.client.request(url, method, body)
      content = simplejson.loads(content)
      return content

    #http://simplegeo.com/docs/api-endpoints/simplegeo-features
    def get_feature_details(self, handle):
      url = self.api_base_url + "/features/"+handle+".json"
      response = self.make_request(url,"GET")
      return response

    def list_of_feature_categories(self):
      url = self.api_base_url + "/features/categories.json"
      response = self.make_request(url,"GET")
      return response

    #http://simplegeo.com/docs/api-endpoints/simplegeo-context
    def get_context_for_a_location(self, latitude=None, longitude=None, address=None, ip=None):
      if ip:
        url = self.api_base_url + "/context/"+ip+".json"
      elif address:
        url = self.api_base_url + "/context/address.json?address="+address
      elif latitude and longitude:
        url = self.api_base_url + "/context/"+str(latitude)+","+str(longitude)+".json"

      response = self.make_request(url,"GET")
      return response

    #http://simplegeo.com/docs/api-endpoints/simplegeo-places
    def search_for_nearby_places(self, q='', category='', num='', radius='', latitude=None, longitude=None, address=None, ip=None):
      p_state = False
      if ip:
        url = self.api_base_url + "/places/"+ip+".json"
      elif address:
        url = self.api_base_url + "/places/address.json?address="+address
      elif latitude and longitude:
        url = self.api_base_url + "/places/"+str(latitude)+","+str(longitude)+".json"

      params = {
          'q':q,
          'category':category,
          'num':num,
          'radius':radius,
          }
      response = self.make_request(url,"GET",params)
      return response


    #http://simplegeo.com/docs/api-endpoints/simplegeo-places#get-update-delete-place
    def get_feature(self, handle):
      url = self.api_base_url + "/features/"+handle+".json"
      response = self.make_request(url,"GET")
      return response

    #TODO
    def update_feature(self, handle, geo_json):
      url = self.api_base_url + "/features/"+handle+".json"
      response = self.make_request(url,"POST",geo_json)
      return response
    #TODO
    def create_feature(self, geo_json):
      url = self.api_base_url + "/places/"
      params = simplejson.loads(geo_json)
      response = self.make_request(url,"POST",params)
      return response

    #http://simplegeo.com/docs/api-endpoints/simplegeo-storage#single-record
    def get_record(self, layer, id):
      url = self.record_api_base_url + "/records/"+layer+"/"+id+".json"
      response = self.make_request(url,"GET")
      return response

    def create_record(self, record): #also update
      #just a note that i spent 2 fucking hours fucking with this and the issue
      #was the version numbers were off. the regular api is 1.0 this is 0.1
      #fuck you
      url = self.record_api_base_url + "/records/"+record.layer+"/"+record.id+".json"
      response = self.make_request(url,"PUT",record.to_json())
      return response

    def delete_record(self, layer, id):
      url = self.record_api_base_url + "/records/"+layer+"/"+id+".json"
      response = self.make_request(url,"DELETE")
      return response

    #http://simplegeo.com/docs/api-endpoints/simplegeo-storage#record-history
    def query_record_history(self, layer, id):
      url = self.record_api_base_url + "/records/"+layer+"/"+id+"/history.json"
      response = self.make_request(url,"GET")
      return response

    #http://simplegeo.com/docs/api-endpoints/simplegeo-storage#nearby
    def query_nearby_records(self, layer, latitude='',longitude='',ip='',geohash='', radius='',  limit='',types='', start='', end=''):
      params = {}
      if limit:
          params['limit'] = limit;
      if types:
          params['types'] = ','.join(types);
      if start:
          params['start'] = start;
      if end:
          params['end'] = end;
          
      if latitude and longitude:
        url = self.record_api_base_url + "/records/"+layer+"/nearby/"+str(latitude)+","+str(longitude)+".json"
        if radius:
            extra_params = {
              'radius':radius,
                }
            params = dict(params, **extra_params)
      #this one may not work
      elif geohash:
        url = self.record_api_base_url + "/records/"+layer+"/nearby/"+str(geohash)+".json"
      elif ip:
        url = self.record_api_base_url + "/records/"+layer+"/nearby/"+str(ip)+".json"

      #response = self.make_request(url,"GET",params) #this is a bug. i don't know why
      response = self.make_request(url,"GET", params) #if you don't pass the param it works
      return response

    #http://simplegeo.com/docs/api-endpoints/tools#spotrank
    #doesn't work. but doesn't work in official client either. HAH
    def population_density_by_day(self, dayname, latitude, longitude):
      url = self.api_base_url + "/density/"+dayname+"/"+str(latitude)+","+str(longitude)+".json"
      response = self.make_request(url,"GET")
      return response

    #doesn't work. but doesn't work in official client either. HAH
    def population_density_by_hour(self, dayname, hour, latitude, longitude):
      url = self.api_base_url + "/density/"+dayname+"/"+str(hour)+"/"+str(latitude)+","+str(longitude)+".json"
      response = self.make_request(url,"GET")
      return response




if __name__ == "__main__": 
    consumer_key=""
    consumer_secret=""

    api = simple_simplegeo(
            consumer_key=consumer_key, 
            consumer_secret=consumer_secret)

    #print api.get_feature_details("SG_2AziTafTLNReeHpRRkfipn_37.766713_-122.428938@1291796505")
    #print api.list_of_feature_categories()
    #print api.get_context_for_a_location(address='205 43rd ave, greeley, 80634')
    #print api.get_context_for_a_location(ip='98.222.40.222')
    #print api.get_context_for_a_location(latitude='37.778381',longitude='-122.389388')
    #print api.search_for_nearby_places(address='205 43rd ave, greeley, 80634')
    #print api.search_for_nearby_places(ip='98.222.40.222')
    #print api.search_for_nearby_places(latitude='37.778381',longitude='-122.389388')
    #print api.search_for_nearby_places(latitude='37.7645',longitude='-122.4294',q="diner", category="Restaurant")
    #print api.get_feature("SG_2AziTafTLNReeHpRRkfipn_37.766713_-122.428938@1291796505")
    #record = Record('harper', '5',37.778381, -122.389388)
    #record = Record('harper', '18',41.8675, -87.674400000000006)
    #print api.create_record(record)
    #print api.delete_record('harper','4')
    #print api.get_record('harper','4')
    #print api.query_record_history('harper','4')
    #print api.query_nearby_records(layer='harper',latitude='37.778381',longitude='-122.389388')
    #print api.query_nearby_records(layer='harper',ip='98.222.40.222')
    #print api.query_nearby_records(layer='harper',geohash='dp3whvtry7tj')
    #addr = '1462 N MILWAUKEE, CHICAGO, 60622'
    #print api.search_for_nearby_places(address=addr)
    #print api.population_density_by_day(dayname='fri', latitude='37.7645',longitude='-122.4294')


