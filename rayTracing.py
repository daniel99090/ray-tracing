###############################################################################
## This program uses ray tracing to show three relective spheres and a 
## relective checkerboard plane. 
###############################################################################

import math
from tkinter import *

canvasWidth = 700
canvasHeight = 500
d = 500
centerOfProjection = [0,0,-d]
Ia = .2 # intensity of ambient light
Ip = .8 # intensity of point light
Kd = .5 # constant of diffuse reflectivity
Ks = .5 # constant of specular reflectivity
specIndex = 8 # specular index
V = [0, 0,-1] # view vector, left hand viewing system
skyColor = [135,207,235]
pointLight = [500,500,0]
depthLimit = 4

# Parent class for every object
class Figure:
    def __init__(self):
        pass
    
    # Function to get the vector from a pointLight to the current intersectionPoint
    def getLightRay(self, pointLight):
        return normalize([pointLight[i]-self.intersectionPoint[i] for i in range(3)])
    
    # Function to determine whether the current intersection point is in a shadow
    def inShadow(self):
        lightRay = self.getLightRay(pointLight)

        # test every object in scene (other than this object)
        for obj in scene:
            if self == obj:
                continue
            if obj.intersect(self.intersectionPoint, lightRay) != [] and obj.t < self.t:
                return True
        
        return False


# Class defining a sphere
class Sphere(Figure):
    def __init__(self, center, radius, reflectWeight, localColor):
        self.center = center
        self.radius = radius
        self.localColor = localColor
        self.t = 99999
        self.intersectionPoint = []
        self.reflectWeight = reflectWeight
        self.localWeight = 1 - reflectWeight

    # function to determine some ray from some starting point intersects this shpere.
    def intersect(self, point, ray):
        a = sum([x*x for x in ray])
        b = 2*sum([ray[i]*(point[i]-self.center[i]) for i in range(3)])
        c = sum([x*x for x in (self.center + point)]) - 2 * dotProduct(self.center, point) - self.radius ** 2

        d = b**2 - 4 * a * c # determinant

        # determinant < 0 => no intersection
        if d < 0:
            return []
        
        d = math.sqrt(d)
        self.t = min(max((-b + d)/(2*a),0), max((-b - d)/(2*a),0))

        # do not consider intersection behind the viewer
        if self.t <= 0:
            return []

        intersectionPoint = [point[i]+self.t*ray[i] for i in range(3)]

        # dont consider intersections beyond a certain point
        if intersectionPoint[2] < -500:
            return []

        self.intersectionPoint = intersectionPoint
        self.normal = normalize([self.intersectionPoint[i] - self.center[i] for i in range(3)])
        self.phongIntensity = getIntensity(self.normal, self.getLightRay(pointLight))
        self.reflect = getReflectionVector(self.normal, ray)

        return intersectionPoint

# Class defining a plane
class Plane(Figure):
    def __init__(self, point, normal, reflectWeight):
        self.point = point
        self.normal = normal
        self.t = 99999
        self.intersectionPoint = []
        self.reflectWeight = reflectWeight
        self.localWeight = 1 - reflectWeight
    
    # function to determine some ray from some starting point intersects this plane.
    def intersect(self, point, ray):
        d = dotProduct(self.normal, ray)

        if abs(d) < .001: # no intersection
            return []
        
        numerator = dotProduct(self.normal, self.point) - dotProduct(self.normal, point)

        self.t = numerator/d

        if self.t < 0:
            return []

        intersectionPoint = [point[i]+self.t*ray[i] for i in range(3)]

        # dont consider intersections beyond a certain point
        if intersectionPoint[2] < -500:
            return []

        self.intersectionPoint = intersectionPoint
        self.phongIntensity = getIntensity(self.normal, self.getLightRay(pointLight))

        self.getColorFromIntersection(intersectionPoint)

        self.reflect = getReflectionVector(self.normal, ray)

        return intersectionPoint
    
    # function to determine the local color of the checkerboard given some point
    def getColorFromIntersection(self, point):
        colors = [[255,0,0], [255,255,255]]
        index = 0
        if point[0] >= 0: index = (index+1)&1
        if point[2] >= 0: index = (index+1)&1
        if (abs(point[0]) % 200) > 100: index = (index+1)&1
        if (abs(point[2]) % 200) > 100: index = (index+1)&1
        
        self.localColor = colors[index]


# this function normalizes a vector
def normalize(v):
    magnitude = math.sqrt(sum([x**2 for x in v]))
    v = [val/magnitude for val in v]
    return v

# Function to get the dot product between two vectors
def dotProduct(v1,v2):
    return sum(x*y for x,y in zip(v1,v2))

# gets the full RGB color code given the intentities for R,G, and B
def getRGBCode(intensities):
    R =  getColorHexCode(intensities[0])
    G =  getColorHexCode(intensities[1])
    B =  getColorHexCode(intensities[2])
    return "#"+R+G+B

# gets the hex value for a color given some intensity
def getColorHexCode(intensity):
    return f"{min(max(round(intensity),0),255):02x}"

# gets the intensity (using phong illumination model) from a given normal and incoming light vector L
def getIntensity(normal, L):
    reflectionVector = normalize(getReflectionVector(normal, L))
    ambient = Ia * Kd
    diffuse = Ip * Kd * dotProduct(normal, normalize(L))
    specular = Ip * Ks * pow(dotProduct(reflectionVector, V), specIndex)

    if dotProduct(normal, L) <= 0:
        diffuse = 0
        specular = 0

    return max(ambient + diffuse + specular, 0)

# Calculate a 3-D reflection Vector, R, given surface normal, N, and another incoming ray, L
def getReflectionVector(N, L):
    R = []
    N = normalize(N)
    L = normalize(L)
    twoCosPhi = 2 * dotProduct(N,L)
    if twoCosPhi > 0:
        for i in range(3):
            R.append(-N[i] + (L[i] / twoCosPhi))
    elif twoCosPhi == 0:
        for i in range(3):
            R.append( - L[i])
    else: # twoCosPhi < 0
        for i in range(3):
            R.append( N[i] - (L[i] / twoCosPhi))
    return normalize(R)

# Traces a single ray, returning the color of the pixel as an [R, G, B] list, using a 0-1 scale
def traceRay(startPoint, ray, depth, currObj=None):
    # return "black" when you reach the bottom of the recursive calls
    if depth == 0: return [0,0,0]

    # intersect the ray with all objects to determine nearestObject (if any)
    tMin = 999999  # initialize t to a very large number
    for obj in scene:
        if (obj == currObj):
            continue

        if obj.intersect(startPoint, ray) != []:
            if obj.t < tMin:
                tMin = obj.t
                nearestObject = obj
 
    # return skyColor if no intersection, or t is too large
    if tMin > 2000: 
        return skyColor

    # determine localColor and the weight for that color at the intersection point
    color = nearestObject.localColor
    intensity = nearestObject.phongIntensity
    if nearestObject.inShadow(): intensity *= 0.25
    localColor = [color[0] * intensity * 2, color[1] * intensity * 2, color[2] * intensity * 2]  # the *2 is a hack
    localWeight = nearestObject.localWeight
    
    # compute the color returned from the reflected ray
    reflectWeight = nearestObject.reflectWeight
    reflectColor = traceRay(nearestObject.intersectionPoint, nearestObject.reflect, depth - 1, nearestObject)
    
    # combine the local and reflected colors together using their respective weights
    returnColor = [0, 0, 0]
    for i in range(3):
        returnColor[i] = localColor[i] * localWeight + reflectColor[i] * reflectWeight
    
    return returnColor

# Driver function for displaying all the pixels on the screen.
def renderImage():
    top = round(canvasHeight/2)
    bottom = round(-canvasHeight/2)
    left = round(-canvasWidth/2)
    right = round(canvasWidth/2)
    for y in range(top, bottom, -1):
        for x in range(left, right):
            ray = normalize([y-x for x,y in zip(centerOfProjection, [x,y,0])])
            color = traceRay(centerOfProjection, ray, depthLimit)
            w.create_line(right+x, top-y, right+x+1, top-y, fill=getRGBCode(color))

# Set up scene
scene = []
scene.append(Plane([0,-150,0],[0,1,0],.3))
scene.append(Sphere([130, -50, 30], 100, .3, [255, 0, 0]))
scene.append(Sphere([-40, -70, 100], 70, .3, [0, 0, 255]))
scene.append(Sphere([-100, -90, -60], 50, .3, [50, 255, 50]))

# Basic tkinter setup
root = Tk()
outerframe = Frame(root)
outerframe.pack()

w = Canvas(outerframe, width=canvasWidth, height=canvasHeight)
w.pack()

renderImage()
root.mainloop()