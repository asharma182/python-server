import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import threading, time
import json, ast
import math
import pymongo
import datetime
import tornado.httpclient


from pymongo import MongoClient
from bson.objectid import ObjectId
from tornado_cors import CorsMixin
from tornado.options import define, options
from bson import json_util
from tornado import escape, gen
from bson.json_util import dumps
from tornado.locks import Condition


define("port", default=8080, help="run on the given port", type=int)

#Connecting MongoDb database
client = MongoClient('mongodb://dba:password@139.59.71.105:10948/grosodel')
db = client['grosodel']
# myrecord = {
#         "author": "Duke",
#         "title" : "PyMongo 101",
#         "tags" : ["MongoDB", "PyMongo", "Tutorial"],
#         "date" : datetime.datetime.utcnow()
#         }

# record_id = mydb.mytable.insert(myrecord)

# print(record_id)
# print(mydb.collection_names())

#Global Variables
global min_dis_vendor
global vendor_list
global min_dis_test
global customer_data  
global get_approval
global vendorConfirmationResponse
global isVendorConfirmed
global customerDataToVendor

min_dis_vendor=[]
get_approval = False 	
vendor_confirm= []
vendor_list=[]
vendor_onConfirm = []
customerDataToVendor = []
getVendorRequest = False
anyRequestFromCustomer={}
anyRequestFromCustomer['requestFromCustomer'] = False
vendorConfirmationResponse = False
isVendorConfirmed= []
condition = Condition()
BookedVendor=[]

#Vendor List for Test
#vendor_map = [{"id": 1,"latitude": 22.5574051, 'longitude': 88.4597658,'vendor_fname': 'Abhi','vendor_contact': '8585059894'},
#		{"id": 2,"latitude": 22.5784051, 'longitude': 88.4599058,'vendor_fname': 'Abhi','vendor_contact': '8585059894'},
#		{"id": 3,"latitude": 22.5884051, 'longitude': 88.4587658,'vendor_fname': 'Abhi','vendor_contact': '8585059894'}]

#customer_map=vendor_map

class Application(tornado.web.Application):
	def __init__(self):
		handlers = [(r"/map_data", UserMapHandler),
		#(r"/api/promo", PromoHandler),
		(r"/api/vendor/map_data",VendorMapHandler),
		(r"/con_vendors", ConfirmVendors),
		#(r"/get_customer", GetCustomer),
		(r"/logoutVendor", LogOutVendor),
		(r"/sendConfirmation", SendConfirmation),
		(r"/getLocationfromVendorAfterConfirmation", GetLocationfromVendorAfterConfirmation),
		(r"/sendCustomerLocationToFindComingVendor", SendCustomerLocationToFindComingVendor),
		(r"/userCancelBookingRequest", UserCancelBookingRequest)] 
		settings =dict(
			xsrf_cookies=False,debug=True)
		tornado.web.Application.__init__(self, handlers,**settings)

class UserMapHandler(tornado.web.RequestHandler):
	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def get(self):
		self.write(self.request.body)
		#data  = json.loads(self.request.body)
		print(str(self.request.version))
		#self.write(tornado.escape.json_encode(self.request.arguments["post"]))

	def post(self):
		#data = json.loads(self.request.body)
		data = escape.json_decode(self.request.body)
		customer_data = ast.literal_eval(json.dumps(data))
		print("data coming from customer",customer_data,data)
		map_location = {}
		#map_location=dist_calc()
		#map_location['latitude'] = 22.5794051
		#map_location['longitude'] = 88.4597658
		#vendor_map = [{"id": 1,"latitude": 22.5574051, 'longitude': 88.4597658},
		#{"id": 2,"latitude": 22.5784051, 'longitude': 88.4599058},
		#{"id": 3,"latitude": 22.5884051, 'longitude': 88.4587658}]
		#vendor_list = vendor_map
		#print(vendor_map)
		i=0
		if customer_data is not None and vendor_list is not None:
			while i < (len(vendor_list)):
				distance = cal_dist(customer_data['lat'],customer_data['lng'],vendor_list[i]['latitude'],vendor_list[i]['longitude'])
				print(round(distance,2))
				if (distance > 20):
					print("found vendor",vendor_list[i]['latitude'],i)
					vendor_list.pop(i)
				else:
					i+=1
		else:
			print("Customer is unable to send the request")
		print(vendor_list)

		# nextBookingId = db.mytable.find().sort('_id',-1).limit(1)
		# print(nextBookingId)
		# if db.mytable.find().count() == 0:
		# 	bookingRecord = {
		# 	"Uid": 'Book_1',
		# 	"CustLocLat" : customer_data['lat'],
		# 	"CustLocLong" : customer_data['lng'],
		# 	"date" : datetime.datetime.utcnow()
		# 	}
		# 	record_id = db.mytable.insert(bookingRecord)

		# for i in nextBookingId:
		# 	print(i['Uid'])
		# 	uid = i['Uid'].split('_')[1]
		# 	print(uid)
		# 	incrementUid = int(uid)+ 1
		# 	nextUid = 'Book_' + str(incrementUid)
		# 	print(nextUid)
		# 	bookingRecord = {
		# 	"Uid": nextUid,
		# 	"CustLocLat" : customer_data['lat'],
		# 	"CustLocLong" : customer_data['lng'],
		# 	"BkCreateDate" : datetime.datetime.utcnow()
		# 	}
		# 	record_id = db.mytable.insert(bookingRecord)
		self.write(json.dumps(vendor_list, default=json_util.default))

class VendorMapHandler(tornado.web.RequestHandler):
	def set_default_headers(self):
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def post(self):
		#data = json.loads(self.request.body)
		data = escape.json_decode(self.request.body)
		vendor_data = ast.literal_eval(json.dumps(data))
		if vendor_data is not None:
			print("vendor is sending location")
			i= int(1 + (len(vendor_list)))
			j=0
			if len(vendor_list) == 0:
				vendor_list.insert(i,{"id": i, "latitude":vendor_data['lat'], "longitude": vendor_data['lng'],"vendor_contact": vendor_data['v_phone'],
						"vendor_fname": vendor_data['v_fname'], "vendor_lname": vendor_data['v_lname']})
				#		"vendor_fname": data['v_name']})
			check_availability_of_phone = False
			print("vendor_list",vendor_list)

			for j in range(0,len(vendor_list)):
				if vendor_data['v_phone'] in vendor_list[j]['vendor_contact']:
					vendor_list[j]['latitude']=vendor_data['lat']
					vendor_list[j]['longitude']=vendor_data['lng']
					check_availability_of_phone = True
		else:
			print("Vendor is unable to send the location")


		if check_availability_of_phone == False:
			vendor_list.insert(i,{"id": i, "latitude":vendor_data['lat'], "longitude": vendor_data['lng'],"vendor_contact": vendor_data['v_phone'],
				"vendor_fname": vendor_data['v_fname'], "vendor_lname": vendor_data['v_lname']})
		#print(vendor_list)
		#sendVendorResquest = hasVendorConfirmed()
		#print("anyRequestFromCustomer['requestFromCustomer']",anyRequestFromCustomer['requestFromCustomer'])
		#val = hasVendorConfirmed()
		#print("min_dis_vendor.....................",min_dis_vendor)
		if(len(min_dis_vendor) != 0):
			if (min_dis_vendor[0]['vendor_contact'] == vendor_data['v_phone']):
				#print("got the data")
				if(anyRequestFromCustomer['requestFromCustomer'] == True):
					get_approval = True
					customerDataToVendor.insert(0,{"requestFromCustomer": True})
					self.write(json.dumps(customerDataToVendor, default=json_util.default))
					anyRequestFromCustomer['requestFromCustomer'] = False
					min_dis_vendor.pop()
					print(min_dis_vendor)
				else:
					self.write(json.dumps(anyRequestFromCustomer, default=json_util.default))



#tornado.httpclient.AsyncHTTPClient.configure("tornado.curl_httpclient.CurlAsyncHTTPClient")
class ConfirmVendors(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def get(self):
		self.write(self.request.body)
		#data  = json.loads(self.request.body)
		print(str(self.request.version))
		#self.write(tornado.escape.json_encode(self.request.arguments["post"]))

	@gen.coroutine		
	def post(self):
		#data = json.loads(self.request.body)
		data = escape.json_decode(self.request.body)
		vendor_map = vendor_list
		print("confirm vendors",len(vendor_map))
		i=0
		if data is not None:
			while i < (len(vendor_map)):
				distance = cal_dist(data['lat'],data['lng'],vendor_map[i]['latitude'],vendor_map[i]['longitude'])
				#print("min distnace:",min(round(distance,2)))
				vendor_confirm.insert(i,{"id": i , "distance": round(distance,2), "latitude": vendor_map[i]['latitude'], "longitude": vendor_map[i]['longitude'], "vendor_fname": vendor_map[i]['vendor_fname'],"vendor_contact": vendor_map[i]['vendor_contact'] })
				#print(vendor_confirm)
				if (distance > 2 ):
					print("found vendor",vendor_map[i]['latitude'],i)
					vendor_map.pop(i)
				else:
					i+=1
		print(vendor_confirm)
		customerDataToVendor.insert(0,data)
		if(len(vendor_list)== 0):
			print("--------------------------------------------------")
			self.write(json.dumps(False, default=json_util.default))
			self.finish()
			return
		else:
			min_dis = min(vendor_confirm, key=lambda x:x['distance'])
			vendor_confirm.remove(min_dis)
		
		print("confirmed vendor",min_dis,vendor_confirm)
		
		anyRequestFromCustomer['requestFromCustomer'] = True
		min_dis_vendor.insert(0,min_dis)
		print("vendor selected",min_dis_vendor)
		#t= threading.Timer(15.0, SendConfirmation.waitForVendorConfirmation)
		t= threading.Timer(15.0, waitForVendorConfirmation)
		t.start()
		yield condition.wait()
		print("out from barrier")
		print("calling the vendor function",isVendorConfirmed)

		if (isVendorConfirmed[0]['status'] == "Accepted"):
			min_dis['gotConfirmationFromVendor'] = True
			min_dis['timeToReach']= isVendorConfirmed[0]['timeToReach']
			print("confirmed vendor",min_dis)
			nextBookingId = db.mytable.find().sort('_id',-1).limit(1)
			print(min_dis)
			if db.mytable.find().count() == 0:
				bookingRecord = {
				"Uid": 'Book_1',
				"CustLocLat" : data['lat'],
				"CustLocLong" : data['lng'],
				"VendLocLat" : min_dis['latitude'],
				"VendLocLong" : min_dis['longitude'],
				"date" : datetime.datetime.utcnow()
				}
				record_id = db.mytable.insert(bookingRecord)

			for i in nextBookingId:
				print(i['Uid'])
				uid = i['Uid'].split('_')[1]
				print(uid)
				incrementUid = int(uid)+ 1
				nextUid = 'Book_' + str(incrementUid)
				print(nextUid)
				bookingRecord = {
				"Uid": nextUid,
				"CustLocLat" : data['lat'],
				"CustLocLong" : data['lng'],
				"VendLocLat" : min_dis['latitude'],
				"VendLocLong" : min_dis['longitude'],
				"BkCreateDate" : datetime.datetime.utcnow()
				}
				record_id = db.mytable.insert(bookingRecord)
			bookingRecord['gotConfirmationFromVendor']=True
			bookingRecord['timeToReach']= isVendorConfirmed[0]['timeToReach']
			for j in range(0,len(vendor_list)):
				if min_dis['vendor_contact'] in vendor_list[j]['vendor_contact']:
					print("removing confirmed vendor from the list")
					vendor_list.pop(j)
					BookedVendor.insert(j,min_dis)
			print(BookedVendor)		
			print("......................................................................", bookingRecord, vendor_list)
			self.write(json.dumps(bookingRecord, default=json_util.default))
		else:
			print("//////////////////////////////////////////////////////////////////////////")
		 	self.write(json.dumps(False, default=json_util.default))


# class PromoHandler(tornado.web.RequestHandler):
# 	def set_default_headers(self):
# 		print("setting headers!!!")
# 		self.set_header("Access-Control-Allow-Origin", "*")
# 		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
# 		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

# 	def options(self):
# 		#if self.request['Access-Control-Request-Method'] == 'POST':
# 		self.set_header("Access-Control-Allow-Headers", "Content-type")

# 	def get(self):
# 		self.write(self.request.body)
# 		#data  = json.loads(self.request.body)
# 		print(str(self.request.version))
# 		#self.write(tornado.escape.json_encode(self.request.arguments["post"]))

# 	def post(self):
# 		#data = json.loads(self.request.body)
# 		data = escape.json_decode(self.request.body)
# 		print(data)
# 		print("huiiii")
# 		print(self.request.uri)
# 		promo_number = {}
# 		promo_number['promo'] = '9585TRY8'
# 		self.write(json.dumps(promo_number, default=json_util.default)) 


def cal_dist(lat1,lon1,lat2,lon2):
	R=6371
	phy_1=math.radians(lat1)
	phy_2=math.radians(lat2)
	delta_phy=math.radians(lat2-lat1)
	delta_lambda=math.radians(lon2-lon1)

	a=(math.sin(delta_phy/2) * math.sin(delta_phy/2) + 
	math.cos(phy_1) * math.cos(phy_2) * math.sin(delta_lambda/2) * math.sin(delta_lambda/2))
	c= 2 * math.atan2(math.sqrt(a),math.sqrt(1-a))
	return (R * c)	




class SendConfirmation(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	@gen.coroutine
	def post(self):
		self.write(self.request.body)
		print("deleting vendor form the list")
		data = escape.json_decode(self.request.body)
		print(data)
		isVendorConfirmed.insert(0,data)
		print(isVendorConfirmed[0]['status'])
		#data  = json.loads(self.request.body)
		# for j in range(0,len(vendor_list)):
		# 	if mobNumber['mobNumber'] in vendor_list[j]['vendor_contact']:
		# 		vendor_list.pop(j)
		#self.write(json.dumps(vendor_list, default=json_util.default))

	# @gen.coroutine
	# def waitForVendorConfirmation():
	# 	print("waiting............")
	# 	#condition.notify()
	# 	if (isVendorConfirmed[0]['status'] != "Accepted"):
	# 		print("not confirmed")
	# 		return False
	# 	else:
	# 		print("returning confirmation from vendor")
	# 		condition.notify()
	# 		return True
def waitForVendorConfirmation():
		print("waiting............")
		#condition.notify()
		if (isVendorConfirmed[0]['status'] != "Accepted"):
			print("not confirmed")
			return False
		else:
			print("returning confirmation from vendor")
			condition.notify()
			return True

##Once vendor confirmed change location of vendor on the way to customer

class GetLocationfromVendorAfterConfirmation(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def post(self):
		self.write(self.request.body)


class SendCustomerLocationToFindComingVendor(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def post(self):
		self.write(self.request.body)


class LogOutVendor(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def post(self):
		self.write(self.request.body)
		print("deleting vendor form the list")
		data = escape.json_decode(self.request.body)
		#data  = json.loads(self.request.body)
		for j in range(0,len(vendor_list)):
			if data['MobNo'] in vendor_list[j]['vendor_contact']:
				vendor_list.pop(j)
		self.write(json.dumps(vendor_list, default=json_util.default))
		
class UserCancelBookingRequest(tornado.web.RequestHandler):

	def set_default_headers(self):
		print("setting headers!!!")
		self.set_header("Access-Control-Allow-Origin", "*")
		self.set_header("Access-Control-Allow-Headers", "x-requested-with")
		self.set_header('Access-Control-Allow-Methods', 'POST, GET')

	def options(self):
		#if self.request['Access-Control-Request-Method'] == 'POST':
		self.set_header("Access-Control-Allow-Headers", "Content-type")

	def post(self):
		data = escape.json_decode(self.request.body)
		rec = ast.literal_eval(json.dumps(data))
		print(rec)
		cancelRecord={
			"MobNo": rec['MobNo'],
			"reason": rec['reason']
		}
		record_id = db.BookingCancel.insert(cancelRecord)
		self.write(json.dumps(True, default=json_util.default))




if __name__ == "__main__":
	tornado.options.parse_command_line() 
	http_server = tornado.httpserver.HTTPServer(Application())
	http_server.listen(options.port)
	tornado.ioloop.IOLoop.instance().start()
