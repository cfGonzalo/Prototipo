from modelo.main import Modelo
from vista.main import Vista
from time import time, sleep
import cv2, torch, os, torchvision
from PIL import Image
from PIL import ImageTk
from copy import copy
from datetime import datetime
import numpy as np
from vmbpy import *
from queue import Queue, Empty
from math import ceil
from models.common import DetectMultiBackend
from pathlib import Path
from threading import Event, Semaphore, Thread
from serial import Serial, SerialException
from serial.tools.list_ports import comports

from utils.general import (check_img_size, non_max_suppression, xyxy2xywh, xywh2xyxy)
from utils.augmentations import letterbox
from utils.torch_utils import select_device

############################################################################################################
############################################################################################################
############################################################################################################
# Programa princial
class Controller:

    def __init__(self, model: Modelo, view: Vista):
        self.view = view
        self.model = model

        self.view.frames['inicio'].bot.config(command=self.finaliza)

        # Cola para pasar datos entre los hilos productor y consumidor
        self.cola = Queue(10)

        # Crear una bandera para indicar que se debe detener el hilo
        self.detener_hilo = Event()
        self.detener_trat = Event()
        self.detener_gps = Event()
        # Semaforos para el control de recursos compartidos entre hilos
        self.sem = Semaphore(1)
        self.sem2 = Semaphore(1)
        self.sem3 = Semaphore(1)
        # Carga el modelo
        self.loadMod()
        # Carga de datos necesarios para el OCR
        self.img = None

        # Recursos compartidos para datos GPS
        self.data_gps = "0000,000,000"

    def start(self):
        # Se inicializan los hilos de datos y la vista        
        vid = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if vid.isOpened():
            vid.set(3, 1920)
            vid.set(4, 1080)

            self.hDatos = Thread(target=self.bucleOpenCv, args=(vid,))
        else:
            self.hDatos = Thread(target=self.bucleVmb, args=()) 
        
        self.hDatos.start()

        self.hTrat = Thread(target=self.libera, args=())
        self.hTrat.start()

        self.hgps = Thread(target=self.gps, args=())
        self.hgps.start()

        self.view.start_mainloop()

    def actualizaPanel(self,img):
        # img=cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img=cv2.resize(img,(1152,648), cv2.INTER_AREA)
        img=Image.fromarray(img)
        if self.detener_hilo.is_set():
            return
        try:
            self.img=ImageTk.PhotoImage(img)
        except Exception as e:
            print("Fallo al transformar la imagen:", e)

        if self.detener_hilo.is_set():
            return
        self.view.root.after(0, self.view.actualizaFrame, self.img)
        del img
        
    def actualizaUlt(self, img, txt):
    
        img=cv2.resize(img,(384,216), cv2.INTER_AREA)
        img=Image.fromarray(img)

        if self.detener_trat.is_set():
            return
        
        img=ImageTk.PhotoImage(img)
        if self.detener_trat.is_set():
            return

        self.view.root.after(0, self.view.actualizaUlt, img,txt)

    def bucleOpenCv(self, vid: cv2.VideoCapture):

        prev_frame_time = 0
        new_frame_time = 0

        font = cv2.FONT_HERSHEY_SIMPLEX 

        while(True):
        
            if self.detener_hilo.is_set():
                break

            ret, frame = vid.read()
            new_frame_time = time() 

            if not frame is None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # print(new_frame_time - prev_frame_time)
                fps = str(int(1/(new_frame_time-prev_frame_time))) 
                prev_frame_time = new_frame_time

                if self.sem3.acquire():
                    gps = copy(self.data_gps)
                    self.sem3.release()

                if self.sem.acquire(blocking = False):
                    self.cola.put(copy((gps,frame)))

                cv2.putText(frame, fps, (7, 70), font, 3, (100,  255, 0), 3, cv2.LINE_AA) 

                if self.detener_hilo.is_set():
                    break
                
                self.view.root.after(0, self.actualizaPanel, frame)

    def bucleVmb(self):

        with VmbSystem.get_instance() as vmb:
            
            self.handler =  Handler()
            cams = vmb.get_all_cameras()

            with cams[0] as cam:
                prev_frame_time =   0
                new_frame_time = 0

                font = cv2.FONT_HERSHEY_SIMPLEX 

                print("Iniciando el ajuste de la camara.")
                # Ajuste de lso parametros de la camara
                cam.AcquisitionMode.set("Continuous")
                cam.ExposureAuto.set("Continuous")
                cam.AcquisitionFrameRateEnable.set(False)

                cam.BlackLevelSelector.set("All")
                cam.BlackLevel.set(0)
                cam.Gain.set(0)
                cam.GainAuto.set("Continuous")

                cam.ExposureAutoMax.set(66661.79)
                cam.ExposureAutoMin.set(62.417)
                # cam.AutoModeRegionSelector.set("Auto Mode Region 1")
                cam.AutoModeRegionWidth.set(4024)
                cam.AutoModeRegionHeight.set(2264)
                cam.AutoModeRegionOffsetX.set(0)
                cam.AutoModeRegionOffsetY.set(386)

                cam.Height.set(2264)
                cam.Width.set(4024)
                cam.OffsetY.set(386) 
                cam.OffsetX.set(0)
                
                cam.GainAuto.set("Continuous")
                cam.set_pixel_format(PixelFormat.BayerRG8)

                print("Ajuste finalizado. Iniciando retransmision.")
                cam.start_streaming(handler=self.handler, buffer_count=10)

                while(True):
                    frameVmb = None

                    if self.detener_hilo.is_set():
                        cam.stop_streaming ()   
                        break

                    frameVmb = self.handler.get_image()
                    
                    if not frameVmb is None:
                        frameVmb = frameVmb.as_numpy_ndarray()
                        frameVmb = cv2.cvtColor(frameVmb, cv2.COLOR_BAYER_RG2BGR)

                        new_frame_time = time() 

                        fps = str(int(1/(new_frame_time-prev_frame_time))) 
                        prev_frame_time = new_frame_time

                        if self.sem3.acquire():
                            gps = copy(self.data_gps)
                            self.sem3.release()
                        if self.sem.acquire(blocking = False):
                            self.cola.put((gps,frameVmb), block = False, timeout = 0.1)

                        frameVmb = cv2.putText(frameVmb, fps, (7, 70), font, 3, (100,  255, 0), 3, cv2.LINE_AA) 
                        if self.detener_hilo.is_set():
                            cam.stop_streaming()
                            break

                        self.view.root.after(0, self.actualizaPanel, frameVmb)
                    
                        # Se espera a que se actualize el panel antes de continuar
                        self.view.root.update_idletasks()

                    del frameVmb

    def libera(self):

        now = datetime.now()
        try:
            os.mkdir("D:/imagenes")
        except Exception as e:
            error = ("ERROR:",e)
        # except:

        carpeta = "D:/imagenes/" + now.strftime("%Y%m%d_%H%M%S")
        os.mkdir(carpeta)
        i = 0
        contador = 0

        font = cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 1
        color = (255, 0, 0) 
        thickness = 10
        conf_thres=0.25 
        iou_thres=0.45
        max_det=1000

        agnostic_nms=False
        classes=None

        self.modelo.warmup(imgsz=(1, 3, *self.imgsz))  # warmup

        while(True):

            if self.detener_trat.is_set():
                break

            try:
                guarda = False
                dat =  self.cola.get(timeout=1) # La imagen entra en formato BGR
                img = dat[1]
                gps = dat[0]
                # Se preprocesa la imagen
                im = self.preprocImg(img) # Sale en formato RGB

                pred = self.modelo(im, augment=False, visualize=False)
                pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)
                #  Objetos para guardar en memoria junto con la imagen que se ha procesado en caso de que exista algo que haya que ensennar
                img_save = cv2.cvtColor(copy(img), cv2.COLOR_RGB2BGR)
                coord_save=""
                im = letterbox(img, self.imgsz, stride=self.stride, auto=self.pt)[0]
                for *xyxy, conf, cls in reversed(pred[0]):
                    xyxy = [int(img.shape[1]*np.floor(xyxy[0].cpu())/im.shape[1]), int(img.shape[0]*np.ceil(xyxy[1].cpu())/im.shape[0]),
                        int(img.shape[1]*np.floor(xyxy[2].cpu())/im.shape[1]), int(img.shape[0]*np.ceil(xyxy[3].cpu())/im.shape[0])]
                    if (int(xyxy[3])-int(xyxy[1])>0) & (int(xyxy[2])-int(xyxy[0])>0) & (int(xyxy[0])>0) & (int(xyxy[1])>0):

                        cv2.rectangle(img, (int(xyxy[0]),int(xyxy[1])),
                            (int(xyxy[2]),int(xyxy[3])), (0,255,0), thickness)
                        
                        # Se annade el rectangulo y el texto a la imagen
                        cv2.rectangle(img, (xyxy[0],xyxy[1]),
                            (xyxy[2],xyxy[3]), (0,0,255), thickness)
                        
                        self.view.root.after(0, self.actualizaUlt, img, "")
                        self.view.root.update_idletasks()

                        for a in xyxy:
                            coord_save = coord_save + str(int(a)) + "\t"
                        coord_save += "\n"
                        guarda = True
                del pred
                if guarda:  
                    cv2.imwrite( carpeta + "/img_"+now.strftime("%Y%m%d_%H%M%S")+".jpg",img_save)
                    arch1 = open(carpeta + "/img_"+now.strftime("%Y%m%d_%H%M%S")+"_coordsHito.txt", 'w')
                    arch1.write(coord_save)
                    arch1.close()
                    arch2 = open(carpeta + "/img_"+now.strftime("%Y%m%d_%H%M%S")+"_coordsGps.txt", 'w')
                    arch2.write(gps)
                    arch2.close()
                    i+=1
                else:
                    if contador % 80 == 0:
                        
                        # Se han tratado 80 imagenes sin detectar un hito
                        # se procede a guardar una imagen.
                        now = datetime.now()
                        cv2.imwrite(carpeta+"/trazado_"+now.strftime("%Y%m%d_%H%M%S")+".jpg", img_save )
                        arch1 =open(carpeta+"/trazado_"+now.strftime("%Y%m%d_%H%M%S")+"_coordsGps.txt", 'w')
                        arch1.write(gps)
                        arch1.close()
                    contador +=1


            except  Empty:
                continue
            except Exception as e:
                if self.detener_trat.is_set():
                    break
                print("Ha ocurido un error:\t", e)
            del img
            self.sem.release()
            self.cola.task_done()
        return

    def finaliza(self):
        print("Finalizar")

        self.detener_hilo.set()
        self.detener_trat.set()
        self.detener_gps.set()

        while(self.hDatos.is_alive() or self.hTrat.is_alive()):
            print("Esperando a terminar los hilos")
            if self.hDatos.is_alive():
                print("\tEl Hilo de datos sigue vivo")
            if self.hTrat.is_alive():
                print("\tEl Hilo de tratamiento sigue vivo")
            if self.hgps.is_alive():
                print("\tEl Hilo de GPS sigue vivo")
            sleep(1)
            self.view.root.update_idletasks()

        self.view.root.destroy()
        return

    def loadMod(self):
        weights="_internal/best.pt"
        data="_internal/mod3.yaml"
        dnn=False
        half=False 
        imgsz=(640, 640) 

        device = select_device("")
        self.modelo = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
        self.stride, self.pt = self.modelo.stride, self.modelo.pt
        self.imgsz = check_img_size(imgsz, s=self.stride)  # check image size
        return

    # Preprocesa la imagen para meterla en el modelo
    def preprocImg(self, img):
        # global imgsz, stride, pt, model

        #Preprocesamiento de la imagen
        im = letterbox(img, self.imgsz, stride=self.stride, auto=self.pt)[0]  # Ajusta el tamanno haciendo "padding"
        del img
        im = im.transpose((2, 0, 1))[::-1]  # HWC(alto, acho, color) to CHW, BGR(azul,verde,rojo) to RGB


        # Transforma la iam al tipo necesario (torch)
        im = np.ascontiguousarray(im)
        im = torch.from_numpy(im).to(self.modelo.device)

        # Selecciona el tipo de numero a utilizar (simple o doble)
        im = im.half() if self.modelo.fp16 else im.float()  # uint8 to fp16/32
        # Normalizacion
        im /= 255  # 0 - 255 to 0.0 - 1.0

        # Si se necesita se annade Batch 
        if len(im.shape) == 3:
            im = im[None]

        return im

    def lee(self, img):
        gris = cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2GRAY)
        # Aplica un limite en la imagen para separar negro y blanco
        theshold_img = cv2.threshold(gris, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        # Aplica OCR a la imagen
        texto = image_to_string(theshold_img, config=" --psm 6")
        return texto

    def gps(self):
        # lectura del gps en bucle
        lista = comports()

        # Se busca el puerto en el que haya un gps de LOCOYS
        port = ""
        for puerto in lista:
            aux = list(puerto)
            if aux[1][:31] == "LOCOSYS Technology GPS Receiver":
                port = aux[0]

        try:
            gps = Serial(port, baudrate=115200)

            while True:

                ser_bytes = gps.readline()
                decoded_bytes = ser_bytes.decode('utf-8')
                data = decoded_bytes.split(",")

                if data[0] == "$GPRMC":
                    lat_nmea = data[3]
                    lat_degrees = lat_nmea[:2]

                    if data[6] == 'S':
                        latitude_degrees = float(lat_degrees) * -1
                    else:
                        latitude_degrees = float(lat_degrees)

                    latitude_degrees = str(latitude_degrees).strip(".0")
                    lat_ddd = lat_nmea[2:10]
                    lat_mmm = float(lat_ddd)/60
                    lat_mmm = str(lat_mmm).strip('0.')[:8]
                    latitude = latitude_degrees + "." + lat_mmm

                    long_nmea = data[5]
                    long_degrees = long_nmea[:3]
                    if data[6] == 'W':
                        longitude_degrees = float(long_degrees) * -1
                    else:
                        longitude_degrees = float(long_degrees)

                    longitude_degrees = str(longitude_degrees).strip('.0')
                    long_ddd = long_nmea[3:10]
                    long_mmm = float(long_ddd) / 60
                    long_mmm = str(long_mmm).strip('0.')[:8]
                    longitude = longitude_degrees + "." + long_mmm

                    data_gps = latitude+","+longitude+","+data[1]
                    
                    if self.sem3.acquire():
                        self.data_gps = data_gps
                        self.sem3.release()

                if self.detener_gps.is_set():
                    break

        except SerialException:
            # Se desconecta el GPS (o no estaba conectado)
            print("Se ha desconectado el GPS")
            # Se devuelven los valores del gps a 0000 para que no haya error con los Datos
            self.latitude = "0000"
            self.longitude = "0000"
            self.hora = "0000"



class Handler:

    def __init__(self):
        self.display_queue = Queue(10)

    def get_image(self):
        try:
            return self.display_queue.get(True, timeout=1)
        except:
            return None

    def __call__(self, cam: Camera, stream: Stream, frame: Frame):
        opencv_display_format = PixelFormat.Bgr8
        if frame.get_status() == FrameStatus.Complete:
            # print('{} acquired {}'.format(cam, frame), flush=True)

            # Convert frame if it is not already the correct format
            # if frame.get_pixel_format() == opencv_display_format:
            display = frame
            # else:
                # This creates a copy of the frame. The original `frame` object can be requeued
                # safely while `display` is used
                # display = frame.convert_pixel_format(opencv_display_format)

            self.display_queue.put(display, True)
        cam.queue_frame(frame)
