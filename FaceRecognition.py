# -*- coding: utf-8 -*-
# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import time
import cv2
from pygame.locals import *
import sys
import face
import config
import os
import glob
import face
import fnmatch
import numpy as np
import csv
import RPi.GPIO as GPIO
import threading,time


#ALIVE = False






def walk_files(directory, match='*'):
	"""Generator function to iterate through all files in a directory recursively
	which match the given filename match parameter.
	"""
	for root, dirs, files in os.walk(directory):
		for filename in fnmatch.filter(files, match):
			yield os.path.join(root, filename)


def prepare_image(filename):
	"""Read an image as grayscale and resize it to the appropriate size for
	training the face recognition model.
	"""
	return face.resize(cv2.imread(filename, cv2.IMREAD_GRAYSCALE))

def count_files(name):
        # Find the largest ID of existing positive images.
# Start new images after this ID value.
        direct = config.TRAIN_DIR + '/' + name
        if not os.path.exists(direct):
                os.makedirs(direct)
        files = sorted(glob.glob(os.path.join(direct,name + '_[0-9][0-9][0-9].pgm')))
        count = 0
        if len(files) > 0:
# Grab the count from the last filename.
          count = int(files[-1][-7:-4])+1
        return count

def remove_files(name):
        direct = config.TRAIN_DIR + '/' + name
        if not os.path.exists(direct):
                print 'no face file'
                return
        
        for file in os.listdir(direct):
                directFile = os.path.join(direct,file)
                if os.path.isfile(directFile):
                        os.remove(directFile)
        os.removedirs(direct)


def capture_train(name,crop):
        face_count = count_files(name)
        name_direct = config.TRAIN_DIR + '/' + name
        filename = os.path.join(name_direct, name + '_%03d.pgm' % face_count)
        cv2.imwrite(filename, crop)
        #filename = os.path.join(config.POSITIVE_DIR, POSITIVE_FILE_PREFIX + '%03d.pgm' % count)

        isnewName = True
        name_count = 0
        if not os.path.exists(config.NAME_FILE):
                file(config.NAME_FILE,'wb')

        faces = []
        labels = []
        datas = []
        data_label = -1                        
        csvfile = file(config.NAME_FILE,'rb')
        reader =  csv.reader(csvfile)
        for data in reader:
                
                datas.append(data)
                label = int(data[0])
                if data[1] == name:
                        name_count = int(data[0])
                        print 'have name'
                        isnewName = False
                        labels.append(name_count)
                        break
                if label > name_count and data_label == -1:
                        data_label = name_count
                name_count += 1
        csvfile.close()
        if isnewName:
                if data_label == -1:
                        datas.append([name_count,name])
                        labels.append(name_count)
                else:
                        datas.insert(data_label,[data_label,name])
                        labels.append(data_label)
                csvfile = file(config.NAME_FILE,'wb')
                writer = csv.writer(csvfile)
                writer.writerows(datas)
                csvfile.close()

        
        
        #for filename in walk_files(name_direct, '*.pgm'):
        faces.append(prepare_image(filename))
        
        if not os.path.exists(config.TRAINING_FILE):
                model.train(np.asarray(faces), np.asarray(labels))
                # Save model results
        else:
                model.load(config.TRAINING_FILE)
                model.update(np.asarray(faces), np.asarray(labels))
        model.save(config.TRAINING_FILE)


def train_all():
        if not os.path.exists(config.NAME_FILE):
                print 'no name saved'
        else:
                faces = []
                labels = []
                csvfile = file(config.NAME_FILE,'rb')
                reader =  csv.reader(csvfile)
                for data in reader:
                        label = int(data[0])
                        name = data[1]
                        name_direct = config.TRAIN_DIR + '/' + name
                        
                        for filename in walk_files(name_direct, '*.pgm'):
                                faces.append(prepare_image(filename))
                                labels.append(label)
                
                csvfile.close()
                model.train(np.asarray(faces), np.asarray(labels))
                # Save model results
                model.save(config.TRAINING_FILE)


def face_recognize(crop):
        data_name = ''
        model.load(config.TRAINING_FILE)
        label, confidence = model.predict(crop)
        csvfile = file(config.NAME_FILE,'rb')
        reader =  csv.reader(csvfile)
                                
        for data in reader:
                data_label = data[0]
                data_name = data[1]
                data_label = int(data_label)
                print data_label
                print label
                if label == data_label and confidence < config.POSITIVE_THRESHOLD:
                        csvfile.close()
                        print 'reconized'
                        return (True,data_name,confidence)
        csvfile.close()
        return False,'Unknown','2000'

def key_read(key):
        
        if key == ord("r"):
                if not os.path.exists(config.TRAINING_FILE):
                        command = config.STATE_NOFACE
                        command_color = config.COLOR_RED
                else:
                        command = config.STATE_SEARCH
                        command_color = config.COLOR_GREEN
        elif key == ord("="):
                showTimeList()
                command = config.STATE_PAUSE
                command_color = config.COLOR_BLACK 
        elif key == ord("s"):
                command = config.STATE_DETECT
                command_color = config.COLOR_GREEN
        
        elif key == ord("t"):
                command = config.STATE_TRAIN
                command_color = config.COLOR_BLUE
        elif key == ord("p"):
                command = config.STATE_PAUSE
                command_color = config.COLOR_BLACK
        elif key == ord("n"):
                show_name()
                command = config.STATE_PAUSE
                command_color = config.COLOR_BLACK
        elif key == ord("d"):
                command = config.STATE_PAUSE
                command_color = config.COLOR_BLACK

                raw_input('Press Enter to start to input')
                name = raw_input('Input a name:\n')
                delete_name(name)
                
        
        else :
                  return None

        return (command,command_color)
        
def show_name():
        csvfile = file(config.NAME_FILE,'rb')
        reader =  csv.reader(csvfile)
        print 'name:'
        for data in reader:
                label = int(data[0])
                print '%03d.%s'%(label,data[1])
        csvfile.close()



def delete_name(name):
        datas = []
        name_count = 0
        csvfile = file(config.NAME_FILE,'rb')
        reader =  csv.reader(csvfile)
        for data in reader:
                if data[1] == name:
                        continue
                name_count += 1
                datas.append(data)
        csvfile.close()
        csvfile = file(config.NAME_FILE,'wb')
        writer = csv.writer(csvfile)
        writer.writerows(datas)
        csvfile.close()
        remove_files(name)
        show_name()
        
        if name_count == 0:
                print ''
                #os.removedirs('./'+config.TRAINING_FILE)
        else:
                train_all()





def aive_detect():
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.ALIVE_DETECTOR_PIN, GPIO.IN)
        while True:
                #global ALIVE
                ALIVE = False
                if GPIO.input(config.ALIVE_DETECTOR_PIN):
                        #global ALIVE
                        ALIVE = True
                        print 'detect if alive'
                        
                else:
                        print 'detect not alive'
                time.sleep(1)

def start_thread():
        threadpool=[]

        th1 = threading.Thread(target= aive_detect)
        threadpool.append(th1)
        th1.start()
        #threading.Thread.join( th1 )

        th2 = threading.Thread(target= video_main)
        threadpool.append(th2)
        th2.start()
        #threading.Thread.join( th2 )
        return (th1,th2)

def recordTime(name):
        datas = []
        rectime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(time.time()))
        if not os.path.exists(config.TIME_FILE):
                file(config.TIME_FILE,'wb')
        csvfile = file(config.TIME_FILE,'rb')
        reader =  csv.reader(csvfile)
        name_count = 0
        for data in reader:
                datas.append(data)
                name_count += 1
        csvfile.close()

        name_count += 1

        datas.append([name_count,name,rectime])

        #labels.append(name_count)
       
        csvfile = file(config.TIME_FILE,'wb')
        writer = csv.writer(csvfile)
        writer.writerows(datas)
        csvfile.close()

def showTimeList():
        if not os.path.exists(config.NAME_FILE):
                print 'no time list'
        csvfile = file(config.TIME_FILE,'rb')
        reader =  csv.reader(csvfile)
        for data in reader:
                label = int(data[0])
                print '%03d.%s %s'%(label,data[1],data[2])
        csvfile.close()

def lightLed(pin):
        GPIO.output(config.GREEN_LED_PIN,False)
        GPIO.output(config.YELLOW_LED_PIN,False)
        GPIO.output(config.RED_LED_PIN,False)
        if pin == config.GREEN_LED_PIN:
                GPIO.output(config.GREEN_LED_PIN,True)
        elif pin == config.YELLOW_LED_PIN:
                GPIO.output(config.YELLOW_LED_PIN,True)
        elif pin == config.RED_LED_PIN:
                GPIO.output(config.RED_LED_PIN,True)
                

def GPIO_init():
        GPIO.cleanup()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(config.ALIVE_DETECTOR_PIN, GPIO.IN)
        GPIO.setup(config.GREEN_LED_PIN, GPIO.OUT)
        GPIO.setup(config.YELLOW_LED_PIN, GPIO.OUT)
        GPIO.setup(config.RED_LED_PIN, GPIO.OUT)
        

if __name__ == '__main__':
        screen_size = config.WINDOW_MIN_SIZE
        while True :
                screen = raw_input('Input "min" for minscreen ,"max" for maxscreen\n')
                if screen == 'min':
                        screen_size = config.WINDOW_MIN_SIZE
                        break
                elif screen == 'max':
                        screen_size = config.WINDOW_MAX_SIZE
                        break
                                   
        #face detect init
        GPIO_init()
        
        model = cv2.createLBPHFaceRecognizer()
        command = config.STATE_PAUSE
        command_color = config.COLOR_BLACK
        #cascade = cv2.CascadeClassifier('haarcascade_frontalface_alt2.xml')
        
# initialize the camera and grab a reference to the raw camera capture
        camera = PiCamera()
        #camera.close()
        camera.resolution = screen_size
        camera.framerate = 32
        rawCapture = PiRGBArray(camera, size=screen_size)

        time.sleep(0.1)
       
        
# capture frames from the camera
        for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
  # grab the raw NumPy array representing the image, then initialize the timestamp
  # and occupied/unoccupied text
          ALIVE = False
          if GPIO.input(config.ALIVE_DETECTOR_PIN):
                ALIVE = True

          image = frame.array

######################################################################################################################
          if command == config.STATE_DETECT or command == config.STATE_SEARCH:
  
# create grayscale version
                grayscale = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)  
                crop =  image.copy()

          #cv2.equalizeHist(grayscale, grayscale)
          #faces = cascade.detectMultiScale(grayscale, scaleFactor=1.3,minNeighbors=5, minSize=(30, 30), flags = cv2.cv.CV_HAAR_SCALE_IMAGE)face.detect_single(image)
          #if len(faces)>0:
          #  for i in faces:
          #    x, y, w, h = i
          #    crop = face.crop(image, x, y, w, h)
                result = face.detect_single(grayscale)
                if result != None:
                        x, y, w, h = result
			# Crop and resize image to face.
                        crop = face.resize(face.crop(grayscale, x, y, w, h))
        #################################################################################################################
                        if ALIVE:
                                if command == config.STATE_SEARCH:
                                
                                        rec_result,data_name,confidence = face_recognize(crop)
                                        if rec_result:
                                                if confidence <= 45:
                                                        lightLed(config.GREEN_LED_PIN)
                                                        print 'green'
                                                        recordTime(data_name)
                                                elif confidence < 65:
                                                        lightLed(config.YELLOW_LED_PIN)
                                                        print 'yellow'
                                                else :
                                                        lightLed(config.RED_LED_PIN)
                                                        print 'red'
                                                text_confi = '%.2f'%confidence
                                                print 'Predicted {0} face with confidence {1} (lower is more confident).'.format(data_name,confidence)
                                                cv2.putText(image, data_name, (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 1, command_color, thickness = 2, lineType = 2)
                                                cv2.putText(image, text_confi, (x + w/3*2, y-5), cv2.FONT_HERSHEY_COMPLEX, 1, command_color, thickness = 2, lineType = 2)  
                                        else:
                                                print 'red'
                                                cv2.putText(image, 'Unknown', (x, y-5), cv2.FONT_HERSHEY_COMPLEX, 1, command_color, thickness = 2, lineType = 2)

        #################################################################################################################
                                elif key == ord("c"):
                                        
                                        raw_input('Press Enter to input a name')
                                        name = raw_input('Input a name:\n')
                                        if name == '':
                                                continue
                                        capture_train(name,crop)

                                        cv2.putText(image, "capture",  (image.shape[0]/2, image.shape[1]/3), cv2.FONT_HERSHEY_COMPLEX, 1, config.COLOR_RED, thickness = 2, lineType = 2)
                                        print "capture"
                                        
                        else:
                                cv2.putText(image, 'not alive', (x, y-10), cv2.FONT_HERSHEY_COMPLEX, 1, command_color, thickness = 2, lineType = 2)
                                print'not alive'
      
                        cv2.rectangle(image, (x, y), (x+w, y+h), config.COLOR_GREEN)
                        print "get face"
                else:
                        print "Faces not detected."


##########################################################################################################################

          elif command == config.STATE_TRAIN:
                  train_all()
                  command = config.STATE_TR_CP
          #elif command == config.STATE_PAUSE:
                  #print "pause"

##########################################################################################################################
          #lightLed(100)
  ##########################
          cv2.putText(image, command, (20, 40), cv2.FONT_HERSHEY_COMPLEX, 1, command_color, thickness = 2, lineType = 2) 
          cv2.imshow("Frame", image)
          key = cv2.waitKey(1) & 0xFF

  # clear the stream in preparation for the next frame
          rawCapture.truncate(0)

  # if the `q` key was pressed, break from the loop
          if key == ord("q"):
                break
          else:
                key_result = key_read(key)
                if key_result != None:
                        command, command_color = key_result
                  
                

        #th1,th2 = start_thread()
        #th1.stop()
        #th2.stop()
        #video_main()
