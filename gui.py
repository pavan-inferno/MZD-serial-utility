'''
Lite version of the GUI
File: c:\Users\nuthip\full-seat-cushion\Python-GUI\Main_GUI_Lite.py
Project: c:\Users\nuthip\full-seat-cushion\Python-GUI
Created Date: Thursday February 7th 2019
Author: Pavan Nuthi
-----
Last Modified: Friday, 26th July 2019 11:17:55 am
Modified By: Pavan Nuthi (pavan.nuthi@uta.edu>)
-----
Copyright (c) 2019 UTARI
'''
# Initial version of this GUI can be tested with emulator code run on Arduino Mega
import binascii
import os.path
import struct
import sys
import time

# confirm the version of Gtk
import pygtk
pygtk.require('2.0')
import gtk

import gobject
import matplotlib
import serial
import serial.tools.list_ports as port_list
import xlsxwriter
from matplotlib import cm
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_gtkagg import \
    FigureCanvasGTKAgg as FigureCanvas
from matplotlib.backends.backend_gtkagg import \
    NavigationToolbar2GTKAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib.mlab import griddata
from mpl_toolkits.mplot3d import Axes3D
from numpy import arange, array, int16, linspace, meshgrid, ones, pi, sin, sqrt
from scipy import interpolate, io
from datetime import datetime

_num_aircell = 48

class GUI():

    # initializes the gui
    def __init__(self):
        ##Building Gtk objects from glade file
        # make a builder object
        self.ui = gtk.Builder()
        # read the builder object from glade file
        self.ui.add_from_file('./Advanced_serial_monitor.glade')
        # iterate through gtkobjects in glade file and import them as self.*
        # optionally prints all the gtk objects in the glade file 
        print "Imported Gtk objects:"
        for i in self.ui.get_objects():
            if issubclass(type(i), gtk.Buildable):
                name = gtk.Buildable.get_name(i)
                setattr(self, name, i)
                # print str(name), ",",
            else:
                print >>sys.stderr, "WARNING: cannot get name for '%s'" % i
        # connect all callbacks mentioned in glade file
        self.ui.connect_signals(self)
 
   

        # initialize serial port
        self.serialport = serial.Serial()
        # initialize comport selection ui
        print "Setting initial port"
        # get a list of serial ports
        ports = list(port_list.comports())
        comportlist = [str(i.device) for i in ports ]
        self.comportlstore = gtk.ListStore(int, str)
        self.make_comboboxlist(self.comportlstore, self.comportbox, comportlist, defaultindex = len(ports)-1)
        # set the baudrate as 250kbits pers second
        baudlist = [9600, 19200, 38400, 57600,  74880, 115200, 230400, 250000, 500000, 1000000, 2000000]
        baudratelist = [str(i) for i in baudlist]
        self.baudlstore = gtk.ListStore(int, str)
        self.make_comboboxlist(self.baudlstore, self.baudbox, baudratelist, defaultindex = 5)
        # set a list of end line sequences for written commands
        el_list = ['', '\\r','\\n','\\r\\n','\\n\\r']
        self.el_list_l = ['', '\r','\n','\r\n','\n\r']
        self.ellstore = gtk.ListStore(int, str)
        self.make_comboboxlist(self.ellstore, self.elbox, el_list, defaultindex = 1)

        self.readbuffer = ''
        self.writebuffer = ''
        
        # initialize flags
        self.red = False
        self.isfullpacket = False   # indicates whether a valid data packet is received
        self.isrecording = False    # indicates whether the GUI is currently recording
        self.ascii_switch = False   # indicates whether the device is sending ascii or binary packets
        # initialize counter for recording frames
        self.rec_counter = 1        # current number of recorded frames

        # initialize list of target pressures sent to the device
        self.setpressuremap = [0.3 for i in range(_num_aircell)]
        # initialize the instantaneous rate at which full data packets are received 
        self.daq_rate = 0           # indicates the rate of full packet reception
    
        # set a timeout function which refreshes display at 1000/50  = 20 fps
        self.gui_update_object = gobject.timeout_add(
            200, self.update_gui)

        # set an idle function which keeps the counter running as well as updates self.t1, t2, t3
        self.gui_mainloop_object = gobject.idle_add(
            self.collect_serialdata, priority=gobject.PRIORITY_DEFAULT_IDLE)
        # create a list of checkbox objects which is easier to access
        self.checkbox_obj_list = []
        for self.checkbox_number in range(1,_num_aircell+1):
            self.temp_obj = self.ui.get_object("cb%s" % self.checkbox_number)
            self.checkbox_obj_list.append(self.temp_obj)


        # show the main window and all its contents
        self.main_window.show_all()
    
    # updates the gui(timer function)
    def update_gui(self):
        if self.serialport.is_open:
            # when serial port is open
            # write time elapsed
            # print(str(int(time.time() - self.start_time)))
            self.elapsed_time.set_text(str(int(time.time() - self.start_time)))
            self.readbuf.set_text(self.readbuffer)
            self.writebuf.set_text(self.writebuffer)

            if(self.autoscroll.get_active()):
                a = self.scrolledwindow1.get_vadjustment()
                a.set_value(a.upper)
                # b = self.scrolledwindow2.get_vadjustment()
                # b.set_value(b.upper)

            

        return True
    
    # main loop to process the serial information (idle function)
    def collect_serialdata(self):
        # when the port's open
        # print "H"
        if self.serialport.is_open:
            # send the setpressure map
            # read a line
            if(self.serialport.in_waiting):
                self.bin_line = self.serialport.readline()                              #Reading data from serial port
                # self.readbuffer +=self.bin_line
                if (len(self.bin_line)>7):
                    # print self.filter.get_active()
                    if(self.bin_line[2]==':' and self.bin_line[5]==':'):
                        if (self.filter.get_active()):
                            # print "passed"
                            pass
                        else:
                            # print "added"
                            self.readbuffer +=self.bin_line
                    else:
                        self.readbuffer +=self.bin_line
                else:
                    self.readbuffer +=self.bin_line



                # print self.bin_line,    
            
            # # determine if its binary packet or ascii
            # if len(self.bin_line) == 201:
            #     # binary full packet conditions
            #     if self.bin_line[200] == '\n' and self.bin_line[199] == '\r' and self.bin_line[198] == 'z' and self.bin_line[0]== 'b':
            #         self.isfullpacket = True
            #         self.ascii_switch = False
            #         self.rcvd_packet = self.bin_line[1:198]
            #         self.rcvd_pkt_len = len(self.rcvd_packet)
            #         self.rcvd_data = struct.unpack("<fffffffffffffffffffffffffffffffffffffffffffffffffB", self.rcvd_packet)
            #         self.pressure_data = [i*0.145038 for i in self.rcvd_data[0:_num_aircell]]
            #         self.arduino_rate = self.rcvd_data[_num_aircell]
            #         self.controller_state = int(self.rcvd_data[_num_aircell+1])
            #     else:
            #         self.isfullpacket = False
            # else:
            #     if self.bin_line[0] == 'a' and self.bin_line[-1]=='\n' and self.bin_line[-2]=='\r' and self.bin_line[-3]== 'z':
            #         self.rcvd_csv = self.bin_line[1:-3]
            #         temp = [i for i in self.rcvd_csv.split(",")]
            #         if len(temp)==50:
            #             # ascii full packet condition                        
            #             self.pressure_data = [float(i)*0.145038 for i in temp[0:_num_aircell]]
            #             self.arduino_rate = float(temp[_num_aircell])
            #             self.rcvd_pkt_len = len(self.rcvd_csv)
            #             self.controller_state = int(temp[_num_aircell+1])
            #             self.isfullpacket = True
            #             self.ascii_switch = True
            #         else:
            #             self.ascii_switch = False
            #             self.isfullpacket = False
            #     else:
            #         self.isfullpacket = False
            #         self.ascii_switch = False
            # # if there's a full packet capture
            # if self.isfullpacket:
            #     # calculate the rate of full packet capture
            #     if not hasattr(self,"t_now"):
            #         self.t_now = time.time()-1          # handle  initial value of t_now
            #     self.t_prev = self.t_now                # update  t_prev with old time
            #     self.t_now = time.time()                # update t_now with new time
            #     if self.t_now !=self.t_prev:            # calculate daq_rate if its not too fast
            #         self.daq_rate = 1/(self.t_now- self.t_prev)
            #     self.avg_seating = sum(self.pressure_data[0:25]+ self.pressure_data[31:56])/50
            #     # update the file if recording
                # if self.isrecording:
                #     for i in range(0, len(self.pressure_data)):          #For loop to select row in the worksheet 
                #         self.worksheet_rec.write(i+1,self.rec_counter, (self.pressure_data[i]))
                #     self.worksheet_rec.write(0, self.rec_counter, self.t_now - self.start_time)
                #     self.worksheet_rec.write(63,self.rec_counter, self.arduino_rate )
                #     self.worksheet_rec.write(64,self.rec_counter, self.daq_rate )                
                #     self.rec_counter = self.rec_counter +1
        return True

    # cleans up and destroys gtk objects
    def on_main_window_destroy(self, *args):
        # cleanup
        # delete idle and timer functions
        gobject.source_remove(self.gui_update_object)
        gobject.source_remove(self.gui_mainloop_object)
        # close serial port if it's open
        if self.serialport.is_open:
            print "Serial port closed on exit"
            self.serialport.close()
        # quit gtk
        gtk.main_quit(*args)

    # creates a combobox from a list of strings and sets a given index
    def make_comboboxlist(self, lststore, combobox, combolist, defaultindex=0):
        # create a liststore
        lststore = gtk.ListStore(int, str)
        # populate it
        for i in range(len(combolist)):
            lststore.append([i, combolist[i]])
        # set the dropdown box to the liststore
        combobox.set_model(lststore)
        # create a  cell renderer object
        self.cell = gtk.CellRendererText()
        # clear the combobox
        combobox.clear()
        # pack the cell renderer into the box
        combobox.pack_start(self.cell, True)
        combobox.add_attribute(self.cell, "text", 1)
        # set given default option
        combobox.set_active(defaultindex)
    
    # displays a message on both notification area and console
    def display_all(self,data = ""):
        # prints data to console as well as notification area
        print data
        self.notification_area.set_text(data)
    
    # converts list into a grouped list
    def split_by_n(self, seq, n):
        while seq:
            yield seq[:n]
            seq = seq[n:]

    # sets the scale manually to a given value
    def on_manual_scale_activate(self, widget):
        # set  new z scale
        self.z_scale = float(widget.get_text())
        # replot the outline on top
        self.plot_seat_outline()
        # set z limit again
        self.ax.set_zlim(0, self.z_scale)
        # clear the input 
        widget.set_text("")

    # connects to the or disconnects from the serial port
    def on_connectbutton_toggled(self, widget):
        # open/close serial port
        if widget.get_active():                     #Connection button status
            # if its already open close it
            if self.serialport.is_open:
                self.serialport.close()
            self.display_all("Opening"+self.serialport.port+"@"+str(self.serialport.baudrate)+"baud")
            widget.set_label("Disconnect")
            self.serialport.open()                      #Opening serial port for user selected port and baudratebo
            if(self.serialport.in_waiting):
                self.bin_line = self.serialport.readline()                              #Reading data from serial po
            self.display_all("connected")
            self.display_all("Reading data..")
            # self.start()                            
            self.start_time = time.time()               #Recording time when connect button is pressed 
            self.start_datetime = datetime.now()        # Recording date and time when its connected
        else:
            if self.serialport.is_open:
                self.serialport.close()                 #Closing serial port
            self.display_all("Serial port closed !")
            widget.set_label("Connect")
    
    # refreshes the list of available serial ports
    def on_refreshbutton_clicked(self,widget):
        ports = list(port_list.comports())
        comportlist = [str(i.device) for i in ports ]
        self.comportlstore = gtk.ListStore(int, str)
        self.comportbox.set_model(None)
        self.make_comboboxlist(self.comportlstore, self.comportbox, comportlist, defaultindex = 1)
    
    # sets the filename to save the snapshot to the given one
    def on_snapshot_name_activate(self, widget):
        self.snapshot_file_name = widget.get_text()
        # widget.set_text('')

    # sets the filename to save the recording to the given one
    def on_rec_name_activate(self, widget):
        self.rec_file_name = widget.get_text()
        # widget.set_text('')
        filenamebase = str(a.second)+'s_'+str(a.minute)+'m_'+str(a.hour)+'h_'+str(a.day)+'d_'+str(a.month)+'M_'+str(a.year)+'y_'
        self.readfilename = 'read'+ filenamebase
        self.writefilename = 'write'+ filenamebase
        
    # saves the snapshot into an excel file with given name
    def on_snapshot_clicked(self, snapshot):
        # needs to be overhauled
        if self.serialport.is_open:
            if not hasattr(self,'snapshot_file_name'):
                self.snapshot_file_name = self.snapshot_name.get_text()
            self.workbook = xlsxwriter.Workbook(self.snapshot_file_name+'.xlsx')          #Creating excel file using xlswriter module
            self.worksheet = self.workbook.add_worksheet()          #Creating worksheet in the created excel file
            self.worksheet.write('A1', 'Bubble No.')                #Writing to the column    
            self.worksheet.write('B1', 'Pressure')                  #Writing to the column
            self.worksheet.write(63,0, "Arduino frequency (Hz)" )
            self.worksheet.write(64,0, "Daq frequency (Hz)" )
            self.worksheet.write(65,0, "units" )
            self.worksheet.write(65,1,self.pressure_unit)
            self.worksheet.write(66,0, "Snapshot time" )
            self.worksheet.write(66,1,unicode(datetime.now()))
            self.display_all("snapshot saved to "+ self.snapshot_file_name)

            for i in range(0, 2):                                   #For loop to select column in the worksheet
                for j in range(0, len(self.pressure_data)):          #For loop to select row in the worksheet 
                    if(i==0):
                        self.worksheet.write(j+1, i, j+1)           #Writing bubble numbers in first column
                    if(i==1):                                       #Writing bubble pressure(psi/kPa/kg per cm^2) values in second column
                        self.worksheet.write(j+1, i, (self.pressure_data[j]))
            self.workbook.close()               #Closing the file after writing data
        else:
            self.display_all("Connect before saving")
        
    # starts and stops recording data into an excel file of given name
    def on_record_toggled(self, widget):
        if self.serialport.is_open:

            if widget.get_active():
                a = datetime.now()      
                filenamebase = str(a.second)+'s_'+str(a.minute)+'m_'+str(a.hour)+'h_'+str(a.day)+'d_'+str(a.month)+'M_'+str(a.year)+'y_'
                self.readfilename = 'read'+ filenamebase
                self.writefilename = 'write'+ filenamebase
                self.display_all("Recording " + filenamebase + "  started")

                self.readfile = open(self.readfilename, "w")
                self.writefile = open(self.writefilename, "w")


                widget.set_label("Stop")
                self.isrecording = True                                                        
            else:
                widget.set_label("Record")

                self.writefile.write(self.writebuffer)
                self.writefile.close()
                self.display_all("Write file Recording   saved !")

                self.readfile.write(self.readbuffer)
                self.readfile.close()
                self.display_all("Read file Recording   saved !")
        else:
            self.display_all("Connect before saving")
            
    # sets the comport
    def on_comportbox_changed(self, widget):
        # When comport is selected
        if not hasattr(self, "serialport"):
            self.serialport = serial.Serial()
        index = widget.get_active()
        model = widget.get_model()
        temp = model[index][1]
        self.serialport.port = temp.split(" ")[0]
        self.display_all(self.serialport.port+" port selected")

 # sets the baudrate
    def on_baudbox_changed(self, widget):
        # When comport is selected
        if not hasattr(self, "serialport"):
            self.serialport = serial.Serial()
        index = widget.get_active()
        model = widget.get_model()
        temp = model[index][1]
        self.serialport.baudrate = temp.split(" ")[0]
        self.display_all(str(self.serialport.baudrate)+" baud selected")

    # sets the display units
    def on_elbox_changed(self, widget):
        # When units are selected
        index = widget.get_active()
        model = widget.get_model()
        self.el_seq = self.el_list_l[index]
        self.display_all("End line seq changed to "+ self.el_seq)
    
    # sends the typed message through the open serial port 
    def on_write_buffer_activate(self, widget):
        if self.serialport.is_open:
            temp_text = widget.get_text() + self.el_seq
            self.serialport.flushInput()
            self.serialport.flushOutput()
            self.serialport.write(temp_text)
            self.serialport.flushInput()
            self.serialport.flushOutput()  
            widget.set_text("")
            self.writebuffer += temp_text

    def scroll_slide_viewport(self):
            """Scroll the viewport if needed to see the current focused widget"""
            widget = self.window.get_focus()
            if not self.is_child(widget, self.main_widget):
                return

            _wleft, wtop = widget.translate_coordinates(self.main_widget, 0, 0)
            wbottom = wtop + widget.get_allocation().height

            top = self.vadj.value
            bottom = top + self.vadj.page_size

            if wtop < top:
                self.vadj.value = wtop
            elif wbottom > bottom:
                self.vadj.value = wbottom - self.vadj.page_size

if __name__ == "__main__":
    GUI_object = GUI()
    gtk.main()
