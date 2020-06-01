import pandas as ps 
import numpy as np
import matplotlib.pylab as plt
import matplotlib.gridspec as gridspec
import sys, getopt
import csv
import sys
import os

# make our test table
iso_table_label = ['Test','Comp',      'Rp', 'Vt', 'Freq', 'PEEP', 'I:E']
iso_table_UNITS = ['    ', 'L/CM*H2O', '  ', 'mL', 'BPM', 'cmH20','1:0' ]
iso_table_data =  [ [ 1,      50,       5,    500,   20,      5,    2], 
                     [ 2,     50,      20,    500,   15,     10,    2], 
                     [ 3,     20,      5,     500,   20,      5,    2], 
                     [ 4,     20,      20,    500,   20,     10,    2],
                     [ 5,     20,      20,    300,   20,      5,    2],
                     [ 6,     20,      50,    300,   15,     10,    3],
                     [ 7,     10,      50,    300,   20,     10,    2],
                     [ 8,     10,      20,    200,   20,      5,    2],
                     [ 9,     10,      20,    200,   24,      5,    1.5],
                     [10,     10,      20,    200,   30,      5,    1],
] 
vent_measured =      [ 'UI',    '',      '',    '',    '',      '',   '']
instrument_measured = [ 'Measured',    '',      '',    '',    '',      '',   '']
per_error =  ['% Error',    '',      '',    '',    '',      '',   '']

display = False
stats = True
plots = True

def plot_volume(X,Y, index, ax) :
   plt.xlabel('time(sec)')
   plt.ylabel('Volume(ml)')
   plt.title('Tidal Volume Per Inspiration '+str(index))
   plt.grid(True)
   plt.plot(X,Y)
   # Annotate max
   xmax = X[np.argmax(Y)]
   ymax = Y[np.argmax(Y)]
   text= "t={:.2f}, Vt={:.2f}".format(xmax, ymax)
   ax=plt.gca()
   bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
   arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
   kw = dict(xycoords='data',textcoords="axes fraction",
            arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
   ax.annotate(text, xy=(xmax, ymax), xytext=(0.55,0.96), **kw)
   plt.plot(X,Y)
#end plot_volume

def plot_pressure(X, Y, index, ax) :
   plt.xlabel('time(sec)')
   plt.ylabel('Pressure (cmH20)')
   plt.title('Pressure Per Breath @ lung '+str(index))
   plt.grid(True)
   plt.plot(X,Y)
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
   plt.plot(X, Y)
#end plot pressure

def plot_flow(X, Y, index, ax) :
   plt.xlabel('time(sec)')
   plt.ylabel('Flow (SLM)')
   plt.title('Flow Per Breath '+str(index))
   plt.grid(True)
   # Annotate max
   xmax = X[np.argmax(Y)]
   print("#########", xmax)
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

def draw_table(ax, testnum) :
   table_data = []
   table_data.append(iso_table_label)
   table_data.append(iso_table_UNITS)
   table_data.append(iso_table_data[testnum-1])
   #table_data.append(vent_measured)
   #table_data.append(instrument_measured)
   #table_data.append(per_error)

   df = ps.DataFrame(data=table_data)
   df = df.T                              # transponse table rows and columns
   table_data = df.values.tolist()


   table = ax.table(cellText=table_data, loc='center')
   table.auto_set_font_size(False)
   table.set_fontsize(9)
   table.auto_set_column_width(col=list(range(len(df.columns))))
   table.scale(2, 2)  # may help
   ax.axis('off')
# end draw_table

def plot_all(testnum,flow_X,flow_Y,press_X,press_Y,volume_X,volume_Y,breath_cycle,plot_file) :
   #Create 2x2 sub plots
   gs = gridspec.GridSpec(2, 2)

   plt.figure(figsize=(8,8))
   plt.subplots_adjust(wspace=0.4, hspace=0.5)

   ax = plt.subplot(gs[0, 0]) # row 0, col 1
   draw_table(ax,testnum)

   ax = plt.subplot(gs[0, 1]) # row 0, col 1
   plot_flow(flow_X,flow_Y,breath_cycle,ax)
   
   ax = plt.subplot(gs[1, 0]) # row 1, col 0
   plot_pressure(press_X, press_Y, breath_cycle,ax)
   
   ax = plt.subplot(gs[1, 1]) # row 1, col 0
   plot_volume(volume_X,volume_Y,breath_cycle,ax)
   
   plt.savefig(plot_file)
   print("show plots",display)
   #input()
   if display == True :
      #input()
      plt.show()
# end ploy_chats




def plot_charts(test_num, flow_file, press_file) :

   # open flow file
   with open(flow_file) as f:
      reader = csv.reader(f)
      data = list(reader)
   # open pressure file
   with open(press_file) as p:
      press_reader = csv.reader(p)
      press_data = list(press_reader)
   
   length = len(data)

   flow_X = []
   flow_Y = []
   press_X = []
   press_Y = []
   volume_X = []
   volume_Y = []
   positive_trend = True
   breath_time = 0.0
   breath_cycle = 0
   volume_sum = 0
   valid_breath =0
   total_vt = 0
   
   first_breath_started = False
 

   end_of_inhalation = False

   plotfile_name=os.path.splitext(flow_file)[0]+'all'+str(breath_cycle)+'.png'

   print(plotfile_name)

   i = 0
   while i < length :
      flow_value = float(data[i][0])
      press_value = float(press_data[i][0])
       
      # if look for zero crossing for breadth detection
      if flow_value < -2.0 and positive_trend == True :
           positive_trend = False
           end_of_inhalation = True
           volume_sum = flow_value         # reset voume sum
      elif flow_value >= 0 and positive_trend == False :
         # when flow is positive we detect start of breath - plot all our data
         plot_all(test_num,flow_X,flow_Y,press_X,press_Y,volume_X,volume_Y,breath_cycle,plotfile_name)

         # write out statistcs - just doing volume for now
         # check if we hqve full breath
         if breath_time > 2000.0 and breath_cycle > 1 :
            valid_breath = valid_breath + 1
            print(volume_Y[np.argmax(volume_Y)])
            total_vt = total_vt + volume_Y[np.argmax(volume_Y)]
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
      if breath_time <= 1000.0 :             # cut off volume at 1
        volume_X.append(breath_time/1000.0)
        volume_Y.append(volume_sum/60.0)

      #for tab in range (0, breath_cycle) :
      #    print(", ,", end = " ")
      print(breath_time/1000, ",",flow_value)
      first_breath_started = True
      i = i +1
      breath_time = breath_time + 1
   # plot_out the last breath
   plot_all(test_num,flow_X,flow_Y,press_X,press_Y,volume_X,volume_Y,breath_cycle, plotfile_name)

   # Write out statistcs
   f = open(os.path.splitext(flow_file)[0]+'.stats', "w+")
   print("****",valid_breath, total_vt, total_vt/float(valid_breath))
   f.write("Average Vt"+str(total_vt/float(valid_breath)))  # python will convert \n to os.linesep
   f.close()



def main(argv):
   global display
   pressure_file = ''
   flow_file= ''
   test_num = 99                    #there are only 10 tests
   try:
      opts, args = getopt.getopt(argv,"ht:f:p:ds",["test=","flow=","pressure=","display","stats"])
   except getopt.GetoptError:
      print('PlotAll.py -t <test number 1 through 10> -f <flowfile> -p <pressure file>')
      sys.exit(2)
   for opt, arg in opts:
      if opt == '-h':
         print('PlotAll.py -t <test number 1 through 10> -f <flowfile> -p <pressure file>')
         sys.exit()
      elif opt == '-t':
         test_num = int(arg)
      elif opt in ("-f", "--flow"):
         flow_file = arg
      elif opt in ("-p", "--pressure"):
         pressure_file= arg
      elif opt in ("-d", "--display"):
         display = True
      elif opt in ("-s", "--stats"):
         stats = True


   # validate
   if test_num < 1 or test_num > 10  or flow_file == '' or pressure_file == '' :
      print('PlotAll.py -t <test number 1 through 10> -f <flowfile> -p <pressure file>')
      sys.exit(2)
      
   print ("test number is", test_num)      
   print ("Flow  file is ", flow_file)
   print ("Pressure file is", pressure_file)
   print ("Display plots", display)
   plot_charts(test_num,flow_file,pressure_file)


if __name__ == "__main__":
   main(sys.argv[1:])


