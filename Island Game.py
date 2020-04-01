from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import *

from math import *
from random import randint,choice,shuffle
from itertools import product

from ast import literal_eval as str_to_py
import os
###############################

from logging import *
basicConfig(level=DEBUG,format="%(levelname)s - %(message)s")

#disable(INFO)#toggle this for developer mode and user
##############################

SETTLEMENTS = ["Hamlet","Village","Town","City"]
WATERHEXAGONS = ["Lake","Shallow Waters","Reservoir"]

LAST = False


global World_Name
World_Name = "Island"
day = 0

def day_passed():
	global day
	day += 1 #day changes
	Day_Display.config(text="Day " + str(day)) #############
	info("Day " +str(day)+":") #############

	for land in Land.List:        #search all lands


		###Update Cities###
		if type(land.structure) == Settlement:    #if land has building on it
			land.structure.collect_resources()
			land.structure.feed_inhabitants()
			land.structure.manufacture()

			if day % 30 == 0:
				land.structure.collect_taxes()


		if type(land.structure) == Structure:
			land.structure.collect_resources()

		###Update Ecosystems###
		if land.farming_type == "Sustainable":
			land.first_day = None
		elif land.farming_type == "Unsustainable": #if farming is sustainable
			if land.first_day:
				if land.first_day + 10 == day:
					if land.type == "Jungle":
						land.change_type(type="Forest")
						land.first_day = None
					elif land.type == "Forest":
						land.change_type(type="Plains")
						land.first_day = None
					elif land.type == "Plains":
						land.change_type(type="Desert")
						land.first_day = None
				elif land.first_day + 5 == day:
					if land.type == "Farmland":
						land.change_type(type="Desert")
						land.first_day = None

			else:
			   land.first_day = day
		elif land.farming_type == "Growth": #if farming is sustainable
			if land.first_day:
				if land.first_day + 10 == day:
					if land.type == "Plains":
						land.change_type(type="Forest")
						land.first_day = None
					elif land.type == "Farmland":
						land.change_type(type="Plains")
						land.first_day = None
				elif land.first_day + 20 == day:
					if land.type == "Forest":
							land.change_type(type="Jungle")
							land.first_day = None
			else:
			   land.first_day = day
		elif land.farming_type == None:
			land.first_day = None
		else:
			raise Exception("Unknown farming type",land.farming_type)

	for cart in Trading_Cart.List:

		cart.next()
   
	root.after(10000,day_passed)

def collect_world_taxes():
	info("Taxes Collected")
	for land in Land.List:
		if land.structure:
			if land.structure.type in SETTLEMENTS:    #if land has building on it
				land.structure.collect_taxes(25) # remove this


#######Classes########

class Land():
	"""A hexagon tile"""

	List = []

	def __init__(self,x,y,z,type_="Plains"):
		
		self.hexCoords = (x,y,z)    #hex coordinates

		self.List.append(self)

		self.selected = False

		self.owned = False
		self.travelable = False
		self.farming_type = None

		
		#Getting normal x and y coords [Don't mess,this took me ages to find]
		size_of_gaps = 40
		self.x  = (size_of_gaps * x * 3/4) + 300
		self.y = -(sqrt(3)/2  * size_of_gaps *( x/2 + y )) + 250
		

		self.type = type_ # set land type
		self.structure = None
		
		self.calculate_base_resources()

		if not self.type in WATERHEXAGONS:
			self.population = randint(1,5)
		else:
			self.population = 0

		self.colour = ("black","white")
		self.draw()

		self.find_nearby()

	def draw(self):

		########Deciding colours of the hexagon###########
		if self.type == "Plains":
			colour = ("black", "chartreuse4")
		elif self.type == "Farmland":
			colour = ("black", "dark goldenrod")
		elif self.type == "Forest":
			colour = ("black", "forest green")
		elif self.type == "Jungle":
			colour = ("black", "dark green") 
		elif self.type == "Mountains":
			colour = ("black", "gray")
		elif self.type == "Reservoir":
			colour =  ("brown", "powder blue")
		elif self.type == "Lake":
			colour =  ("powder blue", "powder blue")
		elif self.type == "Shallow Waters":
			colour =  ("light blue", "light blue")
		elif self.type == "Desert":
			colour = ("black", "yellow")
		else:
			colour = ("red", "red")

		self.colour = colour
		
		
		#Getting normal x and y coords        
		start_x  = self.x - 10
		start_y = self.y - 20

		####get hexagon coordinates####
		hex_corner_hexCoords = []
		for i in range(0,6):
			end_x = start_x + 20 * cos(radians(60 * i))
			end_y = start_y + 20 * sin(radians(60 * i))
			hex_corner_hexCoords.append((start_x, start_y))
			start_x = end_x
			start_y = end_y
		###put hexagon on canvas#####
		self.image = canvas.create_polygon(hex_corner_hexCoords,fill=colour[1],outline=colour[0],tags=["Land",str(self.hexCoords)])

	def build(self,building="Hamlet"):
		
		if building == "Road":   #Roads
			Land_found = False
			
			for land in self.find_nearby():
				
				if land.travelable and not already_linked(self,land,Road.List): #if can connect to somewhere
					road = Road(self,land) # Build <-------------------------
					Land_found = True

			if Land_found == False:
				messagebox.showerror("Road Error", "Needs somewhere to connect to")

			else:
				info("Built " + building)

				update_screen(self,"Land")



		else:          #not Roads
			info("Built " + building)
			
			if building in SETTLEMENTS:
				self.structure = Settlement(self,building) #Build <-------------------------
				
				self.population = self.structure.population

				self.travelable = True

				for land in self.find_nearby(self.structure.range_of_collection) + [self]:
					land.owned = True
					land.farming_type = "Sustainable"

				Connected = False
				for land in self.find_nearby():
					if land.structure and not already_linked(self,land,Road.List): #if can connect to somewhere
						Road(self,land)
						Connected = True


				if not Connected:
					for land in self.find_nearby():
						if land.travelable and not already_linked(self,land,Road.List): #if can connect to a road
							Road(self,land)
							Connected = True
							break


				update_screen(self.structure,"Settlement")

			else:
				self.structure = Structure(self,building)  #Build <-------------------------
				self.farming_type = "Sustainable"
				self.travelable = True
				self.owned = True

				Connected = False
				for land in self.find_nearby():
					if land.structure and not already_linked(self,land,Road.List): #if can connect to somewhere
						Road(self,land)
						Connected = True


				if not Connected:
					for land in self.find_nearby():
						if land.travelable and not already_linked(self,land,Road.List): #if can connect to a road
							Road(self,land)
							Connected = True
							break

				update_screen(self.structure,"Structure")


			
					#root.update_idletasks()

	def destroy_structure(self):

		self.structure.destroy()

		update_screen(self,"Land")

	def find_nearby(self,Range=1):
		
		nearbyhexcoords = [(+1, -1,  0),(+1,  0, -1),(+1,  0, -1),( 0, +1, -1),(-1, +1,  0),(-1,  0, +1),( 0, -1, +1)]
		self.nearbyLands = []

		
		for coords in nearbyhexcoords:
			other_land_coord = []
			for i in range(0,3):
				other_land_coord.append(self.hexCoords[i] + coords[i])
			

			#finding proper land
			for land in Land.List:
				if list(land.hexCoords) == other_land_coord:
					self.nearbyLands.append(land)

		params = []
		for x in range(Range+1):
			params.append(self.nearbyLands)



		#list(product(*tuple(params)))

		self.nearbyLands = list(set(self.nearbyLands))

		return self.nearbyLands

	def calculate_base_resources(self):
		if self.type == "Plains":
			resources = {"meat":(20 + randint(-5,5))}
		elif self.type == "Forest":
			resources = {"wood":(50 + randint(-5,5)),"meat":(15 + randint(-5,5))}
		elif self.type == "Jungle":
			resources = {"wood":70 + randint(-5,5),"meat":5 + randint(-5,5)}
		elif self.type == "Mountains":
			resources = {"stone":50 + randint(-5,5),"meat":5 + randint(-2,5)}
		elif self.type == "Lake":
			resources = {"fish":20 + randint(-5,5)}
		elif self.type == "Reservoir":
			resources = {"fish":10 + randint(-5,5)}

		elif self.type == "Desert":
			resources = {"gems":5,"iron":5}
		elif self.type == "Farmland":
			resources = {"wheat":50 + randint(-5,5),"meat":35 + randint(-5,5),"milk":20 + randint(-5,5)}
		elif self.type == "Shallow Waters":
			resources = {"fish":(50 + randint(-5,5))}
		else:
			resources = {"?":1}
			raise Exception("Unknown land type:",self.type)
			

		self.resources = resources

	def change_type(self,type="plains"):
		self.type = type
		self.calculate_base_resources()
		self.draw()
	
		update_screen(self,"Land")

	def highlight(self,colour=None):

		if not colour:
			canvas.itemconfig(self.image,outline=self.colour[0]) #Use normal colour
		else:
			canvas.lift(self.image) #Lift up
			canvas.itemconfig(self.image,outline=colour) #and highlight with special colour
			


	def get_str_info(self):

		information_string = ""

		#stringing coords
		str_coods = str([int(self.x),int(self.y)])

		#stringing resources
		str_resources = ""
		for resource in self.resources:
			str_resources += resource.title() + ":" + str(self.resources[resource]) + ",\t"


		#land information
		information_string +=  "Type: " + self.type

		information_string += "\t| Structure: " +  str(self.structure)

		information_string += "\nHex Coords: " +  str(self.hexCoords)
		information_string += "\t| Coords: " + str_coods
		information_string += "\nPopulation:" + str(self.population)
		information_string += "\t| Owned: " + str(self.owned)
		information_string += "\t| Farming: " + str(self.farming_type)
		information_string += "\t| Travelable: " + str(self.travelable)
		information_string += "\nResources:{" + str_resources
		
		information_string = information_string[:-2] + "} per day\n\n\n"

		return information_string

	def __str__(self):
		return str(self.hexCoords)


class Site():

	List = []

	def __init__(self,land,type="Camp",stored_resources={}):

		self.land = land
		self.type = type
		self.population = land.population
		self.stored_resources = stored_resources

		self.specialise()

		self.coords = (self.land.x,self.land.y)

		self.draw()

		self.name = self.figure_out_name()

		Site.List.append(self)
		self.List.append(self)

	def specialise(self):

		pass

	def draw(self):

		class_name = type(self).__name__

		font="Verdana 10"
		if type(self) == Settlement:
			font += " bold"


		self.image = canvas.create_text(self.coords,text=self.type[0],tags=[class_name,str(self.coords)],font=font)

		return self.image

	def destroy(self):

		#Delete Image
		canvas.delete(self.image)

		#Remove from lists
		self.List.remove(self)
		Site.List.remove(self)

		self.land.structure = None

		self.land.owned = False
		self.land.population = self.population
		self.land.travelable = False
		self.land.farming_type = None

		info("Destroyed " + self.name)#destroy
		update_screen(self.land,"Land")

	def send_resources(self,resources,to,send_error=True):
		
		#Finding path
		path = []
		path_found = False
		current = self.land
		explored = []

		def find_goto(current,explored):
			for land in current.find_nearby():
				if land not in explored and land.travelable:
					path.append(current.hexCoords)
					explored.append(current)
					info("From {} to {}".format(current.hexCoords,land.hexCoords))
					current = land
					break
			else:
				raise Exception("No suitable gotos")
			return current


		while not path_found:
			try:
				current = find_goto(current,explored)
			except:
				messagebox.showerror("No Connection","We can't send resources from "+str(self)+" at "+str(self.land.hexCoords)
											 +" to "+str(to)+" at "+str(to.land.hexCoords)+" without roads connecting them!")
				break

			if current.structure == to:
				path.append(current.hexCoords)
				info("FOUND!!!!!")
				info(path)
				path_found = True
				break


		
		if path_found == True:
			#remove resources
			self.remove_resources(resources,send_error=True)

			Cart = Trading_Cart(path,resources,to)

	def remove_resources(self,resources,send_error=True):#send error sends an error message to the user

		enought_resources = True#set true
		#removing resources
		for item in resources:
			if item in self.stored_resources: #if we have resource
				if 0 < self.stored_resources[item] - resources[item]:#if we have enough of the resource
					if enought_resources: #if resource is still true #
						enought_resources = True #set true           # We don't actually need this code but it explains itself better so....
				else:
					##we dont have that resource
					if send_error:
						messagebox.showerror("Not enough "+item+"s", "You need "+str(resources[item] - self.stored_resources[item])+" more "+item)
					enought_resources = False
					
			else:
				if send_error:
					messagebox.showerror("No "+item, "You need "+str(resources[item])+" "+item)
				enought_resources = False
				
		if enought_resources == False: #if not enough resources
			raise Not_Enough_Resources("Not Enough Resources",resources) #raise error to be caught when function not correctly executed
		else:
			for item in resources:
				self.stored_resources[item] -= resources[item]   #remove resources

	def figure_out_name(self):

		return str(self.type)

	def __str__(self):

		return self.name

class Settlement(Site):
	"""A settlement on the map"""

	List = []

	def specialise(self):

		self.number_of_houses = 0
		self.special_buildings = []
		self.range_of_collection = 0

		self.population_feeling = "Content"
		
		if self.type == "Hamlet":
			self.population += 5 + randint(-2,2)
			self.number_of_houses = 3 + randint(-1,1)
			self.range_of_collection = 1
		
		elif self.type == "Village":
			self.population += 10 + randint(-5,5)
			self.number_of_houses = 8 + randint(-2,2)
			self.range_of_collection = 1
			
		elif self.type == "Town":
			self.population += 20 + randint(-10,10)
			self.number_of_houses = 20 + randint(-4,4)
			self.range_of_collection = 1
			
		elif self.type == "City":
			self.population += 30  + randint(-15,15)
			self.number_of_houses = 32 + randint(-5,5)
			self.range_of_collection = 2
		else:
			raise Exception("Unknown settlement type",self.type)



	def figure_out_name(self):

		#############Different Naming ##########|||||Only Half Works
		SurroundingLandtypes = {}
		for land in self.land.find_nearby():
			if land.type in SurroundingLandtypes:
				SurroundingLandtypes[land.type] =+ 1
			else:
				SurroundingLandtypes[land.type] = 1

		Most_Common_Surrounding_Land_Type = max(SurroundingLandtypes, key=lambda k: SurroundingLandtypes[k])

		if  Most_Common_Surrounding_Land_Type == "Mountains":
			name = "Mining " + self.type
		elif Most_Common_Surrounding_Land_Type in WATERHEXAGONS:
			name = "Fishing " + self.type
		elif Most_Common_Surrounding_Land_Type == "Farmland":
			name = "Farming " + self.type
		elif Most_Common_Surrounding_Land_Type == "Forest":
			name = "Woodland " + self.type
		else:
			name = self.type

		return name

	def build(self,building):

		try:
			if building == "Mill":
				self.remove_resources({"wood":20,"stone":5})
			elif building == "Forge":
				self.remove_resources({"wood":15,"stone":10})
			elif building == "Port":
				self.remove_resources({"wood":45})
			elif building == "Shipyard":
				self.remove_resources({"wood":60})
		except:
			info("Not enough resources to add "+ building +" to "+str(self))
		else:
			info(building+" added")
			self.special_buildings.append(building)

		update_screen(self,"Settlement")

	def upgrade(self,upgrade_to):
		try:
			if upgrade_to == "Village":
				self.remove_resources({"wood":40})
			elif upgrade_to == "Town":
				self.remove_resources({"wood":80,"stone":50})
			elif upgrade_to == "City":
				self.remove_resources({"wood":120,"stone":80})
		except:
			info("Not enough resources to upgrade to "+ upgrade_to)
		else:
			info("Upgrading " + self.type + " to " + upgrade_to)
			self.type = upgrade_to

			if self.type == "Hamlet":
				self.population += 5 + randint(-2,2)
				self.number_of_houses = 3 + randint(-1,1)
				self.range_of_collection = 1
		
			elif self.type == "Village":
				self.population += 10 + randint(-5,5)
				self.number_of_houses = 8 + randint(-2,2)
				self.range_of_collection = 1
				
			elif self.type == "Town":
				self.population += 20 + randint(-10,10)
				self.number_of_houses = 20 + randint(-4,4)
				self.range_of_collection = 1
				
			elif self.type == "City":
				self.population += 30  + randint(-15,15)
				self.number_of_houses = 32 + randint(-5,5)
				self.range_of_collection = 2
					

			canvas.delete(self.image)
			self.draw()
			
			self.land.population = self.population

			for land in self.land.find_nearby(self.range_of_collection):
				land.owned = True

			self.name = self.type

			update_screen(self,"Settlement")
				
	def destroy(self):
		super().destroy()

		for land in self.land.find_nearby(self.range_of_collection):
			land.owned = False
			land.farming_type = None


		info("Destroyed " + str(self.type))#destroy
		update_screen(self.land,"Land")

	def collect_resources(self):
		for resource in self.land.resources:
			try:
				self.stored_resources[resource] += self.land.resources[resource]
			except KeyError:
				self.stored_resources[resource] = self.land.resources[resource]
				
		for land in self.land.find_nearby(self.range_of_collection): #search nearby lands     
				for resource in land.resources:
					if land.farming_type == "Sustainable": #if farming is sustainable
						collected_resource = land.resources[resource]
					elif land.farming_type == "Unsustainable": #if farming is sustainable
						collected_resource = land.resources[resource] * 2
					elif land.farming_type == "Growth": #if farming is sustainable
						collected_resource = int(land.resources[resource] * 0.5)
					elif land.farming_type == None:
						collected_resource = 0
					else:
						raise Exception("Unknown Farming Type:",land.farming_type)
						
					try:
						self.stored_resources[resource] += int(collected_resource * (self.population/10)) + randint(-5,5)
					except KeyError:
						 self.stored_resources[resource] = int(collected_resource * (self.population/10))  + randint(-5,5)

	def feed_inhabitants(self):
		for person in range(self.population):
			for food in ["fish","meat","bread","milk"]:
				try:
					if self.stored_resources[food] >= 2:
						self.stored_resources[food] -= 2
						break
				except KeyError:
					pass

			else:
				self.population -= 1
				self.land.population -= 1
				self.population_feeling = "Starved"

		if self.population_feeling == "Starved":
			messagebox.showerror("Your people are starving!","People are starving in a " + self.type + " on " + str(self.land.hexCoords))

	def manufacture(self):
		if "Mill" in self.special_buildings:
			try:
				self.remove_resources({"wheat":5},send_error=False)
			except:
				info("Not enough wheat to turn into bread")
			else:
				try:
					self.stored_resources["bread"] += 1
				except KeyError:
					self.stored_resources["bread"] = 1
			
		if "Forge" in self.special_buildings:
			try:
				self.remove_resources({"iron":5},send_error=False)
			except:
				info("Not enough iron to turn into steel")
			else:
				try:
					self.stored_resources["steel"] += int(self.stored_resources["iron"] - 5 / 5)
				except KeyError:
					self.stored_resources["steel"] = int(self.stored_resources["iron"] - 5 / 5)

	def collect_taxes(self,per=25):
		for person in range(self.population):
			if self.type == "Hamlet":
				gold = 10 + randint(-5,5)
			elif self.type == "Village":
				gold = 20 + randint(-5,5)
			elif self.type == "Town":
				gold = 30 + randint(-10,10)
			elif self.type == "City":
				gold = 35 + randint(-20,20)
			else:
				raise Exception("Unknown settlement type",self.type)
				
			try:
				self.stored_resources["gold"] += int(gold*(per/100))
			except KeyError:
				self.stored_resources["gold"] = int(gold*(per/100))

	def get_str_info(self):

		information_string = ""

		#stringing resources
		str_resources = ""
		for resource in self.stored_resources:
			str_resources += resource.title() + ":" + str(self.stored_resources[resource]) + ",\t"


		#land information
		information_string =  "Name: " + self.name
		information_string +=  "\t| Type: " + self.type
		information_string += "\nPopulation: " + str(self.population)
		information_string += "\t| Houses: " + str(self.number_of_houses)
		information_string += "\t| Specialized buildings: " + str(self.special_buildings)
		information_string += "\nStored Resources:{" + str_resources
		information_string = information_string[:-2] + "}\n\n\n"
		information_string += "\nPopulation Mood: " + self.population_feeling

		return information_string

class Structure(Site):
	"""Any building that's not a settlement"""

	List = []

	def collect_resources(self):

		Mine_Resources = {"stone": 80 +randint(-10,10),"iron":50 +randint(-10,10),"copper":70 +randint(-10,10)}
		Farm_Resources = {"meat": 80 +randint(-10,10),"milk":50 +randint(-10,10),"eggs":70 +randint(-10,10)}

		No_Resources = {}


		if self.type == "Mine":
			resources_dict = Mine_Resources
		elif self.type == "Farm":
			resources_dict = Farm_Resources
		else:
			resources_dict = No_Resources

		for resource in resources_dict:
			try:
				self.stored_resources[resource] += resources_dict[resource]
			except KeyError:
				self.stored_resources[resource] = resources_dict[resource]

	def get_str_info(self):


		information_string = "You clicked on the " + str(self) + "\n"

		if self.stored_resources:
			str_resources = ""
			for resource in self.stored_resources:
				str_resources += resource.title() + ":" + str(self.stored_resources[resource]) + ",\t"


			information_string += "It has " + str_resources


		return information_string


class Link():

	List = []

	def __init__(self,start_land,end_land,half=False):

		self.start = start_land

		self.end = end_land

		self.half = half

		self.midpoint = self.caculate_midpoint()

		self.image = self.draw()

		Link.List.append(self)
		self.List.append(self)

		self.name = type(self).__name__

	def draw(self):

		self.image = None

		return image

	def destroy(self):
		
		canvas.delete(self.image)

		try:
			self.List.remove(self)
			Link.List.remove(self)
		except:
			error("Got wrong link")

		

	def caculate_midpoint(self):

		midpoint_x = (self.start.x + self.end.x)/2
		midpoint_y = (self.start.y + self.end.y)/2

		midpoint_coords = (midpoint_x,midpoint_y)

		return midpoint_coords

	def get_str_info(self):

		return ""

class Road(Link):

	List = []

	def draw(self):

		self.start.travelable = True
		self.end.travelable = True

		self.start.owned = True
		self.end.owned = True

		self.List.append(self)

		self.image = canvas.create_line(self.start.x,self.start.y,self.end.x,self.end.y,fill="black",dash=(1,4),tags=["Road",str(self.midpoint)])

		return self.image

	def destroy(self):
		super().destroy()

		if not self.start.structure:
			self.start.owned = None
			self.start.travelable = False


		if not self.end.structure:
			self.end.owned = None
			self.end.travelable = False


		update_screen(self.start,"Land")

	def get_str_info(self):

		information_string = "You clicked on a road.\n"

		if self.start.structure and not str(self.start.structure) == "Road":
			information_string +=  "Going from the " + str(self.start.structure) + " "
		else:
			information_string += "Going "


		if self.start.type == self.end.type:
			information_string +=  "through " + str(self.end.type) + '('+ str(self.start.hexCoords) +'and'+ str(self.end.hexCoords)+')'
		else:
			information_string +=  "through " + str(self.start.type) + str(self.start.hexCoords)
			information_string +=  " and " + str(self.end.type)  + str(self.end.hexCoords)

	
		if self.end.structure and not str(self.end.structure) == "Road":
			information_string +=  " to the " + str(self.end.structure) + "\n"

		return information_string

class River(Link):

	List = []

	def draw(self):

		self.List.append(self)

		if self.half:

			midCoords = self.caculate_midpoint()

			midX, midY = midCoords

			self.end.x = midX
			self.end.y = midY

			self.caculate_midpoint()

		self.image = canvas.create_line(self.start.x,self.start.y,self.end.x,self.end.y,fill="light blue",tags=["River",str(self.midpoint)],smooth=True)

		return self.image

	def dam(self):

		if not self.start.type in ["Mountains"] + WATERHEXAGONS:
			info("Dammed "+str(self.start.hexCoords))
			self.start.change_type("Reservoir")
			if self.start.structure:
				self.start.structure.destroy()

			for road in Road.List:
				if road.start.hexCoords == self.start.hexCoords or road.end.hexCoords == self.start.hexCoords:
					road.destroy()
		else:
			info("Can't dam there")


	def get_str_info(self):

		information_string = "You clicked on a river.\n"

		if self.start.type == "Mountains":
			information_string +=  "Going from a spring "
		else:
			information_string += "Going "


		if self.start.type == self.end.type:
			information_string +=  "through " + str(self.end.type) + '('+ str(self.start.hexCoords) +'and'+ str(self.end.hexCoords)+')'
		else:
			information_string +=  "through " + str(self.start.type) + str(self.start.hexCoords)
			information_string +=  " and " + str(self.end.type)  + str(self.end.hexCoords)

	
		if self.end.type == "Shallow Waters":
			information_string +=  " to the Sea.\n"

		return information_string


def already_linked(place1,place2,link_list=Link.List):

	AlreadyLinked = False
	for link in link_list:
		if link.start == place1 and link.end == place2:
			AlreadyLinked = True
		elif link.end == place1 and link.start == place2:
			AlreadyLinked = True

	return AlreadyLinked


class Moveable():

	List = []

	def __init__(self,location):

		self.location = location

		self.draw()

		self.List.append(self)

	def draw(self):

		x,y,z = self.location

		size_of_gaps = 40
		self.x  = (size_of_gaps * x * 3/4) + 300
		self.y = -(sqrt(3)/2  * size_of_gaps *( x/2 + y )) + 250

		self.image = canvas.create_text((self.x,self.y),text="h-w",tags=["Moveable",str(self.location)],font="Verdana 10 bold")

	def erase(self):

		canvas.delete(self.image)


	def get_str_info(self):

		return ""


class Trading_Cart(Moveable):

	List = []

	def __init__(self,path,resources,to):

		self.path = path

		self.to = to

		self.resources = resources

		self.stage_of_journey = 0

		self.location = path[self.stage_of_journey]

		self.draw()

		self.List.append(self)

	def draw(self):

		x,y,z = self.location

		size_of_gaps = 40
		self.x  = (size_of_gaps * x * 3/4) + 300
		self.y = -(sqrt(3)/2  * size_of_gaps *( x/2 + y )) + 250

		self.image = canvas.create_text((self.x,self.y),text="h-w",tags=["Trading_Cart",str(self.location)],font="Verdana 10 bold")

	def delete(self):

		canvas.delete(self.image)

	def next(self):

		self.delete()

		self.stage_of_journey += 1

		try:
			self.location = self.path[self.stage_of_journey]
		except:
			self.finished()
		else:
			self.draw()
		
	def finished(self):

		#giving resources
		for item in self.resources:
			try:
				self.to.stored_resources[item] += self.resources[item]
			except KeyError:
				self.to.stored_resources[item] = self.resources[item]


	def get_str_info(self):

		information_string = "You clicked on a cart.\n"


		str_resources = ""
		for resource in self.resources:
			str_resources += resource.title() + ":" + str(self.resources[resource]) + ",\t"

		information_string += "It has " + str_resources + "\n"

		information_string += "It's going to " + self.to.name + " from "+ str(self.path[0]) +"\n"

		information_string += "It's currently at " + str(self.location)  +"\n"



		return information_string

		
#####GUIs####

def move_resources_menu(settlement):
	####Titles####
	top = Toplevel(root,width=20,height=20) ; top.title("Moving Resources")
	Label(top,text="Moving Resources:",font=("Georgia", "12", "bold")).grid(columnspan=2)

	###Finding Settlements###
	Settlement_Lookup = {}
	for site in Site.List:
		if not site == settlement and site.land.owned:
			Settlement_Lookup[str(site) +" at "+str(site.land.hexCoords)] = site

	Label(top,text=" From:                            To:").grid(row=1,column=0)
	
	##From##
	Label(top,text=settlement.name+" at "+str(settlement.land.hexCoords)+ "   to ").grid(row=2,column=0)
	
	##To##
	
	other_settlement = StringVar()
	other_settlement.set("send to")

	drop = OptionMenu(top,other_settlement,*Settlement_Lookup)
	drop.grid(row=2,column=1)

	
	###Resources###
	Label(top,text="Resources:").grid(row=3,column=0,sticky=W)
	
	resource = StringVar()

	drop = OptionMenu(top,resource,*settlement.stored_resources).grid(row=4,column=0)
		

	number_of_resource = IntVar()
	spinbox = Spinbox(top,textvariable=number_of_resource, from_=0, to=0,width=15)
	spinbox.grid(row=4,column=1)
	
	def update(num1,num2,num3):
		spinbox.config(from_=0,to=settlement.stored_resources[resource.get()])
		
	resource.trace("w", update)
	
	####Finish and Exit####
	def activate_send_resources_function(settlement,resources,to):
		if not to == "send to":
			settlement.send_resources(resources,Settlement_Lookup[to])
		top.destroy()

	
	Button(top,text="Done",command=lambda:activate_send_resources_function(settlement,{resource.get():number_of_resource.get()},to=other_settlement.get())).grid(columnspan=2)

def chose_farming_type_menu(land):
	top = Toplevel(root,width=20,height=20) ; top.title("Pick Farming Type")
	Label(top,text="Pick Farming Type:").grid()

	FARMING_TYPES = ["Unsustainable","Sustainable","Growth",None]

	v = StringVar()
	v.set(land.farming_type)

	def change_farming_type(land,type_):
		land.farming_type = type_
		update_screen(object_class=land,info_about="Land")
		top.destroy()

	for type_ in FARMING_TYPES:
		Radiobutton(top,text=str(type_),padx = 20, variable=v,value=type_).grid()


	Button(top,text="Enter",command=lambda:change_farming_type(land,v.get())).grid()
	
########################Creating,Saving and opening worlds#######################
def create_new_custom_world():
	global World_Name

	clear_world()
	
	if WorldNameEntry.get() == "":
		World_Name = "Temp World"
	else:
		World_Name = WorldNameEntry.get()
		
	if WorldsizeEntry.get() == "":
		World_Size = 6
	else: 
		World_Size = int(round(float(WorldsizeEntry.get()))) + 1
		
	top.destroy()
	canvas.delete(ALL) # remove all items
	
	draw_island(World_Size)

	update_screen()

def add_rivers(num=1):

	def flow_river_from(higher_land):

		Priority_Pyramid = [[],[],[],[],[]]

		for land in higher_land.find_nearby():

			AlreadyRivered = False
			for river in River.List:
				if river.start == land or river.end == land:
					AlreadyRivered = True


			if already_linked(land,higher_land,River.List) or land in RiverFlow:
				#River has already been here
				pass

			elif land.type == "Shallow Waters" or AlreadyRivered:
				Priority_Pyramid[0].append(land)
				#print("Reached End")

			elif land.type == "Lake":
				Priority_Pyramid[1].append(land)

			elif land.type == "Desert":
				Priority_Pyramid[2].append(land)
				#print("joined Up")

			elif not land.type == "Mountains":
				Priority_Pyramid[3].append(land)
				#Continuing

			else:
				Priority_Pyramid[4].append(land)
				
		#Selecting which land
		for level in Priority_Pyramid:
			if len(level) > 0:
				lower_land = choice(level)
				break


		if not lower_land in Priority_Pyramid[3]:
			River(higher_land,lower_land)#It Ends
		else:
			River(higher_land,lower_land)#It continues
		


		if lower_land in Priority_Pyramid[3]: #River Continues
			#print("Continuing Flow Downwards")
			RiverFlow.append(lower_land)
			flow_river_from(lower_land)


	
	shuffle(Land.List)
	for land in Land.List:

		if land.type == "Mountains":
			river_origin = land

			RiverFlow = [land]
			flow_river_from(river_origin)
	
			num -= 1

			if num <= 0:
				break

def add_random_structures(num=1):


	shuffle(Land.List)
	for land in Land.List:

		land.structure = Structure(land,"Ruins")

		num -= 1

		if num <= 0:
			break

def draw_island(size):

	#coord range
	coordrange = [0]
	for x in range(1,size+1):
		coordrange.append(x)
		coordrange.append(-x)

	#getting hexCoords
	hexCoords = []
	for x in coordrange:
		for z in coordrange:
			for y in coordrange:
				if y+x+z == 0 and not (x,y,z) in hexCoords:
					hexCoords.append((x,y,z))


					
	for coord in hexCoords:
		x = coord[0]
		y = coord[1]
		z = coord[2]

		for i in coord:
			if i in [-size,size]:
				edge = True
				break
		else:
			edge = False

		if edge:
			Land(x,y,z,"Shallow Waters")
		else:  
			random = randint(0,15)
			if random == 1:
				Land(x,y,z,"Lake")
			elif random == 2:
				Land(x,y,z,"Desert")
			elif random in [3,4,5]:
				Land(x,y,z,"Mountains")
			elif random in [6,7,8,9]:
				Land(x,y,z,"Forest")
			else:
				Land(x,y,z)


	add_rivers(5)
	add_random_structures(1)

	update_screen()
	day_passed()
		
def save_world(SaveAs=False):

	path_to_world_folder = 'Islands'+'\\'
	
	if SaveAs:
		world_file = asksaveasfile(mode='w',initialfile=World_Name,defaultextension=".wor")
	else:
		try:
			open(path_to_world_folder + World_Name + ".wor","r")
			world_file = open(path_to_world_folder + World_Name + ".wor","w")
		except FileNotFoundError:
			world_file = asksaveasfile(mode='w',initialfile=World_Name,defaultextension=".wor")

	if world_file:

		world_file.write("World"+"!"+str(World_Name)+"!"+str(day)+"!\n")
			
		for land in Land.List:
			world_file.write("Land"+"!"+str(land.hexCoords)+"!"+str(land.type)+"!"+str(land.farming_type)+"!\n")

		world_file.write("\n")

		for link in Link.List:
			world_file.write(type(link).__name__+"!"+str(link.start.hexCoords)+"!"+str(link.end.hexCoords)+"!\n")

		world_file.write("\n")

		for site in Site.List:
			world_file.write(type(site).__name__+"!"+str(site.land.hexCoords)+"!"+str(site.type)+"!"+str(site.stored_resources)+"!\n")

		world_file.close()

		error(World_Name + " Saved")
		messagebox.showinfo(World_Name + " Saved","Your world, "+World_Name+", was saved")

	else:
		error("File Not Selected")
		messagebox.showerror("File Not Selected","You have not selected a file")

def open_world():
	global World_Name
	global day

	clear_world()

	try:
		world_file = askopenfile(mode='r',defaultextension=".wor")
		path , World_Name = os.path.split(world_file.name)
	except AttributeError:
		info("No file selected")
	else:
		World_Name = World_Name[:-4]
		info(World_Name + " Loading")
		canvas.delete(ALL) # remove all items

		
		for line in world_file:
			objectinfo = line.split("!")

			if objectinfo[0] == "World":
				World_Name = objectinfo[1]
				day = int(objectinfo[2])

			elif objectinfo[0] == "Land":
				landinfo = objectinfo 
				x,y,z  = str_to_py(landinfo[1])

				land = Land(int(x),int(y),int(z),landinfo[2])
				
				if landinfo[3] == "None":
					land.farming_type = None
				else:
					land.farming_type = landinfo[3]
					
			elif objectinfo[0] in ["Road","River"]:
				linkinfo = objectinfo
				link_class = linkinfo[0]


				land_start_coords =  str_to_py(linkinfo[1])
				land_end_coords = str_to_py(linkinfo[2])


				land_start = None
				land_end = None
				for land in Land.List:
					if land.hexCoords == land_start_coords:
						land_start = land
					if land.hexCoords == land_end_coords:
						land_end = land

					if land_start and land_end:
						break


				if not land_start and not land_end:
					error("Cannot find "+str(land_start)+" or "+str(land_end))
				elif link_class == "Road" and not already_linked(land_start,land_end,Road.List):
					Road(land_start,land_end)
				elif link_class == "River":
					River(land_start,land_end)
				else:
					error("Unknown Link Class")

			elif objectinfo[0] in ["Settlement","Structure"]:
				siteinfo = objectinfo
				site_class = siteinfo[0]

				land_HexCoords = str_to_py(siteinfo[1])

				stored_resources = str_to_py(siteinfo[3])

				this_sites_land = None
				for land in Land.List:
					if land.hexCoords == land_HexCoords:
						this_sites_land = land
						break

				if site_class == "Settlement":
					settlement = Settlement(this_sites_land,siteinfo[2],stored_resources)

					this_sites_land.population = settlement.population

					this_sites_land.travelable = True

					for land in this_sites_land.find_nearby(settlement.range_of_collection) + [this_sites_land]:
						land.owned = True
						land.farming_type = "Sustainable"

				elif site_class == "Structure":
					structure = Structure(this_sites_land,siteinfo[2],stored_resources)

					this_sites_land.travelable = True

					this_sites_land.farming_type = "Sustainable"
					this_sites_land.owned = True

				else:
					error("Unknown Site Class")


			elif objectinfo[0] == "" or objectinfo[0] == "\n":
				pass


			else:
				error("Unknown Class in TextFile: "+objectinfo[0])

		update_screen()
		info(World_Name+" Loaded")

		day_passed()

def clear_world():

	canvas.delete(ALL) # remove all items

	for Class in [Land,Site,Settlement,Structure,Link,Road,River,Moveable,Trading_Cart]:
		Class.List = []

################################
###########GUI set up############
################################

def new_world_menu():
	global top
	top = Toplevel()
	top.title("New World")
	Label(top, text="New World Name:").grid()
	
	global WorldNameEntry
	WorldNameEntry = Entry(top, bd = 5)
	WorldNameEntry.grid(column=1,row=0)

	Label(top, text="New World Size:").grid(column=0)
	global WorldsizeEntry
	WorldsizeEntry = Entry(top, bd = 5)
	WorldsizeEntry.grid(column=1,row=1)
	
	B = Button(top, text ="Enter", command = create_new_custom_world)
	B.grid(row=3,columnspan=2)

	top.bind("<Return>",lambda x:create_new_custom_world())

def click(event,twoclicks=False):
	global LAST
	
	canvas.update_idletasks()
	
	if canvas.find_withtag(CURRENT): #if user has clicked object on canvas

		info("User clicked on "+str(canvas.gettags(CURRENT)))
		
		LAST = canvas.find_withtag(CURRENT) # new object is now last object
		
		canvas.update_idletasks()

		info_about = canvas.gettags(CURRENT)[0]
		
		object_class = None

		##Finding ObjectClass (and telling it has been selected)
		if info_about == "Land":

			#Find Specific Land
			for land in Land.List:
				land.selected = False
				if str(land.hexCoords) == str(canvas.gettags(CURRENT)[1]):
					object_class = land          
					object_class.selected = True 
					break

			else:
				raise KeyError("Object Class Not Found")
				
		elif info_about == "Settlement":

			for settlement in Settlement.List:
				if str(settlement.coords) == str(canvas.gettags(CURRENT)[1]):
					object_class = settlement
					break
			else:
				raise KeyError("Object Class Not Found")

		elif info_about == "Structure":
			for structure in Structure.List:
				if str(structure.coords) == str(canvas.gettags(CURRENT)[1]):
					object_class = structure
					break
			else:
				raise KeyError("Object Class Not Found")
			
		elif info_about == "Road":

			for road in Road.List:
				if str(road.midpoint) == str(canvas.gettags(CURRENT)[1]):
					object_class = road
					break
			else:
				raise KeyError("Object Class Not Found")

		elif info_about == "River":

			for river in River.List:
				if str(river.midpoint) == str(canvas.gettags(CURRENT)[1]):
					object_class = river
					break
			else:
				raise KeyError("Object Class Not Found")

		elif info_about == "Trading_Cart":

			for cart in Trading_Cart.List:
				if str(cart.location) == str(canvas.gettags(CURRENT)[1]):
					object_class = cart
					break
			else:
				raise KeyError("Object Class Not Found")

			
		else:
			object_class = None
			raise Exception("Unknown Class: "+ info_about) #we don't know what it is


		update_screen(object_class,info_about)
	
	else:
		info("User clicked")
		update_screen()

def world_str_info():

	information_string = World_Name.upper() + " STATISTICS\n"
		
	World_Resources = {}
	World_Stored_Resources = {}
		
	Total_Population = 0
	for land in Land.List:
		Total_Population += land.population
		for resource in land.resources:
			if resource in World_Resources:
				World_Resources[resource] += land.resources[resource]
			else:
				World_Resources[resource] = land.resources[resource]

				
		if land.structure:
			if land.structure.type in SETTLEMENTS:
				for resource in land.structure.stored_resources:
					if resource in World_Stored_Resources:
						World_Stored_Resources[resource] += land.structure.stored_resources[resource]
					else:
						World_Stored_Resources[resource] = land.structure.stored_resources[resource]

	
	information_string += "Total Population :" + str(Total_Population)
	
	information_string += "\nWorld Available Resources:{"
	for resource in World_Resources:
		information_string += resource.title() + ":" + str(World_Resources[resource]) + ",\t"
		
	information_string = information_string[:-2] + "} per day"

	information_string += "\nWorld Stored Resources:{"
	for resource in World_Stored_Resources:
		information_string += resource.title() + ":" + str(World_Stored_Resources[resource]) + ",\t"
		
	information_string = information_string[:-2] + "}"

	return information_string	

def update_screen(object_class=None,info_about="World"):
	global World_Name
	global information_box

	title.config(text="Map of "+ World_Name) #update name of world

	#Sort out highlighting and levels
	for land in Land.List:
		global show_owned_land
		if show_owned_land.get() and land.owned:
			land.highlight("blue")
		else:
			land.highlight(False)

	if info_about == "Land":
		object_class.highlight("red")

	for link in Link.List:
		canvas.lift(link.image)
	for site in Site.List:
		canvas.lift(site.image)

	

	##reset stuff###
	information_box.delete(0.0,END) #delete any thing in text box
	for child in actions_box.winfo_children(): #remove any buttons
			child.grid_remove() 
	

	#########Displaying info in information box#########################
	if object_class:
		information_string = object_class.get_str_info()
	else:
		information_string = world_str_info()

	information_box.insert(END,information_string) #sending information to text
	
	#########Buttons####################

	def buildbutton(structure):
		build_button = Button(actions_box,text="Build "+structure, command = lambda:object_class.build(structure),height=5, width=15)
		build_button.grid()

	def upgradebutton(structure):
		upgrade_button = Button(actions_box,text="Build "+structure, command = lambda:object_class.structure.upgrade(structure),height=5, width=15)
		upgrade_button.grid()

	def destroybutton():
		if type(object_class) == Land:
			destroy_button = Button(actions_box,text="Destroy \n"+ object_class.structure.name, command=object_class.destroy_structure,height=5, width=15)
		else: 
			destroy_button = Button(actions_box,text="Destroy \n"+object_class.name, command = object_class.destroy,height=5, width=15)
		destroy_button.grid()

	if info_about == "Land":
		
		if not object_class.structure: #if nothing there

			accessible = None
			no_nearby_settlements = True
			for land in object_class.find_nearby():
				if land.structure:
					if land.structure.type in SETTLEMENTS:
						no_nearby_settlements = False

				if not object_class.type in WATERHEXAGONS + ["Mountains"]:
					if land.travelable:
						accessible = True

			#Build Roads
			if accessible and not object_class.travelable:
				buildbutton("Road")
			

			if object_class.type not in WATERHEXAGONS + ["Mountains"]:#can build

				if no_nearby_settlements:
					buildbutton("Hamlet")

				
			if object_class.type == "Mountains": #Mines
				buildbutton("Mine")

			elif object_class.type == "Farmland":
				buildbutton("Farm")
			

		else:
				
			if object_class.structure.type == "Hamlet":
				upgradebutton("Village")
			elif object_class.structure.type == "Village":
				upgradebutton("Town")
			elif object_class.structure.type == "Town":
				upgradebutton("City")


			destroybutton()


		if object_class.type == "Plains": #Farms
			plough_button = Button(actions_box,text="Plough Farmland", command = lambda: object_class.change_type("Farmland"),height=5, width=15)
			plough_button.grid()

		if object_class.owned:
			change_f_type = Button(actions_box,text="Change\nFarming type", command = lambda:chose_farming_type_menu(object_class),height=5, width=15)
			change_f_type.grid()
			

	elif info_about == "Settlement":


		if 2 <= len(Settlement.List) and object_class.stored_resources:
			move_resources_Button = Button(actions_box,text="Move Resources", command = lambda:move_resources_menu(object_class),height=5, width=15)
			move_resources_Button.grid()
		

		if not "Mill" in object_class.special_buildings:
			buildbutton("Mill")
			
		near_mountains = False
		near_water = False
		for land in object_class.land.find_nearby():
			if land.type == "Mountains":
				near_mountains = True

			if land.type in WATERHEXAGONS:
				near_water = True


		if near_mountains:
			if not "Forge" in object_class.special_buildings:
				buildbutton("Forge")
			
		if near_water:
			if not "Port" in object_class.special_buildings:
				buildbutton("Port")
			
			elif not "Shipyard" in object_class.special_buildings: #elif is correct
				buildbutton("Shipyard")

		destroybutton()

		 
	
	elif info_about == "World":
		
		collect_taxes_button = Button(actions_box,text="Collect \nEmergency Taxes", command=collect_world_taxes,height=5, width=15)
		collect_taxes_button.grid()


	elif info_about == "Road":

		destroybutton()

	elif info_about == "River":
	
		if not object_class.start in ["Mountains"] + WATERHEXAGONS: #add must be owned later and price
			dam_button = Button(actions_box,text="Dam River", command=object_class.dam ,height=5, width=15)
			dam_button.grid() 
		

	elif info_about == "Structure":

		destroybutton()

	elif info_about == "Trading_Cart":

		pass
		

	else:
		raise Exception("What is this information about?",info_about) #we don't know what it is
	
def Start_Tutorial():
	TutorialGuide = Toplevel()
	TutorialGuide.title("Tutorial")
	Label(TutorialGuide,text="Tutorial Guide").grid(columnspan=2)

	TutorialTexts = ["Introduction\nWelcome to the Island\nYour objective is to colonize the island and rule it as you see fit.\nYou colonize the island by building towns and cities and gathering resources\n[Click on the arrow button to continue]",
	"Conflict\nYou can play the game peacefully or attack other players.\nAs you go along with the game you will face numerous problems which you have to decide how to deal with.\n[Click on the arrow button to continue]",
	"The GUI\nThe main screen shows your world map\nBelow that is the information box\nTo the right hand side is the action box where you choose actions\nThe bottom right displays the day you are on.",
	"Building Settlements\nFirst of all click on one of the light green hexagonal tiles\nA few buttons should pop up in the action box\nClick on the Build Hamlet box\nYou should notice a letter appear on the hexagon",
	"The End of the Tutorial\nThis is the end of the tutorial\nWe hope it has given you a basic idea of how to play the game\nFor more complex game mechanic's and info see the wiki page\n[Click the exit button to exit]"]

	global page
	page = 0
	
	TutorialTextbox = Text(TutorialGuide,width=35,height=10,wrap=WORD)
	TutorialTextbox.grid(columnspan=2)

	def changepage(change):
		global page
		page += change

		TutorialTextbox.delete(0.0,END)
		TutorialTextbox.insert(END,TutorialTexts[page])

		TutorialTextbox.tag_add("Title", "1.0", "2.0")
		TutorialTextbox.tag_config("Title",font=("Georgia", "12", "bold"))
	
		if page == 0:                       #Start
			pagebackward.config(text="Exit",command=TutorialGuide.destroy)
			pageforward.config(text="--->",command=lambda:changepage(1))

		elif page == len(TutorialTexts) - 1: #End
			pagebackward.config(text="<---",command=lambda:changepage(-1))
			pageforward.config(text="Exit",command=TutorialGuide.destroy)
		else:                               #Middle
			pagebackward.config(text="<---",command=lambda:changepage(-1))
			pageforward.config(text="--->",command=lambda:changepage(1))


		

			
	
	
	TutorialTextbox.insert(END,TutorialTexts[page])
	
	pagebackward = Button(TutorialGuide,text="<---",command=lambda:changepage(-1))
	pagebackward.grid(row=2,column=0,sticky="E")
	pageforward = Button(TutorialGuide,text="--->",command=lambda:changepage(1))
	pageforward.grid(row=2,column=1,sticky="W")

	changepage(0)

	TutorialGuide.mainloop()

def exit_and_save():
	save_world()
	root.destroy()

######GUI###################    
root = Tk()

show_owned_land = BooleanVar(root)
show_owned_land.set(False)

root.wm_title("Island")

########Canvas Map###########
title = Label(root,text="Map of "+ World_Name)
title.grid(column=0,row=0)
canvas_frame = Frame(root).grid()#frame
canvas = Canvas(canvas_frame, bg="light blue", height=550, width=600) #canvas
canvas.grid(column=0,row=1)

## Bindings ##
canvas.bind("<Button-1>", click)
#canvas.bind("<Double-Button-1>",lambda x: click("hi",two_clicks=True))


#####Information Box############
information_box = Text(root, height=5, width=75,wrap="word")
information_box.grid(column=0,row=2)#information box

########Actions box############
global actions_box
Label(root,text="Actions").grid(column=1,row=0)
actions_box = Frame(root, height=65, width=15,relief=SUNKEN,borderwidth=1)
actions_box.grid(column=1,row=1,sticky="NESW")

#######Time display######
Day_Display = Label(root,text="Day " + str(day))
Day_Display.grid(column=1,row=2,sticky="NW",pady=2,padx=2)

########Menu########
menubar = Menu(root)
filemenu = Menu(menubar,tearoff=0)
filemenu.add_command(label="New", command=new_world_menu)
filemenu.add_command(label="Open", command=open_world)
filemenu.add_command(label="Save", command=lambda:save_world(SaveAs=False))
filemenu.add_command(label="Save as...", command= lambda:save_world(SaveAs=True))
filemenu.add_separator()
filemenu.add_command(label="Exit and Save", command=exit_and_save)
filemenu.add_command(label="Just Exit", command=root.destroy)
menubar.add_cascade(label="File", menu=filemenu)

Display = Menu(menubar,tearoff=0)
Display.add_checkbutton(label="Show Territory", command=lambda:update_screen(object_class=None,info_about="World"),variable=show_owned_land,onvalue=True, offvalue=False)
menubar.add_cascade(label="Display", menu=Display)

helpmenu = Menu(menubar,tearoff=0)
helpmenu.add_command(label="About...",command= lambda:messagebox.showinfo("About", "\tCredits:\nProgrammer: Ben P.S Grant\nArtist: Ben P.S Grant\nGame Testers: Patrick K.G Grant and Emilia M.S Grant\nEnglish Translator: Juliet J.S Grant"))
helpmenu.add_command(label="Tutorial",command=Start_Tutorial)
menubar.add_cascade(label="Help", menu=helpmenu)

root.config(menu=menubar)

######Title Screen##########

random_island_button = Button(actions_box,text="Create New Island", command = lambda: draw_island(6),height=5, width=15)
random_island_button.grid()

open_island_button = Button(actions_box,text="Open Saved Island", command = lambda: open_world(),height=5, width=15)
open_island_button.grid()

#main
root.mainloop()
