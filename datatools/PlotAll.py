

import pandas as ps 
import numpy as np
import matplotlib.pylab as plt
import matplotlib.gridspec as gridspec
import sys, getopt
import csv
import sys
import os


# make our test 2
iso_table_label = ['Test','Comp',      'Rp', 'Vt', 'Freq', 'PEEP', 'I', 'E']
iso_table_UNITS = ['    ', 'L/CM*H2O', '  ', 'mL', 'BPM', 'cmH20',' sec', ' sec' ]
iso_table_data =  [ [ "#1 Set",      50,       5,    500,   20,      5,    1,      2], 
                     [ "#2 Set",     50,      20,    500,   15,     10,    1,      3], 
                     [ "#3 Set", "#2 Set",3,     20,      5,     500,   20,      5,    1,      2], 
                     [ "#4 Set",  20,      20,    500,   20,     10,    1,      2],
                     [ "#5 Set",     20,      20,    300,   20,      5,    1,      2],
                     [ "#6 Set",     20,      50,    300,   15,     10,    1,      3],
                     [ "#7 Set",     10,      50,    300,   20,     10,    1,      2],
                     [ "#8 Set",     10,      20,    200,   20,      5,    1,      2],
                     [ "#9 Set",     10,      20,    200,   24,      5,    1,    1.5],
                     [ "#10 Set",     10,      20,    200,   30,      5,    1,      1],
                     [ "24hrs",    50,      5,     600,   35,      10,    1,  1]    # endurance test
                  ]


graph_table_header = ['Breath #','Vt',      'PEEP', 'I', 'E', 'I+E']


vent_measured =      [ 'UI',    '',      '',    '',    '',      '',   '']
instrument_measured = [ 'Measured',    '',      '',    '',    '',      '',   '']
per_error =  ['% Error',    '',      '',    '',    '',      '',   '']

#defaults
display = False         # if true show graph on screen
stats = True            # create track file
plots = True            # create plots
verbose = False         # print data on screen
recorded_peep = 0.0
breath_cycle = 0.0

insp_time = 0.0
ie_time = 0.0
total_vt = 0

insp_time_pb = []
total_vt_pb = []
recorded_peep_pb = []
ie_time_pb = []
stats_table = []
graph_table =  []
beath_num = 0



breath_time = 0.0
split = True
annotate = True
start = 0
stop = 0
raw_graph = False

def plot_volume(X,Y, index, ax) :
   plt.xlabel('time(sec)')
   plt.ylabel('Volume(ml)')
   if split == True :
      plt.title('Tidal Volume Per Inspiration '+str(index))
   else :
      plt.title('Tidal Volume')

   plt.yticks(np.arange(0, max(Y)+50, 50))
   plt.xticks(np.arange(min(X), max(X)+1, 1.0))
   plt.grid(True)
   plt.plot(X,Y)

   if annotate == True :
      # Annotate max
      xmax = X[np.argmax(Y)]
      ymax = Y[np.argmax(Y)]
      #print("*****",xmax)
      text= "t={:.2f}, Vt={:.2f}".format(xmax, ymax)
      ax=plt.gca()
      bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
      arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
      kw = dict(xycoords='data',textcoords="axes fraction",
               arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
      ax.annotate(text, xy=(xmax, ymax), xytext=(0.55,0.96), **kw)
   plt.plot(X,Y)
#end plot_volume

def plot_pressure(pressure_type, X, Y, index, ax) :
   global recorded_peep
   
   plt.xlabel('time(sec)')
   plt.ylabel('Pressure (cmH20)')
   if pressure_type == "lung" :
      plt.title('Pressure Per Breath @ Lung '+str(index))
   elif pressure_type == "airway" :
      plt.title('Pressure Per Breath in Airway (before PEEP V ) '+str(index))
   else :
      if split == True :
         plt.title('Pressure Per Breath at PEEP '+str(index))
      else :
         plt.title('Pressure at PEEP')
   
   plt.yticks(np.arange(0, max(Y)+5, 5.0))
   plt.ylim(0,max(Y)+5)
   plt.xticks(np.arange(min(X), max(X)+1, 1.0))
   plt.grid(True)
   plt.plot(X,Y)

   if annotate == True :
      # Annotate max
      xmax = X[np.argmax(Y)]
      ymax = Y[np.argmax(Y)]
      
      text= "t={:.2f}, p={:.2f}".format(xmax, ymax)
      ax=plt.gca()
      bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
      arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
      kw = dict(xycoords='data',textcoords="axes fraction",
               arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
      ax.annotate(text, xy=(xmax, ymax), xytext=(0.94,0.96), **kw)
      
      if pressure_type == "peep" or pressure_type == "lung":
         xmin = X[np.argmin(Y)]
         ymin = Y[np.argmin(Y)]
         peep = 0.0
         if breath_cycle > 0 and len(Y) > 1000 :         # this is terrible, but here its a way to tell valid breath
            #print(breath_cycle,len(Y))
            for k in range(len(Y)-50,len(Y)) :           # PEEP IS average of last 50 values
               peep = peep + Y[k]
            recorded_peep = recorded_peep + (peep/50.0)
         text= "t={:.2f}, p={:.2f}".format(xmin, ymin)
         ax=plt.gca()
         bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
         arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=20,angleB=120")
         kw = dict(xycoords='data',textcoords="axes fraction",
               arrowprops=arrowprops, bbox=bbox_props, ha="left", va="bottom")
         ax.annotate(text, xy=(xmin, ymin), xytext=(0.5,0.5), **kw)
   
   plt.plot(X, Y)
#end plot pressure




def plot_flow(X, Y, index, ax) :
   plt.xlabel('time(sec)')
   plt.ylabel('Flow (SLM)')
   if split == True :
      plt.title('Flow Per Breath '+str(index))
   else :
      plt.title('Flow Per Breath ')
   plt.xticks(np.arange(min(X), max(X)+1, 1.0))
   plt.grid(True)

   if annotate == True :
      # Annotate max
      xmax = X[np.argmax(Y)]
      ymax = Y[np.argmax(Y)]
      text= "t={:.2f}, f={:.2f}".format(xmax, ymax)
      ax=plt.gca()
      bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
      arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
      kw = dict(xycoords='data',textcoords="axes fraction",
               arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
      ax.annotate(text, xy=(xmax, ymax), xytext=(0.94,0.96), **kw)
   plt.plot(X, Y)
#end plot_flow

def draw_table(ax, testnum, trans) :
   global stats_table
   table_data = []
   table_data.append(iso_table_label)
   table_data.append(iso_table_UNITS)
   table_data.append(iso_table_data[testnum-1])

   #print(iso_table_UNITS)
   #print(stats_table)
   if stats_table != [] :
      table_data.append(stats_table[0])  
      table_data.append(stats_table[1]) 
      table_data.append(stats_table[2])
      table_data.append(stats_table[3])  
      table_data.append(stats_table[4])
      table_data.append(stats_table[5]) 


   df = ps.DataFrame(data=table_data)

   if trans == True :
      df = df.T                              # transponse  rows and columns
      table_data = df.values.tolist()


 
   table = ax.table(cellText=table_data, loc='center')
   
   table.auto_set_font_size(False)
  

   if trans == True :
      table.set_fontsize(8)
      table.scale(2, 2)  # may help
   else :
      if split == True :
         table.set_fontsize(10)
         table.scale(10, 4)
      else :
         table.set_fontsize(8)
         #table.scale(5, 2)        
   table.auto_set_column_width(col=list(range(len(df.columns))))
   ax.axis('off')
# end draw_table

def draw_graph_table(ax, testnum, trans) :
   global stats_table
   graph_table_data = []
   graph_table_data.append(graph_table_header)
  

   for i in range(0,breath_num-1) :
      graph_table_data.append(graph_table[i])  


   df = ps.DataFrame(data=graph_table_data)

   if trans == True :
      df = df.T                              # transponse  rows and columns
      table_data = df.values.tolist()


 
   table = ax.table(cellText=graph_table_data, loc='center')
   
   table.auto_set_font_size(False)
  

   if trans == True :
      table.set_fontsize(8)
      table.scale(2, 2)  # may help
   else :
      if split == True :
         table.set_fontsize(10)
         table.scale(10, 4)
      else :
         table.set_fontsize(8)
         #table.scale(5, 2)        
   table.auto_set_column_width(col=list(range(len(df.columns))))
   ax.axis('off')
# end draw_table

def plot_all(testnum,pressure_type,flow_X,flow_Y,press_X,press_Y,volume_X,volume_Y,breath_cycle,plot_file) :

  
   if split == True :
   
      if testnum  ==  11 :

         plt.figure(figsize=(8,8))
         plt.subplots_adjust(wspace=1.0, hspace=0.5)
         # create 2x2 grid
         gs = gridspec.GridSpec(2, 4)
        
         

         ax = plt.subplot(gs[0, :2], )
         plot_flow(flow_X,flow_Y,breath_cycle,ax)

         ax = plt.subplot(gs[0, 2:]) # row 1, col 0'
        
         plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)


         ax = plt.subplot(gs[1, 1:3])
         plot_volume(volume_X,volume_Y,breath_cycle,ax)

      else : 
         plt.figure(figsize=(8,8))
         plt.subplots_adjust(wspace=0.4, hspace=0.5)
         # create 2x2 grid
         gs = gridspec.GridSpec(2, 2)
         
         ax = plt.subplot(gs[0, 0]) # row 0, col 1
         draw_table(ax,testnum, True)     ## transpose the 
      
         ax = plt.subplot(gs[0, 1]) # row 0, col 1
         plot_flow(flow_X,flow_Y,breath_cycle,ax)
         
         ax = plt.subplot(gs[1, 0]) # row 1, col 0
         plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)
         
         ax = plt.subplot(gs[1, 1]) # row 1, col 0
         plot_volume(volume_X,volume_Y,breath_cycle,ax)
   else :

      if testnum  ==  11 :

         plt.figure(figsize=(8,8))
         plt.subplots_adjust(wspace=1.0, hspace=0.5)
         # create 2x2 grid
         gs = gridspec.GridSpec(3, 1)
        
         

         ax = plt.subplot(gs[0, 0], )
         plot_flow(flow_X,flow_Y,breath_cycle,ax)

         ax = plt.subplot(gs[1, 0]) # row 1, col 0'
        
         plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)


         ax = plt.subplot(gs[2, 0])
         plot_volume(volume_X,volume_Y,breath_cycle,ax)

      else : 
         
         # plt.figure(figsize=(8,9))
         # plt.subplots_adjust(wspace=0.4, hspace=0.46, bottom = 0.06, top = 0.98)
         # # create 2x2 grid
         # gs = gridspec.GridSpec(4, 1)
         
         # ax = plt.subplot(gs[0, 0]) # row 0, col 1
         # draw_table(ax,testnum, False)     ## transpose the 
      
         # ax = plt.subplot(gs[1, 0]) # row 0, col 1
         # plot_flow(flow_X,flow_Y,breath_cycle,ax)
         
         # ax = plt.subplot(gs[2, 0]) # row 1, col 0
         # plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)
         
         # ax = plt.subplot(gs[3, 0]) # row 1, col 0
         # plot_volume(volume_X,volume_Y,breath_cycle,ax)

         plt.figure(figsize=(8,9))
         plt.subplots_adjust(wspace=0.02, hspace=0.47, bottom = 0.06, top = 0.96, left = 0.09, right= 0.95)
         # create 2x2 grid
         gs = gridspec.GridSpec(4, 4)
         
         ax = plt.subplot(gs[0, 0:2]) # row 0, col 1
         draw_table(ax,testnum, False)     ## transpose the 

         ax = plt.subplot(gs[0, 3]) # row 0, col 1
         draw_graph_table(ax,testnum, False)     ## transpose the 
      
         ax = plt.subplot(gs[1, 0:4]) # row 0, col 1
         plot_flow(flow_X,flow_Y,breath_cycle,ax)
         
         ax = plt.subplot(gs[2, 0:4]) # row 1, col 0
         plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)
         
         ax = plt.subplot(gs[3, 0:4]) # row 1, col 0
         plot_volume(volume_X,volume_Y,breath_cycle,ax)
      
   plt.savefig(plot_file)

   if display == True :
      #input()
      plt.show()
# end ploy_chats


# calculate and return PEEP
def calculate_PEEP(j,k,X,Y) :
   peep = 0
   for i in range(k-50,k) :
            peep = peep + Y[i]
   print("PEEP :",peep/50)
   return(peep/50.0)



def plot_charts_per_breath(test_num, flow_file, press_file , pressure_type) :
   global breath_cycle
   global breath_time
   global insp_time
   global ie_time
   global total_vt
   global recorded_peep

   # open flow file
   airway = False
   with open(flow_file) as f:
      reader = csv.reader(f)
      data = list(reader)
   # open pressure file
   with open(press_file) as p:
      press_reader = csv.reader(p)
      press_data = list(press_reader)
   
   
   length = len(data)

   # state varibles for breath detection
   positive_trend = True
   valid_breath = 0
   breath_cycle = 0
   first_breath_started = False
   end_of_inhalation = False

   # data and stats 
   flow_X = []
   flow_Y = []
   press_X = []
   press_Y = []
   volume_X = []
   volume_Y = []
  
   volume_sum = 0.0

   
   plotfile_name=os.path.splitext(flow_file)[0]+'all'+str(breath_cycle)+'.png'

   # loop thru data, detect breath, seperate and process
   i = 0
   while i < length :
      flow_value = float(data[i][0])
      press_value = float(press_data[i][0])
      if airway == True :
         airway_press_value = float(airway_press_data[i][0])
       
      # if look for zero crossing for breadth detection
      if flow_value < -2.0 and positive_trend == True :
           positive_trend = False
           end_of_inhalation = True
           volume_sum = flow_value         # reset voume sum
      elif flow_value >= 5.0 and positive_trend == False :
         # when flow is positive we detect start of breath - plot all our data
         plot_all(test_num, 
            pressure_type,
            flow_X,flow_Y,
            press_X,press_Y,
            volume_X,volume_Y,
            breath_cycle,
            plotfile_name)

         # write out statistcs - just doing volume for now
         # check if we hqve full breath
         #print(breath_time, breath_cycle)
         if breath_time > 1000 and breath_cycle > 0 :
            valid_breath = valid_breath + 1
            #print(breath_time, breath_cycle, valid_breath)
            if verbose == True :
               print(volume_Y[np.argmax(volume_Y)])
            total_vt = total_vt + volume_Y[np.argmax(volume_Y)]
            insp_time = insp_time + volume_X[np.argmax(volume_Y)]
            #print(insp_time)
            ie_time = ie_time + breath_time
            if verbose == True :
               print(breath_time, valid_breath, volume_Y[np.argmax(volume_Y)])


            

         # reset everything and prepare for next
         positive_trend = True
         breath_time = 0.0      # start a new breath
         flow_X = []
         flow_Y = []
         press_X = []
         press_Y = []
         volume_X = []
         volume_Y = []
         volume_sum = flow_value         # reset voume sum
         
         if first_breath_started == True :         # special case the first time
            breath_cycle = breath_cycle + 1
            plotfile_name=os.path.splitext(flow_file)[0]+'all'+str(breath_cycle)+'.png'
      else :
            volume_sum = volume_sum + flow_value

      #end detecting breadth         
      
      #  Add X and Y values
      flow_X.append(breath_time/1000.0)
      flow_Y.append(flow_value)
      press_X.append(breath_time/1000.0)
      press_Y.append(press_value)
      if test_num < 11 and breath_time <= 1000.0 :             # cut off volume at 1
         volume_X.append(breath_time/1000.0)
         volume_Y.append(volume_sum/60.0)
      elif breath_time <= 700 :
         volume_X.append(breath_time/1000.0)
         volume_Y.append(volume_sum/60.0)


      #for tab in range (0, breath_cycle) :
      #    print(", ,", end = " ")
      if verbose == True :
         print(breath_time/1000, ",",flow_value)
      first_breath_started = True
      i = i +1
      breath_time = breath_time + 1
   # plot_out the last breath
   plot_all(test_num, 
      pressure_type,
      flow_X,flow_Y,
      press_X,press_Y,
      volume_X,volume_Y,
      breath_cycle,
      plotfile_name)

   # Write out statistcs'
   #print("valid_breath ", valid_breath)
   if valid_breath > 0 :
      expected_bpm = iso_table_data[test_num-1] [4]
      average_ie_time = (ie_time/float(valid_breath))/1000
      average_bpm = 60/average_ie_time
      error_bpm = 100 * (average_bpm-expected_bpm)/expected_bpm

      if test_num == 11 :
         expected_insp_time = 60.0/(2* iso_table_data[test_num-1] [4])
      else :
            expected_insp_time = 1.0
      average_insp_time = (insp_time/float(valid_breath))
      error_insp_time = 100 * (average_insp_time-expected_insp_time)/expected_insp_time

      expected_vt = iso_table_data[test_num-1] [3]
      average_vt = total_vt/float(valid_breath)
      error_vt = 100.0 * ((average_vt - expected_vt)/expected_vt)
      
      expected_peep = iso_table_data[test_num-1] [5]
      average_peep = recorded_peep/float(valid_breath)
      error_peep = 100.0 * ((average_peep - expected_peep)/expected_peep)
      
      #f.write("file","Test #","Expected vt","Average Vt","% Error","Expected PEEP","Average PEEP","% Error\n")  
      f = open(os.path.splitext(flow_file)[0]+'.stats', "w+")
      #f.write(flow_file,test_num,expected_vt,average_vt,expected_peep,average_peep,error_peep)  # python will convert \n to os.linesep
      print("{0:<14},{1:>5},{2:>8.2f},{3:>8.2f},{4:>8.2f},{5:>8.2f},{6:>8.2f},{7:>8.2f},{8:>8.2f},{9:>8.2f},{10:>8.2f},{11:>8.2f},{12:>8.2f},{13:>8.2f}".format(flow_file,test_num,expected_bpm,average_bpm,error_bpm,expected_insp_time,average_insp_time,error_insp_time,expected_vt,average_vt,error_vt,expected_peep,average_peep,error_peep)) # python will convert \n to os.linesep

      
      f.write("\n")
      f.close()

def print_stats(flow_file,test_num) :
   global insp_time_pb
   global total_vt_pb
   global recorded_peep_pb
   global ie_time_pb

   print(total_vt_pb)
   print(insp_time_pb)
   print(ie_time_pb)
   print(recorded_peep_pb)

   # lets adhust data to leanth

   total_vt_pb = total_vt_pb[0:(breath_num-1)]
   insp_time_pb = insp_time_pb[0:(breath_num-1)]
   ie_time_pb = ie_time_pb[0:(breath_num-1)]
   recorded_peep_pb =  recorded_peep_pb[0:(breath_num-1)]

   print(total_vt_pb)
   print(insp_time_pb)
   print(ie_time_pb)
   print(recorded_peep_pb)

   mean_vt = np.mean(total_vt_pb)
   mean_insp_time = np.mean(insp_time_pb)/1000.0
   mean_ie_time = np.mean(ie_time_pb)/1000.0
   mean_peep = np.mean(recorded_peep_pb)
   mean_e_time = mean_ie_time - mean_insp_time

   # calculate min
   min_vt = np.min(total_vt_pb)
   min_insp_time = np.min(insp_time_pb)/1000.0
   min_ie_time = np.min(ie_time_pb)/1000.0
   min_peep = np.min(recorded_peep_pb)

   min_e_time = 99
   for i in range(0,breath_num-1) :
      x = (ie_time_pb[i] - insp_time_pb[i])/1000.0
      if x < min_e_time :
         min_e_time = x

   # calculate max

   max_vt = np.max(total_vt_pb)
   max_insp_time = np.max(insp_time_pb)/1000.0
   max_ie_time = np.max(ie_time_pb)/1000.0
   max_peep = np.max(recorded_peep_pb)

   max_e_time = 0
   for i in range(0,breath_num-1) :
      x = (ie_time_pb[i] - insp_time_pb[i])/1000.0
      if x >  max_e_time:
         max_e_time = x


   expected_bpm = iso_table_data[test_num-1] [4]
   mean_bpm = 60/mean_ie_time
   error_bpm = 100 * (mean_bpm-expected_bpm)/expected_bpm

   

   if test_num == 11 :
         expected_insp_time = 60.0/(2* iso_table_data[test_num-1] [4])
   else :
      expected_insp_time = 1.0
   
   error_insp_time = 100 * (mean_insp_time-expected_insp_time)/expected_insp_time

   expected_vt = iso_table_data[test_num-1] [3]
   error_vt = 100.0 * ((mean_vt-expected_vt)/expected_vt)

   expected_peep = iso_table_data[test_num-1] [5]
   error_peep = 100.0 * ((mean_peep - expected_peep)/expected_peep)

   expected_e_time = iso_table_data[test_num-1] [7]
   error_e_time = 100 * (mean_e_time-expected_e_time)/expected_e_time

   # now calculate the errors in min and max

   
   min_bpm = 60/max_ie_time      # this is max on purpose
   min_error_bpm = 100 * (min_bpm-expected_bpm)/expected_bpm

   
   min_error_insp_time = 100 * (min_insp_time-expected_insp_time)/expected_insp_time

   
   min_error_vt = 100.0 * ((min_vt-expected_vt)/expected_vt)

   min_error_peep = 100.0 * ((min_peep - expected_peep)/expected_peep)

   min_error_e_time = 100 * (min_e_time-expected_e_time)/expected_e_time

   # calculate errors in max

   max_bpm = 60/min_ie_time      # this is max on purpose
   max_error_bpm = 100 * (min_bpm-expected_bpm)/expected_bpm

   
   max_error_insp_time = 100 * (max_insp_time-expected_insp_time)/expected_insp_time

   
   max_error_vt = 100.0 * ((max_vt-expected_vt)/expected_vt)

   max_error_peep = 100.0 * ((max_peep - expected_peep)/expected_peep)

   max_error_e_time = 100 * (max_e_time-expected_e_time)/expected_e_time

   # add to table
   m_vt_s = "{:.2f}".format(mean_vt)
   m_bpm_s = "{:.2f}".format(mean_bpm)
   m_peep_s = "{:.2f}".format(mean_peep)
   m_insp_s = "{:.2f}".format(mean_insp_time)
   m_e_s = "{:.2f}".format(mean_e_time)

   e_vt_s = "{:.2f}".format(error_vt)
   e_bpm_s = "{:.2f}".format(error_bpm)
   e_peep_s = "{:.2f}".format(error_peep)
   e_insp_s = "{:.2f}".format(error_insp_time)
   e_e_s = "{:.2f}".format(error_e_time)

   #iso_table_label =['Test','Comp', 'Rp', 'Vt',   'Freq',  'PEEP',   'I',       'E']
   stats_table.append(['Mean',     '',    '',   m_vt_s, m_bpm_s, m_peep_s, m_insp_s, m_e_s])
   stats_table.append(['% Error',     '',    '',   e_vt_s, e_bpm_s, e_peep_s, e_insp_s, e_e_s])

   # add to table min values
   min_vt_s = "{:.2f}".format(min_vt)
   min_bpm_s = "{:.2f}".format(min_bpm)
   min_peep_s = "{:.2f}".format(min_peep)
   min_insp_s = "{:.2f}".format(min_insp_time)
   min_e_s = "{:.2f}".format(min_e_time)

   min_e_vt_s = "{:.2f}".format(min_error_vt)
   min_e_bpm_s = "{:.2f}".format(min_error_bpm)
   min_e_peep_s = "{:.2f}".format(min_error_peep)
   min_e_insp_s = "{:.2f}".format(min_error_insp_time)
   min_e_e_s = "{:.2f}".format(min_error_e_time)

   #iso_table_label =['Test','Comp', 'Rp', 'Vt',   'Freq',  'PEEP',   'I',       'E']
   stats_table.append(['Min',     '',    '',   min_vt_s, min_bpm_s, min_peep_s, min_insp_s, min_e_s])
   stats_table.append(['% Error',     '',    '',   min_e_vt_s, min_e_bpm_s, min_e_peep_s, min_e_insp_s, e_e_s])


   # add to table max values
   max_vt_s = "{:.2f}".format(max_vt)
   max_bpm_s = "{:.2f}".format(max_bpm)
   max_peep_s = "{:.2f}".format(max_peep)
   max_insp_s = "{:.2f}".format(max_insp_time)
   max_e_s = "{:.2f}".format(max_e_time)

   max_e_vt_s = "{:.2f}".format(max_error_vt)
   max_e_bpm_s = "{:.2f}".format(max_error_bpm)
   max_e_peep_s = "{:.2f}".format(max_error_peep)
   max_e_insp_s = "{:.2f}".format(max_error_insp_time)
   max_e_e_s = "{:.2f}".format(max_error_e_time)

   #iso_table_label =['Test','Comp', 'Rp', 'Vt',   'Freq',  'PEEP',   'I',       'E']
   stats_table.append(['Max',     '',    '',   max_vt_s, max_bpm_s, max_peep_s, max_insp_s, max_e_s])
   stats_table.append(['% Error',     '',    '',   max_e_vt_s, max_e_bpm_s, max_e_peep_s, max_e_insp_s, max_e_e_s])



   
   print("{0:<14},{1:>5},{2:>8.2f},{3:>8.2f},{4:>8.2f},{5:>8.2f},{6:>8.2f},{7:>8.2f},{8:>8.2f},{9:>8.2f},{10:>8.2f},{14:>8.2f},{15:>8.2f},{16:>8.2f}".format(
   flow_file,
   test_num,
   expected_bpm,
   mean_bpm,
   error_bpm,
   expected_insp_time,
   mean_insp_time,
   error_insp_time,
   expected_vt,
   mean_vt,
   error_vt,
   expected_peep,
   mean_peep,
   error_peep,
   expected_e_time,
   mean_e_time,
   error_e_time)) # python will convert \n to os.linesep

   # now lets make the graph table
   #graph_table_header = "['Breath #','Vt',      'PEEP', 'I', 'E', 'I+E']"

   #print(breath_num)
   #print(total_vt_pb)
   #print(insp_time_pb)
   #print(ie_time_pb)
   #print(recorded_peep_pb)


   for i in range(0,breath_num-1) :
      b_s = str(i+1)
      vt_s = "{:.2f}".format(total_vt_pb[i])
      peep_s = "{:.2f}".format(recorded_peep_pb[i])
      i_time_s = "{:.2f}".format(insp_time_pb[i]/1000)
      e_time_s = "{:.2f}".format((ie_time_pb[i]-insp_time_pb[i])/1000)
      ie_time_s = "{:.2f}".format(ie_time_pb[i]/1000)
      #graph_table_header = "['Breath #','Vt',      'PEEP', 'I', 'E', 'I+E']"
      graph_table.append([b_s,        vt_s,      peep_s, i_time_s, e_time_s, ie_time_s])

   print(graph_table)


   
# end



def plot_charts(test_num, flow_file, press_file , pressure_type) :
   

   global start
   global stop
   global insp_time_pb
   global total_vt_p
   global recorded_peep_pb
   global ie_time_pb
   global breath_num

   with open(flow_file) as f:
      reader = csv.reader(f)
      data = list(reader)
   # open pressure file
   with open(press_file) as p:
      press_reader = csv.reader(p)
      press_data = list(press_reader)
   
   
   length = len(data)
   breath_time = 0

   positive_trend = True

   
   # state 0, looking for 1st breath
   # state 1, inspiration
   # state 2, expiration phase
   looking = 0
   lookfor_positive = 1
   lookfor_partial_breath = 2 
   expiration = 3
   inspiration = 4
 

   state = looking


   # data and stats 
   flow_X = []
   flow_Y = []
   press_X = []
   press_Y = []
   volume_X = []
   volume_Y = []
  
   volume_sum = 0.0

 
   flow_value = 0
   volume_bias = 0
   last_valid_breath = 0
   breath_num = 0
   first_breath_started = False
   first_breath_time = 0
   max_volume = 0


   total_vt = 0.0
   valid_breath = 0 


   plotfile_name=os.path.splitext(flow_file)[0]+'all'+str(breath_cycle)+'.png'
   
   # loop thru data, detect breath, seperate and process
   volume_X.append(0)
   volume_Y.append(0)
   i = start
   if stop == 0 :
      stop = len(data)
   state = looking
   volume_sum_new =0
   last_valid_breath=i
   #print(i)
   while i < stop :
      k = i - start
      flow_value = float(data[i][0])
      press_value = float(press_data[i][0])

      #print(">>>>>> state:", state," i:", i," breath_time: ", breath_time,"flow_value",flow_value,volume_sum)   
     
      if state == looking :
            if flow_value < 0 : # look for transition to postive
                  state = lookfor_positive
      
      elif state == lookfor_positive :
         if flow_value > 0 :
            # initialize everything for inspiration here
            state = inspiration
            last_valid_breath = k
            breath_time = 0
            volume_sum = 0
            breath_num = 1

      elif state == inspiration :
         if flow_value < -2.0  :
            state = expiration
            insp_time_pb.append(k-last_valid_breath)
            max_volume = volume_sum/60
            total_vt_pb.append(volume_sum/60)
            if verbose == True :
                  print("inspiration time: ",k-last_valid_breath, "volume:", volume_sum/60.0)


      
      elif state == expiration :
         if flow_value >= 0 :
            state = inspiration
            
            volume_bias = volume_sum



            #handle sudden plot cut outs
            if (volume_bias/60.0>50):
               volume_bias=0

            
            if first_breath_started == False :
               first_breath_started = True
               first_breath_time = last_valid_breath
               if verbose == True :
                  print("first_breath_time",first_breath_time)

            
            if verbose == True :
               print("breath_num",breath_num,"breath_time :",k-last_valid_breath)
            ie_time_pb.append(k-last_valid_breath)

            #average_ie_time += k-last_valid_breath


            #plot volume retrospectively

            max_new_volume = 0
            j=last_valid_breath
            #volume_sum_new=0
            #print("len",len(volume_X), j)
            v_start = len(volume_X) 
            if (k>last_valid_breath) :
               while j<k:
                  flow_old=float(data[j+start][0])
                  volume_sum_new = volume_sum_new + flow_old - volume_bias/(k-last_valid_breath)
                  if volume_sum_new > max_new_volume :
                      max_new_volume = volume_sum_new
                  volume_X.append(j/1000.0)
                  volume_Y.append((volume_sum_new)/60.0)
                  j=j+1
               volume_sum=0
            
            #print("len 2",len(volume_X), j)
            max_new_volume = max_new_volume/60.0

            # now add the difference
            r = max_volume/max_new_volume
            #print("DIFF",r)
            for m in range(v_start,len(volume_X)) :
                  volume_Y[m] = volume_Y[m] * r


            # lets calculate the PEEP values
            recorded_peep_pb.append(calculate_PEEP(j,k,press_X,press_Y))


            last_valid_breath = k

            breath_time = 0
            breath_num += 1


            #print("**************************")

      if (state == inspiration or state == expiration):                  # ignore positive values in expiration phase
         volume_sum = volume_sum + flow_value
         
         #  Add X and Y values
         flow_X.append(k/1000.0)
         flow_Y.append(flow_value)
         press_X.append(k/1000.0)
         press_Y.append(press_value)
         breath_time = breath_time + 1
      else :
         volume_sum = 0
         flow_X.append(k/1000.0)
         flow_Y.append(flow_value)
         press_X.append(k/1000.0)
         press_Y.append(press_value)
         

      
      i = i + 1
      #print("<<<<<< state:", state," i:", i," breath_time: ", breath_time,"flow_value",flow_value, volume_sum)   
      
     


   #print("first_breath_time",first_breath_time)
   #print("last", last_valid_breath, "bias :",volume_bias)
   #print(len(flow_X))
   # flow_X = flow_X[0:last_valid_breath]
   # flow_Y = flow_Y[0:last_valid_breath]
   # press_X = press_X[0:last_valid_breath] 
   # press_Y = press_Y[0:last_valid_breath]
   # volume_X = volume_X[0:last_valid_breath]
   # volume_Y = volume_Y[0:last_valid_breath]

   if raw_graph  == False :

      flow_X = flow_X[first_breath_time:last_valid_breath]
      flow_Y = flow_Y[first_breath_time:last_valid_breath]
      press_X = press_X[first_breath_time:last_valid_breath] 
      press_Y = press_Y[first_breath_time:last_valid_breath]
      volume_X = volume_X[1:last_valid_breath]
      volume_Y = volume_Y[1:last_valid_breath]
   
      # rewrite X scale

      for i in range(0,len(flow_X)) :
            flow_X [i] = i / 1000.0
      for i in range(0,len(press_X)) :
            press_X [i]= i /1000.0
      for i in range(0,len(volume_X)) :
            volume_X [i] = i /1000.0


  

   # plot_out the last breath
   print (plotfile_name)
   print_stats(flow_file, test_num)
   plot_all(test_num, 
      pressure_type,
      flow_X,flow_Y,
      press_X,press_Y,
      volume_X,volume_Y,
      breath_cycle,
      plotfile_name)

  

#end func
   





def main(argv):
   global display
   global stats
   global verbose
   global split
   global annotate
   global start
   global stop
   global raw_graph

   pressure_file = ''
   flow_file= ''
   airway_pressure_file = ''
   test_num = 0                   #there are only 10 tests
   try:
      opts, args = getopt.getopt(argv,"ht:f:p:aledsvnr",
         ["help",
         "test=",
         "flow=",
         "pressure=","airway_pressure","lung_pressure","peep_pressure",
         "display","stats","verbose","nosplit","begin=","stop=","zero"
         ])
   except getopt.GetoptError:
      print('PlotAll.py -t <test number 1 through 11> -f <flowfile> -p <pressure file>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print(' 1PlotAll.py -t <test number 1 through 11> -f <flowfile> -p <pressure file>')
         sys.exit()
      elif opt == '-t':
         test_num = int(arg)
         if test_num < 1 or test_num > 11 :
            print(' 2  PlotAll.py -t <test number 1 through 11> -f <flowfile> -p <pressure file>')
            sys.exit(2)
      elif opt in ("-f", "--flow"):
         flow_file = arg
      elif opt in ("-p", "--pressure"):
         pressure_file= arg
      elif opt in ("-d", "--display"):
         display = True
      elif opt in ("-s", "--stats"):
         stats = True
      elif opt in ("-a", "--airway_pressure"):
         pressure_type = "airway"
      elif opt in ("-l", "--lung_pressure"):
         pressure_type = "lung"
      elif opt in ("-e", "--peep_pressure"):
         pressure_type = "peep"
      elif opt in ("-n", "--nosplit"):
         split = False
         annotate = False
      elif opt in ("--begin") :
         start = int(arg)
      elif opt in ("--stop") :
         stop = int(arg)
      elif opt in ("-z","zero") :
         zero  = True
      elif opt in ("-v") :
         verbose  = True
      elif opt in ("-r") :
         raw_graph  = True




   # validate need flow file and atleast one pressure file
   if flow_file == '' or  pressure_file == '' :
      print ("test number is", test_num)      
      print ("Flow  file is ", flow_file)
      print ("Lung Pressure file is", pressure_file)
      print ("Display plots", display)
      print(' 3 PlotAll.py -t <test number 1 through 11> -f <flowfile> -p <pressure file>')
      sys.exit(2)
   
   if verbose == True :   
      print ("test number is", test_num)      
      print ("Flow  file is ", flow_file)
      print ("Lung Pressure file is", pressure_file)
      print ("Airway Pressure file is", airway_pressure_file)
      print ("Display plots", display)
   
   if split == True :
      plot_charts_per_breath(test_num, flow_file, pressure_file, pressure_type)
   else :
      plot_charts(test_num, flow_file, pressure_file, pressure_type)


if __name__ == "__main__":
   main(sys.argv[1:])


