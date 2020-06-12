
 
import pandas as ps 
import numpy as np
import matplotlib.pylab as plt
import matplotlib.gridspec as gridspec
import sys, getopt
import csv
import sys
import os


# make our test 2
iso_table_label = ['Test','Comp',      'Rp', 'Vt', 'Freq', 'PEEP', 'I:E']
iso_table_UNITS = ['    ', 'L/CM*H2O', '  ', 'mL', 'BPM', 'cmH20','1:0' ]
iso_table_data =  [ [ 1,      50,       5,    500,   20,      5,    2], 
                     [ 2,     50,      20,    500,   15,     10,    3], 
                     [ 3,     20,      5,     500,   20,      5,    2], 
                     [ 4,     20,      20,    500,   20,     10,    2],
                     [ 5,     20,      20,    300,   20,      5,    2],
                     [ 6,     20,      50,    300,   15,     10,    3],
                     [ 7,     10,      50,    300,   20,     10,    2],
                     [ 8,     10,      20,    200,   20,      5,    2],
                     [ 9,     10,      20,    200,   24,      5,    1.5],
                     [10,     10,      20,    200,   30,      5,    1],
                     [ "24hrs",    50,      5,     600,   35,      10,    1]    # endurance test
                  ]


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
breath_time = 0.0
split = True
annotate = True
start = 0
stop = 0

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
            for k in range(len(Y)-50,len(Y)) :
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
   table_data = []
   table_data.append(iso_table_label)
   table_data.append(iso_table_UNITS)
   table_data.append(iso_table_data[testnum-1])
  

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
         table.scale(5, 2)        
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
         
         plt.figure(figsize=(8,9))
         plt.subplots_adjust(wspace=0.4, hspace=0.46, bottom = 0.06, top = 1.0)
         # create 2x2 grid
         gs = gridspec.GridSpec(4, 1)
         
         ax = plt.subplot(gs[0, 0]) # row 0, col 1
         draw_table(ax,testnum, False)     ## transpose the 
      
         ax = plt.subplot(gs[1, 0]) # row 0, col 1
         plot_flow(flow_X,flow_Y,breath_cycle,ax)
         
         ax = plt.subplot(gs[2, 0]) # row 1, col 0
         plot_pressure(pressure_type, press_X, press_Y, breath_cycle,ax)
         
         ax = plt.subplot(gs[3, 0]) # row 1, col 0
         plot_volume(volume_X,volume_Y,breath_cycle,ax)
      
   plt.savefig(plot_file)

   if display == True :
      #input()
      plt.show()
# end ploy_chats




def plot_charts_per_breath(test_num, flow_file, press_file , pressure_type) :
   global breath_cycle
   global breath_time
   global insp_time
   global ie_time
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
   total_vt = 0.0
   
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
      elif flow_value >= 0 and positive_trend == False :
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

def plot_charts(test_num, flow_file, press_file , pressure_type) :
   

   global start
   global stop

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
   number_of_positives = 0
   last_valid_breath = 0
   breath_num = 0


 


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
   print(i)
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
      
      elif state == expiration :
         if flow_value >= 0 :
            state = inspiration
            breath_time = 0
            breath_num += 1
            volume_bias = volume_sum

            #handle sudden plot cut outs
            if (volume_bias/60.0>50):
               volume_bias=0

            #plot volume retrospectively
            j=last_valid_breath
            #volume_sum_new=0
            if (k>last_valid_breath) :
               while j<k:
                  flow_old=float(data[j+start][0])
                  volume_sum_new = volume_sum_new + flow_old - volume_bias/(k-last_valid_breath)
                  volume_X.append(j/1000.0)
                  volume_Y.append((volume_sum_new)/60.0)
                  j=j+1
               volume_sum=0
            last_valid_breath = k
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
      
     
   #Lets truncate to last breath
   last_valid_breath = last_valid_breath-500

   #print("last", last_valid_breath, "bias :",volume_bias)
   #print(len(flow_X))
   flow_X = flow_X[0:last_valid_breath]
   flow_Y = flow_Y[0:last_valid_breath]
   press_X = press_X[0:last_valid_breath] 
   press_Y = press_Y[0:last_valid_breath]
   volume_X = volume_X[0:last_valid_breath]
   volume_Y = volume_Y[0:last_valid_breath]

   # plot_out the last breath
   print (plotfile_name)
   plot_all(test_num, 
      pressure_type,
      flow_X,flow_Y,
      press_X,press_Y,
      volume_X,volume_Y,
      breath_cycle,
      plotfile_name)

   





def main(argv):
   global display
   global stats
   global verbose
   global split
   global annotate
   global start
   global stop

   pressure_file = ''
   flow_file= ''
   airway_pressure_file = ''
   test_num = 0                   #there are only 10 tests
   try:
      opts, args = getopt.getopt(argv,"ht:f:p:aledsvn",
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


