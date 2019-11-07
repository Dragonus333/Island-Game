from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import *

from math import *
from random import randint
from itertools import product


import os
###############################

from logging import *
basicConfig(level=DEBUG,format="%(levelname)s - %(message)s")

disable(INFO)#toggle this for developer mode and user
##############################

SETTLEMENTS = ["Hamlet","Village","Town","City"]
WATERHEXAGONS = ["Lake","Shallow Waters"]

LAST = False

Done = False

Lands = {}
Structures = {}

global World_Name
World_Name = "Island"
day = 0

def day_passed():
    global day
    day += 1 #day changes
    Day_Display.config(text="Day " + str(day)) #############
    info("Day " +str(day)+":") #############

    global Lands
    for land in Lands:        #search all lands
        if str(land.structure) in SETTLEMENTS:    #if land has building on it
            land.structure.collect_resources()
            land.structure.feed_inhabitants()
            land.structure.manufacture()

            if day % 30 == 0:
                land.structure.collect_taxes()

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
            raise Exception("Unknown farming type",land.farmingtype)

    for cart in Trading_Cart.S:

        cart.next()
   
    update_screen()
    root.after(10000,day_passed)

#######Classes########

class Land():
    """A hexagon tile"""
    def __init__(self,x,y,z,type_="Plains",structure=None):
        
        self.hexCoords = (x,y,z)    #hex coordinates
        Lands[self] = self.hexCoords #send to list of lands

        self.selected = False

        self.owned = False
        self.travelable = False
        self.farming_type = None

        
        #Getting normal x and y coords [Don't mess,this took me ages to find]
        size_of_gaps = 40
        self.x  = (size_of_gaps * x * 3/4) + 300
        self.y = -(sqrt(3)/2  * size_of_gaps *( x/2 + y )) + 250
        

        self.type = type_ # set land type
        self.structure = structure #any structures on the land
        
        self.calculate_base_resources()

        if not self.type in WATERHEXAGONS:
            self.population = randint(1,5)
        else:
            self.population = 0

        self.draw()
        if type(self.structure) == str:
            self.build(structure)
        else:
            self.structure = None

    def draw(self):

        ########Deciding colours of the hexagon###########
        if self.type == "Plains" or self.type == "Farmland":
             colour = ("black", "chartreuse4")
        elif self.type == "Forest":
            colour = ("black", "forest green")
        elif self.type == "Jungle":
            colour = ("black", "dark green") 
        elif self.type == "Mountains":
            colour = ("black", "gray")
        elif self.type == "Lake":
            colour =  ("black", "powder blue")
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
        self.image = canvas.create_polygon(hex_corner_hexCoords,fill=colour[1],outline=colour[0],tags=[str(self.hexCoords)])

    def build(self,building="Hamlet"):
        
        if building == "Road":   #Roads
            Land_found = False
            
            for land in self.find_nearby():
                
                if str(land.structure) in SETTLEMENTS + ["Road"]: #if can connect to somewhere
                    self.structure = Road(self,land)
                    Land_found = True

            if Land_found == False:
                if Done:
                    messagebox.showerror("Road Error", "Needs somewhere to connect to")
            else:
                info("Built " + building) 
                self.structure = "Road" # Build <-------------------------
                self.owned = True
                self.travelable = True
                self.farming_type = "Sustainable"

        else:          #not Roads
            info("Built " + building)
            
            
            if not building == "Mine":
                self.structure = Settlement(self,building) #Build <-------------------------
                self.population = self.structure.population
                self.farming_type = "Sustainable"
                self.owned = True
            else:  
                self.structure = "Mine"
                self.farming_type = "Sustainable"
                self.owned = True


            try:
                for land in self.find_nearby(self.structure.range_of_collection):
                    land.owned = True
                    land.farming_type = "Sustainable"
                    self.travelable = True
            except:
                pass

            for land in self.find_nearby():
                if str(land.structure) in ["Road"] + SETTLEMENTS: #if can connect to somewhere
                    Road(self,land)
                    #root.update_idletasks()


        
        
        if self.structure == "Mine":
             self.resources["stone"] += 80 +randint(-10,10)
             self.resources["iron"] = 50 +randint(-10,10)
             self.resources["copper"] = 70 +randint(-10,10)


        if not building == "Road":
            canvas.create_text((self.x,self.y),text=str(self.structure).upper()[0],tags=["letter "+str(self.x+self.y)],font="Verdana 10 bold")
            Structures["letter "+str(self.x+self.y)] = self.structure

        if not self.structure in ["Road","Mine"]:
            update_screen(self.structure,"Settlement")
        else:
            update_screen(self,info_about="Land")

    def destroy(self):

        
        if not self.structure == "Road":
            canvas.delete(self.image)
        
        
        for x in range(6):
            try:
                canvas.delete(canvas.find_withtag("Road "+str(self.x+self.y))[0]) #fix this
            except:
                break

       
        if self.structure == "Hamlet":
            self.population = 1
        elif self.structure == "Village":
            self.population = 2
        elif self.structure == "Town":
            self.population = 5
        elif self.structure == "City":
            self.population = 10
        
        
        info("Destroyed " + str(self.structure))#destroy
        self.structure = None
        self.owned = False
        self.travelable = False
        
        if not self.structure in [None,"Road","Mine"]:
            for land in self.find_nearby(self.structure.range_of_collection):
                land.owned = False
                land.farming_type = None

        update_screen(self,"Land")


    def find_nearby(self,Range=1):
        
        nearbyhexcoords = [(+1, -1,  0),(+1,  0, -1),(+1,  0, -1),( 0, +1, -1),(-1, +1,  0),(-1,  0, +1),( 0, -1, +1)]
        self.nearbyLands = []

        
        for coords in nearbyhexcoords:
            other_land_coord = []
            for i in range(0,3):
                other_land_coord.append(self.hexCoords[i] + coords[i])
            

            #finding proper land
            for land in Lands:
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

        if self.structure and not self.structure == "Road":
            canvas.create_text((self.x,self.y),text=str(self.structure).upper()[0],tags=["letter "+str(self.x+self.y)],font="Verdana 10 bold")
        elif self.structure == "Road":
            self.structure == None
            self.travelable = False
            self.owned = False

        if self.type == "Farmland":
            canvas.create_text((self.x,self.y),text="F"[0],tags=["letter "+str(self.x+self.y)])
        
    
        update_screen(self,"Land")

    def highlight_toggle(self,highlight_toggle=True,colour="blue"):
        if highlight_toggle:
            canvas.itemconfig(canvas.find_withtag(self),outline=colour)
        else:
            canvas.itemconfig(canvas.find_withtag(self)[0],outline=self.colour[0])

    def __str__(self):
        return str(self.hexCoords)

class Settlement():
    """A settlement on the map"""

    def __init__(self,land,type="Hamlet"):

        self.land = land
        self.type = type
        self.population = land.population
        self.stored_resources = {}
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

        

        #############Different Naming ##########|||||Only Half Works
        SurroundingLandtypes = {}
        for land in self.land.find_nearby():
            if land.type in SurroundingLandtypes:
                SurroundingLandtypes[land.type] =+ 1
            else:
                SurroundingLandtypes[land.type] = 1


        if max(SurroundingLandtypes, key=lambda k: SurroundingLandtypes[k]) == "Mountains":
            self.name = "Mining " + self.type
        if max(SurroundingLandtypes, key=lambda k: SurroundingLandtypes[k]) in WATERHEXAGONS:
            self.name = "Fishing " + self.type 
        else:
            self.name = self.type

    def bulid(self,building):
        try:
            if building == "Mill":
                self.remove_resources({"wood":20,"stone":5})
            elif building == "Forge":
                self.remove_resources({"wood":15,"stone":10})
            elif building == "Port":
                self.send_resources({"wood":45})
            elif building == "Shipyard":
                self.send_resources({"wood":60})
        except:
            info("Not enough resources to add "+ building +" to "+str(self))
        else:
            info(building+" added")
            self.special_buildings.append(building)

            update_screen(self,"Settlement")

    def upgrade(self,building):
        try:
            if building == "Village":
                self.remove_resources({"wood":40})
            elif building == "Town":
                self.remove_resources({"wood":80,"stone":50})
            elif building == "City":
                self.remove_resources({"wood":120,"stone":80})
        except:
            info("Not enough upgrade to bulid "+ building)
        else:
            info("Upgrading " + str(self) + " to " + str(building))
            self.type = building
            self.land.structure = self

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
                    

            canvas.delete(canvas.find_withtag("letter "+ str(self.land.x+self.land.y)))
            canvas.create_text((self.land.x,self.land.y),text=self.type[0],tags=["letter "+str(self.land.x+self.land.y)],font="Verdana 10 bold")
            
            
            self.land.population = self.population

            for land in self.land.find_nearby(self.range_of_collection):
                land.owned = True

            self.name = self.type

            update_screen(self,"Settlement")
                
    def destroy(self):
        canvas.delete(canvas.find_withtag("letter "+ str(self.land.x+self.land.y)))
        
        if self.type == "Hamlet":
            self.population = 1
        elif self.type == "Village":
            self.population = 2
        elif self.type == "Town":
            self.population = 5
        elif self.type == "City":
            self.population = 10
        
        
        info("Destroyed " + str(self.type))#destroy
        self.land.structure = None
        self.land.owned = False
        self.land.population = self.population
        self.land.travelable = False

        for land in self.land.find_nearby(self.range_of_collection):
            land.owned = False
            land.farming_type = None

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

    def remove_resources(self,resources,send_error=True):#send error sends an error message to the user

        enought_resources = True#set true
        #removing resources
        for item in resources:
            if item in self.stored_resources: #if we have resource
                if 0 < self.stored_resources[item] - resources[item]:#if we have enough of the resource
                    if enought_resources: #if resource is still true #
                        enought_resources = True #set true           # We dont actually need this code but it exolains iself better so....
                else:
                    ##we dont have that resource
                    if send_error:
                        messagebox.showerror("Not enough "+item+"s", "You need "+str(resources[item] - self.stored_resources[item])+" more "+item)
                    enought_resources = False
                    
            else:
                if send_error:
                    messagebox.showerror("No "+item, "You need "+str(resources[item])+" "+item)
                enought_resources = False
                
        if enought_resources == False: #if not enough resouces
            raise Not_Enough_Resources("Not Enough Resources",resources) #raise error to be caught when function not correctly exicuted
        else:
            for item in resources:
                self.stored_resources[item] -= resources[item]   #remove resources

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
                print("Error")
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

            newCart = Trading_Cart(path,resources,to)

            
                    

        
    def highlight_toggle(self,highlight_toggle=True,colour="blue"):
        if highlight_toggle:
            canvas.itemconfig(canvas.find_withtag(self),outline=colour)
        else:
            canvas.itemconfig(canvas.find_withtag(self),outline="black")

    



    def __str__(self):
        return self.type


class Link():

    def __init__(self,start_land,end_land):

        self.start = start_land

        self.end = end_land

        self.image = self.draw()


    def draw(self):

        self.image = None

        return image

class Road(Link):

    def draw(self):

        self.image = canvas.create_line(self.start.x,self.start.y,self.end.x,self.end.y,fill="black",dash=(1,4),tags=["Road "+str(self.end.x+self.end.y)])

        return self.image

class River(Link):

    def draw(self):

        self.image = canvas.create_line(self.start.x,self.start.y,self.end.x,self.end.y,fill="blue",tags=["River "+str(self.end.x+self.end.y)])

        return self.image


class Trading_Cart():

    S = []

    def __init__(self,path,resources,to):

        self.path = path

        self.to = to

        self.resources = resources

        self.stage_of_journey = 0

        self.location = path[self.stage_of_journey]

        self.draw()

        self.S.append(self)

    def draw(self):

        x,y,z = self.location

        size_of_gaps = 40
        self.x  = (size_of_gaps * x * 3/4) + 300
        self.y = -(sqrt(3)/2  * size_of_gaps *( x/2 + y )) + 250

        self.Image = canvas.create_text((self.x,self.y),text="&-m",tags=["cart "+str(self.location)],font="Verdana 10 bold")

    def delete(self):

        canvas.delete(canvas.find_withtag("cart "+str(self.location)))

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
        
        
        

def collect_world_taxes():
    print("Taxes Collected")
    global Lands
    for land in Lands:
        if str(land.structure) in SETTLEMENTS:    #if land has building on it
            land.structure.collect_taxes(25) # remove this

def get_object_from_(canvas_object):

    found_object = None
    
    for land in Lands:
        if len(canvas.gettags(CURRENT)) > 1:
            if str(land.hexCoords) == str(canvas.gettags(CURRENT)[0]):
                found_object = land        ##Its a land##
                break
        else:
            pass
    else:
        for structure in Structures:
            if str(structure) == str(canvas.gettags(CURRENT)[0]):
                found_object = Structures[structure]
                break

        else:

            if not canvas.gettags(CURRENT):
                found_object = False #we didn't click anything
            elif str(canvas.gettags(CURRENT)[0][:4]) == "Road":
                found_object = land ##Its a Road##
            else:
                raise Exception("Unknown Class") #we don't know what it is


    return found_object

#####GUIs####

def move_resources_menu(settlement):
    ####Titles####
    top = Toplevel(root,width=20,height=20) ; top.title("Moving Resources")
    Label(top,text="Moving Resources:",font=("Georgia", "12", "bold")).grid(columnspan=2)

    ###Finding Settlemnets###
    Structures = {}
    for land in Lands:
        if not land.structure in [None,"Road","Mine"]:
            if land.structure.type in SETTLEMENTS  and not land.structure == settlement:
                Structures[str(land.structure) +" at "+str(land.hexCoords)] = land.structure

    Label(top,text=" From:                            To:").grid(row=1,column=0)
    
    ##From##
    Label(top,text=settlement.name+" at "+str(settlement.land.hexCoords)+ "   to ").grid(row=2,column=0)
    
    ##To##
    
    other_settlement = StringVar()
    other_settlement.set("send to")


    drop = OptionMenu(top,other_settlement,*Structures)
    drop.grid(row=2,column=1)

    
    ###Resorces###
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
    def send_resources(settlement,resources,to):
        if not to == "send to":
            settlement.send_resources(resources,Structures[to])
        top.destroy()

    
    Button(top,text="Done",command=lambda:send_resources(settlement,{resource.get():number_of_resource.get()},to=other_settlement.get())).grid(columnspan=2)

def chose_farming_type_menu(land):
    top = Toplevel(root,width=20,height=20) ; top.title("Pick Farming Type")
    Label(top,text="Pick Farming Type:").grid()

    FARMING_TYPES = ["Unsustainable","Sustainable","Growth",None]

    v = StringVar()
    v.set(land.farming_type)

    def change_type(land,type_):
        land.farming_type = type_
        update_screen(object_class=land,info_about="Land")
        top.destroy()

    for type_ in FARMING_TYPES:
        Radiobutton(top,text=str(type_),padx = 20, variable=v,value=type_).grid()


    Button(top,text="Enter",command=lambda:change_type(land,v.get())).grid()
    
########################Creating,Saving and opening worlds#######################
def create_new_world():
    global World_Name

    World_Size = 5
    
    if WorldNameEntry.get() == "":
        World_Name = "Temp World"
    else:
        World_Name = WorldNameEntry.get()
        
    if WorldsizeEntry.get() == "":
        World_Size = 5
    else: 
        World_Size = int(round(float(WorldsizeEntry.get()))) + 1
        
    top.destroy()
    canvas.delete(ALL) # remove all items
    
    draw_island(World_Size)

    update_screen()
    

def draw_island(size):
    global Lands ,Structures
    Lands = {} #list of lands that make up the island
    Structures = {}
    
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


    update_screen()
    day_passed()

    global Done
    Done = True
        
def save_world(save_mode="save"):

    path_to_world_folder = 'Islands'+'\\'
    
    if save_mode == "saveAs":
        world_file = asksaveasfile(mode='w',initialfile=World_Name,defaultextension=".wor")   
    else:
        try:
            world_file = open(path_to_world_folder + World_Name + ".wor","w")
        except FileNotFoundError:
            world_file = asksaveasfile(mode='w',initialfile=World_Name,defaultextension=".wor")
            
    for land in Lands:
        world_file.write(str(land.hexCoords)+"!"+str(land.type)+"!"+str(land.structure)+"!\n")
        
    world_file.close()


def open_world():
    global World_Name,Lands ,Structures
    Lands = {} #list of lands that make up the island
    Structures = {}

    global Done
    Done = False

    try:
        world_file = askopenfile(mode='r',defaultextension=".wor")
        path , World_Name = os.path.split(world_file.name)
    except AttributeError:
        info("No file selected")
    else:
        World_Name = World_Name[:-4]
        info(World_Name + "Loading")
        canvas.delete(ALL) # remove all items
        
        for line in world_file:
            landinfo = line.split("!")
            x,y,z  = tuple(landinfo[0][1:-1].split(","))
            
            if landinfo[2] == "None":
                Land(int(x),int(y),int(z),landinfo[1],bool(landinfo[2]))
            else:
                Land(int(x),int(y),int(z),landinfo[1],landinfo[2])
                

        update_screen()
        info(World_Name+" Loaded")

        day_passed()
        

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
    
    B = Button(top, text ="Enter", command = create_new_world)
    B.grid(row=3,columnspan=2)

    top.bind("<Return>",lambda x:create_new_world())

def click(event,twoclicks=False):
    global LAST

    #Sort out highlighting
    for land in Lands:
        global show_owned_land
        if show_owned_land.get() and land.owned:
            land.highlight_toggle()
        else:
            land.highlight_toggle(False)
    
    canvas.update_idletasks()
    
    if canvas.find_withtag(CURRENT): #if user has clicked object on canvas

        info("User clicked on "+canvas.gettags(CURRENT)[0])

        
        LAST = canvas.find_withtag(CURRENT) # new object is now last object
        

        try:
            canvas.itemconfig(CURRENT, outline="red") #if object is a shape
            

        except TclError:
            pass #its a letter so it refers to a settlement or Mine
        

        canvas.update_idletasks()

            
        for land in Lands:
            land.selected = False
            if str(land.hexCoords) == str(canvas.gettags(CURRENT)[0]):
                object_class = land          ##############
                info_about = "Land"          ##Its a land##
                object_class.selected = True ##############
                break               
        else:
            for structure in Structures:
                if str(structure) == str(canvas.gettags(CURRENT)[0]):
                    object_class = Structures[structure]
                    try:
                        object_class.type
                    except:
                        info_about = "Other Structure" ##Its not a Settlement##
                        break
                    else:
                        info_about = "Settlement" ##Its a Settlement##
                        break

            else:
                if str(canvas.gettags(CURRENT)[0][:4]) == "Road":
                    object_class = land
                    info_about = "Road" ##Its a Road##
                else:
                    pass
                    #raise Exception("Unknown Class") #we don't know what it is



                
        
        update_screen(object_class,info_about)

        

        
    else:
        info("User clicked")
        update_screen()

def update_screen(object_class=None,info_about="World"):
    global World_Name
    global information_box

    #reset stuff
    information_box.delete(0.0,END) #delete any thing in text box
    for child in actions_box.winfo_children(): #remove any buttons
            child.grid_remove() 
    
    title.config(text="Map of "+ World_Name) #update name of world

    
    if info_about == "Land":



        #########Displaying info#########################

        #stringing coords
        str_coods = str([int(object_class.x),int(object_class.y)])

        #stringing resources
        str_resources = ""
        for resource in object_class.resources:
            str_resources += resource.title() + ":" + str(object_class.resources[resource]) + ",\t"


        #land information
        information_string =  "Type: " + object_class.type
        try:
            information_string += "\t| Structure: " +  str(object_class.structure.name)
        except:
            information_string += "\t| Structure: " +  str(object_class.structure)
        information_string += "\nHex Coords: " +  str(Lands[object_class])
        information_string += "\t| Coords: " + str_coods
        information_string += "\nPopulation:" + str(object_class.population)
        information_string += "\t| Owned: " + str(object_class.owned)
        information_string += "\t| Farming: " + str(object_class.farming_type)
        information_string += "\t| Travelable: " + str(object_class.travelable)
        information_string += "\nResources:{" + str_resources
        
        information_string = information_string[:-2] + "} per day\n\n\n"
        
        information_box.insert(END,information_string) #sending information to text
        
        #########Buttons####################
        if object_class.owned:
            change_f_type = Button(actions_box,text="Change\nFarming type", command = lambda:chose_farming_type_menu(object_class),height=5, width=15)
            change_f_type.grid()

        
        if not object_class.structure: #if nothing there

            if object_class.type == "Plains":#villages
                no_nearby_settlements = True
                for land in object_class.find_nearby():
                    try:
                        if land.structure.type in SETTLEMENTS:
                            no_nearby_settlements = False
                    except:
                        pass
                if no_nearby_settlements:
                    build_button = Button(actions_box,text="Build Hamlet", command = lambda:object_class.build("Hamlet"),height=5, width=15)
                    build_button.grid()
                
                if object_class.type == "Plains": #Farms
                    build_button = Button(actions_box,text="Plough Farmland", command = lambda: object_class.change_type("Farmland"),height=5, width=15)
                    build_button.grid()

                
            if object_class.type == "Mountains": #Mines
                build_button = Button(actions_box,text="Build Mine", command = lambda:object_class.build("Mine"),height=5, width=15)
                build_button.grid()
                

            #road
            bulidroad = None
            
            if not object_class.type in WATERHEXAGONS + ["Mountains"]: #Roads
                for land in object_class.find_nearby():
                    if str(land.structure) in SETTLEMENTS + ["Road"]:
                        bulidroad = True
                        break
                else:
                    bulidroad = False
                    
            if bulidroad and not object_class.structure == "Road":
                build_button = Button(actions_box,text="Build Road", command = lambda:object_class.build("Road"),height=5, width=15)
                build_button.grid()

        else:
            
            def Upgradebutton(structure):
                upgrade_button = Button(actions_box,text="Build "+structure, command = lambda:object_class.structure.upgrade(structure),height=5, width=15)
                upgrade_button.grid()
        
            
            try:
                structure_type = object_class.structure.type
            except:
                structure_type = object_class.structure
           
            
                
            if structure_type == "Hamlet":
                Upgradebutton("Village")
            elif structure_type == "Village":
                Upgradebutton("Town")
            elif structure_type == "Town":
                Upgradebutton("City")

            try:
                destroy_button = Button(actions_box,text="Destroy "+ structure_type, command =object_class.structure.destroy,height=5, width=15)
            except:
                destroy_button = Button(actions_box,text="Destroy "+ structure_type, command =object_class.destroy,height=5, width=15)
                
            destroy_button.grid()
            
                



    elif info_about == "Settlement":
        

        #stringing resources
        str_resources = ""
        for resource in object_class.stored_resources:
            str_resources += resource.title() + ":" + str(object_class.stored_resources[resource]) + ",\t"


        #land information
        information_string =  "Name: " + object_class.name
        information_string +=  "\t| Type: " + object_class.type
        information_string += "\nPopulation: " + str(object_class.population)
        information_string += "\t| Houses: " + str(object_class.number_of_houses)
        information_string += "\t| Specialized buildings: " + str(object_class.special_buildings)
        information_string += "\nStored Resources:{" + str_resources
        information_string = information_string[:-2] + "}\n\n\n"
        information_string += "\nPopulation Mood: " + object_class.population_feeling
        
        
        
        
        information_box.insert(END,information_string) #sending information to text

        #Buttons
        number_of_settlements = 0
        for land in Lands:
            try:
                structure_type = land.structure.type
            except:
                 structure_type = land.structure
                
            if structure_type:
                if structure_type in SETTLEMENTS:
                    number_of_settlements += 1
        

                

        if 1 < number_of_settlements and object_class.stored_resources:
            move_resources_Button = Button(actions_box,text="Move Resources", command = lambda:move_resources_menu(object_class),height=5, width=15)
            move_resources_Button.grid()
        
        def buildbutton(structure):
            build_button = Button(actions_box,text="Build "+structure, command = lambda:object_class.bulid(structure),height=5, width=15)
            build_button.grid()
            
        

        if not "Mill" in object_class.special_buildings:
            buildbutton("Mill")
            
        for land in object_class.land.find_nearby():
            if land.type == "Mountains":
                near_mountains = True
                break
        else:
            near_mountains = False
        if near_mountains:
            if not "Forge" in object_class.special_buildings:
                buildbutton("Forge")


        for land in object_class.land.find_nearby():
            if land.type in WATERHEXAGONS:
                near_water = True
                break
        else:
            near_water = False
            
        if near_water:
            if not "Port" in object_class.special_buildings:
                buildbutton("Port")
            
            elif not "Shipyard" in object_class.special_buildings: #elif is correct
                buildbutton("Shipyard")
                
        

         
    
    elif info_about == "World":

        information_string = World_Name.upper() + " STATISTICS\n"
        
        World_Resources = {}
        World_Stored_Resources = {}
            
        Total_Population = 0
        for land in Lands:
            Total_Population += land.population
            for resource in land.resources:
                if resource in World_Resources:
                    World_Resources[resource] += land.resources[resource]
                else:
                    World_Resources[resource] = land.resources[resource]

                    
            if land.structure:
                if not land.structure in ["Road","Mine"]:
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



        
        collect_taxes_button = Button(actions_box,text="Collect \nEmergency Taxes", command=collect_world_taxes,height=5, width=15)
        collect_taxes_button.grid()


    elif info_about == "Road":
        information_string = "You clicked on a road"

    elif info_about == "Other Structure":
        information_string = "You clicked on a structure that isn't a settlement (Mine)"
        

    else:
        raise Exception("What is this infomation about?",info_about) #we don't know what it is
    

    information_box.insert(END,information_string)
    

def Start_Tutorial():
    TutorialGuide = Toplevel()
    TutorialGuide.title("Tutorial")
    Label(TutorialGuide,text="Tutorial Guide").grid(columnspan=2)

    TutorialTexts = ["Introduction\nWelcome to the Island\nYour objective is to colonize the island and rule it as you see fit.\nYou colonize the island by building towns and cities and gathering resources\n[Click on the arrow button to continue]",
    "Conflict\nYou can play the game peacefully or attack other players.\nAs you go along with the game you will face numerous problems which you have to decide how to deal with.\n[Click on the arrow button to continue]",
    "The GUI\nThe main screen shows your world map\nBelow that is the information box\nTo the right hand side is the action box where you choose actions\nThe bottom right displays the day you are on.",
    "building Settlements\nFirst of all click on one of the light green hexagonal tiles\nA few buttons should pop up in the action box\nClick on the Build Hamlet box\nYou should notice a letter appear on the hexagon",
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
filemenu.add_command(label="Save", command=save_world)
filemenu.add_command(label="Save as...", command= lambda:save_world("saveAs"))
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
#root.mainloop()
